"""Minimal HTTP client: Python stdlib urllib only (no third-party deps).

Why urllib and not httpx/requests: on this VM, plain httpx calls through
the stock proxy have failed before, while urllib-based calls to the same
public APIs have worked. urllib also honours the environment proxy
settings by default, so no special proxy handling is needed here.

Every fetch returns (data, error): data is parsed JSON or None, error is
a short human-readable string or None. Callers never raise on a failed
source — they report "source unavailable" instead.
"""

import json
import urllib.error
import urllib.request

USER_AGENT = "PharmaIntel-research/1.0"


def get_json(url, timeout=30):
    """GET a URL, return (parsed_json_or_None, error_or_None)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        return None, "HTTP %s" % exc.code
    except urllib.error.URLError as exc:
        return None, "network error: %s" % (exc.reason,)
    except (TimeoutError, ValueError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    except Exception as exc:  # never let one source kill the whole report
        return None, "%s: %s" % (type(exc).__name__, exc)
