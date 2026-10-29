"""PharmaIntel CLI entry point.

Usage:
    python -m pharmaintel <drug-name> [--out report.md] [--html report.html]

Prints the Markdown report to stdout unless --out is given (in which
case the report is written to that file and a one-line summary is
printed). --html writes an HTML version alongside.

Exit code is 0 whenever a report was produced, even if one source
failed — a failed source is reported inside the report, not as a crash.
Exit code 2 means bad usage (no drug name).
"""

import argparse
import sys

from . import __version__, report as report_mod
from . import sources


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pharmaintel",
        description="One unified drug-intelligence report from public APIs. "
                    "Research tool only — not medical advice.")
    parser.add_argument("drug", help="drug name, generic preferred "
                                     "(e.g. metformin, atorvastatin)")
    parser.add_argument("--out", metavar="FILE",
                        help="write the Markdown report to FILE")
    parser.add_argument("--html", metavar="FILE",
                        help="also write an HTML version to FILE")
    parser.add_argument("--version", action="version",
                        version="PharmaIntel %s" % __version__)
    args = parser.parse_args(argv)
    if not args.drug.strip():
        parser.error("drug name must not be empty")

    drug = args.drug.strip()
    label = sources.fetch_label(drug)
    faers = sources.fetch_faers(drug)
    interactions = sources.fetch_interactions(
        drug, label_sections=label.get("sections") if label["ok"] else None)
    rep = report_mod.build(drug, label, faers, interactions)
    markdown = report_mod.to_markdown(rep)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print("PharmaIntel report for '%s' written to %s" % (drug, args.out))
    else:
        sys.stdout.write(markdown)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(report_mod.to_html(rep))
        print("HTML version written to %s" % args.html)

    populated = [
        name for name, ok in (
            ("label", label["ok"]),
            ("interactions",
             bool(interactions["rxnav_pairs"] or interactions["label_text"])),
            ("faers", faers["ok"]))
        if ok
    ]
    print("Sections populated: %s"
          % (", ".join(populated) if populated else "none"), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
