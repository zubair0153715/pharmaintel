# PharmaIntel — piece map (draft, 2026-10-29)

Prepared from verified local code, not from memory. PharmaIntel was the
#1 recommendation in chat on 2026-10-29 (drug-intelligence CLI: one report
per drug). This map is the offered first move; no repo skeleton has been
built yet and nothing has been published.

## Already built — reusable as-is (call, don't copy-paste blindly)

1. **FDA label + FAERS side-effect signals**
   - `~/workspace/clinic-demo/app/drugsafety/drugsafety.py` (178 lines)
   - openFDA `drug/label.json` (label) + `drug/event.json` (FAERS),
     with an INN→USAN map for label lookup (US labels use USAN names).
   - Live as /drugsafety. Caveat already on that page: FAERS ≠ proven
     causation.

2. **Renal / hepatic dosing, 119 curated drugs**
   - `~/workspace/clinic-demo/app/mediscribe/dose.py` (389 lines) +
     `~/workspace/clinic-demo/app/mediscribe/data/dose_rules.json`
     (`drugs`: 119 entries, version 24; methods: Cockcroft-Gault,
     CKD-EPI, Schwartz, Child-Pugh, IBW/AdjBW).
   - 11 NTI drugs force TDM warnings (per standing memory).

3. **Curated pairwise interaction / contraindication flags**
   - `~/workspace/clinic-demo/app/mediscribe/engine.py` — `safety_check()`
     uses a curated `_IX` pairwise table and `_CONTRAX` condition table.
   - Scope limit: this covers pairs inside the curated drug list only.
     It is NOT a general interaction lookup for arbitrary drug pairs.

4. **Research / similarity layer (LeadForge)**
   - `~/workspace/clinic-demo/app/discovery/sources.py` — UniProtKB
     target search, ChEMBL targets / bioactivities / molecule, PubChem
     by name / SMILES / similarity, all with a local cache helper.
   - `chem.py` (RDKit similarity), `tox.py` (Lipinski/Veber, PAINS,
     ToxGuard) in the same directory.

## Gap for the promised first command

First command as offered: `drug name → label + interactions + FAERS summary`.

- Label: covered (item 1). FAERS: covered (item 1).
- Renal dose: covered for the 119 (item 2); other drugs fall back to
  live FDA label + "not yet curated" banner, as MediScribe already does.
- Interactions: PARTIAL. Curated pairs work; an arbitrary pair needs a
  new public source (candidates to verify before building: RxNav
  interaction API, or the interaction section of the DailyMed label).
  Do not claim full interaction coverage until that source is verified.

## Suggested skeleton (not built — needs his word)

- `pharmaintel/` repo, one command `pharmaintel <drug>` → single
  report: label summary, FAERS top signals with counts + "not
  causation" note, renal/hepatic dose if curated else label fallback,
  curated interaction flags, ChEMBL/PubChem identifiers.
- Standing lines that carry over: research tool only, never medical
  advice; no copying of proprietary code/data — public APIs + own glue
  only; no card, no paid API.

## What this map does NOT claim

- DailyMed is not yet wired (openFDA label is the current label source).
- No interaction coverage beyond the curated list has been verified.
- Nothing here has been sent, published, or shown to anyone else.
