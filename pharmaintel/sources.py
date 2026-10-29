"""Public-source fetchers for PharmaIntel v1.

Sources (all free, no API key required):
- FDA label ......... openFDA drug/label.json (official FDA label text)
- FAERS events ...... openFDA drug/event.json (voluntary reports)
- Interactions ...... (a) NLM RxNav interaction API (RxCUI lookup, then
                          interaction list) and (b) the Drug Interactions
                          section of the FDA label itself.
                      On 2026-10-29 the RxNav interaction endpoints
                      returned HTTP 404 from this VM, so (b) is the
                      working interaction source and (a) is reported
                      honestly as unavailable. Nothing is invented to
                      fill the gap.

No source is ever faked: a failed fetch yields an "unavailable" note
with the real error, and the report still renders.
"""

import urllib.parse

from .client import get_json

OPENFDA = "https://api.fda.gov/drug"
RXNAV = "https://rxnav.nlm.nih.gov/REST"

# INN -> USAN: US FDA labels use USAN names (same small map pattern the
# user's MediScribe/Drug Safety code already uses).
INN_TO_USAN = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "adrenaline": "epinephrine",
    "glyceryl trinitrate": "nitroglycerin",
    "frusemide": "furosemide",
}

LABEL_SECTIONS = (
    "boxed_warning",
    "indications_and_usage",
    "dosage_and_administration",
    "contraindications",
    "warnings",
    "adverse_reactions",
    "drug_interactions",
)


def _join(value):
    if isinstance(value, list):
        return " ".join(str(v) for v in value).strip()
    return str(value or "").strip()


def _label_search_name(query):
    return INN_TO_USAN.get(query.strip().lower(), query.strip())


# Salt/counter-ion words stripped when comparing generic names, so
# "metformin" matches a label filed as "METFORMIN HYDROCHLORIDE" while
# "sitagliptin and metformin hydrochloride" (a combination) does not.
_SALT_WORDS = {
    "hydrochloride", "hcl", "dihydrochloride", "hydrobromide", "sulfate",
    "sulphate", "sodium", "potassium", "calcium", "magnesium", "mesylate",
    "maleate", "tartrate", "phosphate", "citrate", "bromide", "chloride",
    "acetate", "fumarate", "succinate", "besylate", "tosylate", "nitrate",
    "hydroxide", "oxide", "carbonate", "bitartrate", "edisylate",
}


def _base_name(name):
    words = "".join(ch if ch.isalnum() or ch.isspace() else " "
                    for ch in name.lower()).split()
    return " ".join(w for w in words if w not in _SALT_WORDS)


def _pick_label(results, query):
    """Prefer a single-ingredient label matching the query's base name.

    Scores: 3 = single generic exactly matching the base name,
    2 = single generic starting with the base name, 1 = a combination
    label containing the exact base name, 0 = anything else. First
    result wins ties (and when every score is 0).
    """
    wanted = _base_name(query)
    best, best_score = results[0], -1
    for result in results:
        generics = [g for g in
                    ((result.get("openfda") or {}).get("generic_name") or [])]
        bases = [_base_name(g) for g in generics]
        if len(bases) == 1 and bases[0] == wanted:
            score = 3
        elif len(bases) == 1 and bases[0].startswith(wanted + " "):
            score = 2
        elif wanted in bases:
            score = 1
        else:
            score = 0
        if score > best_score:
            best, best_score = result, score
            if score == 3:
                break
    return best


def fetch_label(query):
    """Fetch the best FDA label for a drug name.

    openFDA generic-name search matches combination products too, so we
    fetch up to 10 labels and prefer a single-ingredient label whose
    generic name equals the query; otherwise the first result wins.
    Returns a dict with ok, generic_name, brand_names, sections
    {section: text}, source, and error (when not ok).
    """
    name = _label_search_name(query)
    params = urllib.parse.urlencode(
        {"search": 'openfda.generic_name:"%s"' % name, "limit": 10})
    data, err = get_json("%s/label.json?%s" % (OPENFDA, params), timeout=60)
    if data is None:
        return {"ok": False, "error": "FDA label source unavailable (%s)." % err,
                "source": "openFDA drug/label.json"}
    results = data.get("results") or []
    if not results:
        return {"ok": False,
                "error": "No FDA label found for '%s'." % query,
                "source": "openFDA drug/label.json"}
    best = _pick_label(results, name)
    openfda = best.get("openfda") or {}
    sections = {}
    for key in LABEL_SECTIONS:
        text = _join(best.get(key))
        if text:
            sections[key] = text
    return {
        "ok": True,
        "query": query,
        "search_name": name,
        "generic_name": (openfda.get("generic_name") or [query])[0],
        "brand_names": (openfda.get("brand_name") or [])[:5],
        "manufacturer": (openfda.get("manufacturer_name") or [])[:3],
        "sections": sections,
        "source": "openFDA drug/label.json (official FDA label text)",
        "error": None,
    }


def fetch_faers(query):
    """FAERS adverse-event summary for a drug name via openFDA.

    Returns top reactions with counts, total and serious report counts.
    FAERS product-name matching is broad: counts cover every report
    naming this product, including combination products. The report
    carries the honest caveat that a FAERS report is NOT proof the
    drug caused the event.
    """
    med = 'patient.drug.medicinalproduct:"%s"' % query.strip()
    params = urllib.parse.urlencode(
        {"search": med, "count": "patient.reaction.reactionmeddrapt.exact",
         "limit": 10})
    data, err = get_json("%s/event.json?%s" % (OPENFDA, params), timeout=60)
    if data is None or "results" not in data:
        # Retry once title-cased: FAERS product names are case-sensitive-ish.
        alt = query.strip().title()
        params = urllib.parse.urlencode(
            {"search": 'patient.drug.medicinalproduct:"%s"' % alt,
             "count": "patient.reaction.reactionmeddrapt.exact", "limit": 10})
        data, err = get_json("%s/event.json?%s" % (OPENFDA, params),
                             timeout=60)
        if data is not None and "results" in data:
            query = alt
            med = 'patient.drug.medicinalproduct:"%s"' % alt
    if data is None or "results" not in data:
        return {"ok": False,
                "error": "No FAERS reports found for '%s' (%s)."
                         % (query, err or "empty result"),
                "source": "openFDA drug/event.json (FAERS)"}

    def _total(search):
        params = urllib.parse.urlencode({"search": search, "limit": 1})
        tot, _ = get_json("%s/event.json?%s" % (OPENFDA, params), timeout=60)
        try:
            return tot["meta"]["results"]["total"]
        except (KeyError, TypeError):
            return None

    reactions = [(r.get("term", "?"), r.get("count", 0))
                 for r in data.get("results", [])]
    return {
        "ok": True,
        "query": query,
        "top_reactions": reactions,
        "total_reports": _total(med),
        "serious_reports": _total("%s AND serious:2" % med),
        "source": "openFDA drug/event.json (FDA Adverse Event Reporting System)",
        "error": None,
    }


def fetch_interactions(query, label_sections=None):
    """Known drug interactions for a drug name.

    Two sub-sources, each reported separately:
    1. RxNav: resolve the name to an RxCUI, then read the interaction
       list. (Returned HTTP 404 on 2026-10-29; reported as unavailable
       rather than papered over.)
    2. The FDA label's own Drug Interactions section, when the label
       fetch produced one. This is official label text, not a pairwise
       database, and the report says so.
    """
    out = {"rxnav_pairs": [], "rxnav_error": None,
           "label_text": None, "label_source": None}
    q = urllib.parse.quote(query.strip())
    data, err = get_json(
        "%s/rxcui.json?name=%s&search=1" % (RXNAV, q), timeout=30)
    rxcui = None
    if data is not None:
        ids = (data.get("idGroup") or {}).get("rxnormId") or []
        rxcui = ids[0] if ids else None
    if rxcui:
        data, err = get_json(
            "%s/interaction/interaction.json?rxcui=%s" % (RXNAV, rxcui),
            timeout=30)
        if data is None:
            out["rxnav_error"] = (
                "NLM RxNav interaction API unavailable (%s); no pairwise "
                "interaction list could be retrieved." % err)
        else:
            for group in data.get("interactionTypeGroup") or []:
                for itype in group.get("interactionType") or []:
                    for pair in itype.get("interactionPair") or []:
                        concepts = pair.get("interactionConcept") or []
                        other = None
                        for concept in concepts:
                            item = (concept or {}).get("minConceptItem") or {}
                            if item.get("rxcui") != rxcui and item.get("name"):
                                other = item["name"]
                        if other:
                            out["rxnav_pairs"].append(
                                (other, pair.get("description") or ""))
            if not out["rxnav_pairs"]:
                out["rxnav_error"] = (
                    "RxNav returned no interaction pairs for this RxCUI.")
    else:
        out["rxnav_error"] = (
            "No RxCUI found for '%s' via NLM RxNorm (%s); pairwise "
            "interaction lookup not possible." % (query, err or "no id"))
    if label_sections and label_sections.get("drug_interactions"):
        out["label_text"] = label_sections["drug_interactions"]
        out["label_source"] = (
            "FDA label, Drug Interactions section (openFDA drug/label.json)")
    return out
