# PharmaIntel v1 — drug-intelligence CLI

**Research tool only — not medical advice.**

One command, one unified report per drug. PharmaIntel is original glue
code in the REA style: it calls fragmented public tools and merges
their outputs into a single report. It copies no proprietary code or
data, stores no patient data, and needs no API key.

## Install

Python 3.10+ only, **standard library only** — no packages to install:

```bash
cd ~/workspace/pharmaintel
python3 -m pharmaintel metformin
```

## Usage

```bash
# Print the Markdown report to stdout
python3 -m pharmaintel metformin

# Write Markdown + HTML files
python3 -m pharmaintel atorvastatin --out atorvastatin.md --html atorvastatin.html
```

Use the generic name when you know it (`paracetamol` is mapped to the
US label name `acetaminophen` automatically). Brand names work for the
FAERS section but the label lookup prefers generics.

## What a report contains

1. **FDA label summary** — indications, dosage and administration,
   boxed warning, contraindications, warnings, adverse reactions.
   Source: openFDA `drug/label.json` (official FDA label text).
2. **Known drug interactions** — two sub-sources, each cited:
   - NLM RxNav interaction API (pairwise list via RxNorm RxCUI);
   - the Drug Interactions section of the FDA label itself.
3. **FAERS adverse-event summary** — most-reported reactions with
   counts, total and serious report counts.
   Source: openFDA `drug/event.json` (FDA Adverse Event Reporting
   System).

Every section cites its source. If a source is unreachable, that section
says **"source unavailable"** with the real error — label text,
interactions, and side-effect numbers are never invented.

## Honest limits (read before trusting a report)

- **FAERS ≠ causation.** FAERS reports are voluntary and unverified:
  a report means someone reported an event while taking the drug, not
  that the drug caused it. Serious events are over-reported, and counts
  cover every product naming the drug, including combinations.
- **Label matching is approximate.** openFDA generic-name search can
  return a combination product first; PharmaIntel prefers a
  single-ingredient label with the exact generic name, otherwise it
  uses the first result and shows the generic/brand names it used, so
  you can spot a mismatch.
- **Interactions are partial.** The RxNav interaction endpoints
  returned HTTP 404 from this VM on 2026-10-29 (the API may be
  retired); until that is resolved, the interaction section rests on
  the FDA label's Drug Interactions text, which is official but not a
  pairwise database. The report states this plainly.
- **Not a dosing tool.** This v1 does not include the user's separate
  renal/hepatic dose module (119 curated drugs in MediScribe) — that
  is a planned v1.1 addition, not silently bundled here.
- **US-centric.** FDA labels and FAERS are US data; Pakistani brands
  are not covered (the FAERS section notes when a name is unmatched).

## Tests

```bash
python3 tests/test_end_to_end.py
```

Runs the CLI end-to-end on metformin (a real drug, live APIs) and
verifies the report contains all three sections plus the disclaimer,
then prints which sections actually populated with live data. The test
fails only if a section heading or the disclaimer is missing entirely —
a source being down is reported, not hidden.

## Project layout

```
pharmaintel/
  __init__.py   version
  __main__.py   CLI (argparse, exit codes)
  client.py     stdlib urllib GET helper (urllib, not httpx: httpx
                through this VM's proxy has failed before)
  sources.py    openFDA label, openFDA FAERS, RxNav interactions
  report.py     Markdown + HTML renderers, disclaimer, truncation
tests/
  test_end_to_end.py
```

## Prior work this builds on (user's own code, called in spirit)

- `~/workspace/clinic-demo/app/drugsafety/drugsafety.py` — openFDA
  label + FAERS patterns (INN→USAN map, FAERS count queries).
- `~/workspace/clinic-demo/app/mediscribe/` — dose module (119 drugs)
  and live-label fallback pattern; not imported by v1, noted for v1.1.
- `~/workspace/clinic-demo/app/discovery/` — LeadForge research layer
  (ChEMBL/PubChem); not imported by v1.
- `~/workspace/pharmaintel/PIECE-MAP.md` — the piece map this build
  followed, including the interaction-coverage gap it flagged.
