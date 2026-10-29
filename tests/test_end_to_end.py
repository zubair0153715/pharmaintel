"""End-to-end test: run the real CLI on a real drug (metformin).

Verifies the produced report contains all three sections plus the
disclaimer. Prints which sections actually populated with live data;
a source being down does NOT fail the test (the report must say
"source unavailable" instead) — only a missing section heading or a
missing disclaimer fails it. Run from ~/workspace/pharmaintel:

    python3 tests/test_end_to_end.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DRUG = os.environ.get("PHARMAINTEL_TEST_DRUG", "metformin")

REQUIRED_MARKERS = [
    "# PharmaIntel report: %s" % DRUG,
    "Research tool only — not medical advice.",
    "## 1. FDA label summary",
    "## 2. Known drug interactions",
    "## 3. FAERS adverse-event summary",
    "FAERS reports are voluntary and unverified",
]

POPULATION_MARKERS = {
    "label populated": "Generic name:",
    "interactions populated": "Source:** NLM RxNav interaction API",
    "label interaction text populated": "FDA label, Drug Interactions section",
    "faers populated": "Most frequently reported reactions",
}


def main():
    proc = subprocess.run(
        [sys.executable, "-m", "pharmaintel", DRUG],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    print("--- CLI stderr ---")
    print(proc.stderr.strip())
    if proc.returncode != 0:
        print("FAIL: CLI exited %s" % proc.returncode)
        print(proc.stdout[-2000:])
        return 1
    missing = [m for m in REQUIRED_MARKERS if m not in proc.stdout]
    if missing:
        print("FAIL: report is missing:")
        for m in missing:
            print("  - %r" % m)
        return 1
    print("--- section population (live data) ---")
    for name, marker in POPULATION_MARKERS.items():
        print("%s: %s" % (name, "yes" if marker in proc.stdout else "no"))
    if "source unavailable" in proc.stdout.lower():
        print("NOTE: at least one section reported a source as unavailable "
              "(see report); no data was invented for it.")
    print("PASS: report for '%s' contains all three sections + disclaimer."
          % DRUG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
