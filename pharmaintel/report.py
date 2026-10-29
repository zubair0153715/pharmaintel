"""Report rendering: one Markdown report, one optional HTML version.

Rules enforced here, not left to callers:
- The disclaimer is on every report, at the top.
- Every section names its source, or says "source unavailable" with the
  real error. Nothing is ever invented to fill a missing section.
- Long label texts are truncated with an explicit truncation note.
"""

import datetime
import html

DISCLAIMER = ("Research tool only — not medical advice. "
              "This report summarises public regulatory and spontaneous-"
              "report data; it is not a substitute for a pharmacist, "
              "prescriber, or the full official label.")

FAERS_CAVEAT = ("FAERS reports are voluntary and unverified: a report "
                "means someone reported an event while taking the drug, "
                "NOT that the drug caused it. Serious events are "
                "over-reported, and counts cover every product naming "
                "this drug, including combinations.")

SECTION_TITLES = {
    "boxed_warning": "Boxed warning",
    "indications_and_usage": "Indications and usage",
    "dosage_and_administration": "Dosage and administration",
    "contraindications": "Contraindications",
    "warnings": "Warnings",
    "adverse_reactions": "Adverse reactions (label)",
    "drug_interactions": "Drug interactions (label)",
}

MAX_SECTION_CHARS = 2000
MAX_PAIRS = 30


def _trunc(text, limit=MAX_SECTION_CHARS):
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + (
        "\n\n[…truncated here; see the full official FDA label for the "
        "complete text.]")


def build(drug, label, faers, interactions):
    """Assemble the report data dict consumed by both renderers."""
    today = datetime.date.today().isoformat()
    return {
        "drug": drug,
        "generated": today,
        "label": label,
        "faers": faers,
        "interactions": interactions,
    }


def to_markdown(rep):
    label = rep["label"]
    faers = rep["faers"]
    inter = rep["interactions"]
    lines = []
    lines.append("# PharmaIntel report: %s" % rep["drug"])
    lines.append("")
    lines.append("> **%s**" % DISCLAIMER)
    lines.append("")
    lines.append("_Generated %s. Sources are cited per section; any "
                 "section whose source failed says so instead of "
                 "showing invented data._" % rep["generated"])
    lines.append("")

    # ---- 1. FDA label summary ----
    lines.append("## 1. FDA label summary")
    if label["ok"]:
        lines.append("")
        lines.append("**Source:** %s" % label["source"])
        lines.append("")
        lines.append("- Generic name: %s" % label["generic_name"])
        if label["brand_names"]:
            lines.append("- Brand names on label: %s"
                         % ", ".join(label["brand_names"]))
        if label["manufacturer"]:
            lines.append("- Manufacturer: %s"
                         % "; ".join(label["manufacturer"]))
        for key in ("boxed_warning", "indications_and_usage",
                    "dosage_and_administration", "contraindications",
                    "warnings", "adverse_reactions"):
            text = label["sections"].get(key)
            if text:
                lines.append("")
                lines.append("### %s" % SECTION_TITLES[key])
                lines.append("")
                lines.append(_trunc(text))
    else:
        lines.append("")
        lines.append("**Source unavailable:** %s" % label["error"])
    lines.append("")

    # ---- 2. Known drug interactions ----
    lines.append("## 2. Known drug interactions")
    lines.append("")
    if inter["rxnav_pairs"]:
        lines.append("**Source:** NLM RxNav interaction API "
                     "(pairwise, via RxNorm RxCUI)")
        lines.append("")
        for other, desc in inter["rxnav_pairs"][:MAX_PAIRS]:
            lines.append("- **%s** — %s" % (other, desc))
        if len(inter["rxnav_pairs"]) > MAX_PAIRS:
            lines.append("- …and %d more pairs (see RxNav for the full "
                         "list)." % (len(inter["rxnav_pairs"]) - MAX_PAIRS))
    else:
        lines.append("**RxNav pairwise list unavailable:** %s"
                     % (inter["rxnav_error"] or "no pairs returned."))
    if inter["label_text"]:
        lines.append("")
        lines.append("**Source:** %s" % inter["label_source"])
        lines.append("")
        lines.append(_trunc(inter["label_text"]))
    elif label["ok"]:
        lines.append("")
        lines.append("**Label interaction text unavailable:** this FDA label "
                     "has no Drug Interactions section.")
    lines.append("")

    # ---- 3. FAERS adverse-event summary ----
    lines.append("## 3. FAERS adverse-event summary")
    lines.append("")
    lines.append("> %s" % FAERS_CAVEAT)
    if faers["ok"]:
        lines.append("")
        lines.append("**Source:** %s" % faers["source"])
        lines.append("")
        if faers["total_reports"] is not None:
            lines.append("- Total reports naming this drug: %s"
                         % f"{faers['total_reports']:,}")
        if faers["serious_reports"] is not None:
            lines.append("- Of those, serious: %s"
                         % f"{faers['serious_reports']:,}")
        lines.append("")
        lines.append("Most frequently reported reactions (by report count):")
        lines.append("")
        lines.append("| Reaction | Reports |")
        lines.append("|----------|---------|")
        for term, count in faers["top_reactions"]:
            lines.append("| %s | %s |" % (term, f"{count:,}"))
    else:
        lines.append("")
        lines.append("**Source unavailable:** %s" % faers["error"])
    lines.append("")
    lines.append("---")
    lines.append("_PharmaIntel v1 — original glue code over public APIs. "
                 "No patient data, no keys, no proprietary data._")
    return "\n".join(lines) + "\n"


def to_html(rep):
    """Small self-contained HTML rendering of the same report."""
    md_title = "PharmaIntel report: %s" % html.escape(rep["drug"])
    body = []
    body.append("<p><strong>%s</strong></p>" % html.escape(DISCLAIMER))
    body.append("<p><em>Generated %s. Sources are cited per section."
                "</em></p>" % rep["generated"])
    label = rep["label"]
    body.append("<h2>1. FDA label summary</h2>")
    if label["ok"]:
        body.append("<p><strong>Source:</strong> %s</p>"
                    % html.escape(label["source"]))
        body.append("<p>Generic name: %s</p>"
                    % html.escape(label["generic_name"]))
        if label["brand_names"]:
            body.append("<p>Brand names on label: %s</p>"
                        % html.escape(", ".join(label["brand_names"])))
        for key in ("boxed_warning", "indications_and_usage",
                    "dosage_and_administration", "contraindications",
                    "warnings", "adverse_reactions"):
            text = label["sections"].get(key)
            if text:
                body.append("<h3>%s</h3>" % SECTION_TITLES[key])
                body.append("<p>%s</p>"
                            % html.escape(_trunc(text)))
    else:
        body.append("<p><strong>Source unavailable:</strong> %s</p>"
                    % html.escape(label["error"]))
    inter = rep["interactions"]
    body.append("<h2>2. Known drug interactions</h2>")
    if inter["rxnav_pairs"]:
        body.append("<p><strong>Source:</strong> NLM RxNav interaction "
                    "API</p><ul>")
        for other, desc in inter["rxnav_pairs"][:MAX_PAIRS]:
            body.append("<li><strong>%s</strong> — %s</li>"
                        % (html.escape(other), html.escape(desc)))
        body.append("</ul>")
    else:
        body.append("<p><strong>RxNav pairwise list unavailable:</strong> "
                    "%s</p>" % html.escape(inter["rxnav_error"] or ""))
    if inter["label_text"]:
        body.append("<p><strong>Source:</strong> %s</p>"
                    % html.escape(inter["label_source"]))
        body.append("<p>%s</p>" % html.escape(_trunc(inter["label_text"])))
    faers = rep["faers"]
    body.append("<h2>3. FAERS adverse-event summary</h2>")
    body.append("<p><em>%s</em></p>" % html.escape(FAERS_CAVEAT))
    if faers["ok"]:
        body.append("<p><strong>Source:</strong> %s</p>"
                    % html.escape(faers["source"]))
        if faers["total_reports"] is not None:
            body.append("<p>Total reports: %s; serious: %s</p>"
                        % (f"{faers['total_reports']:,}",
                           f"{faers['serious_reports']:,}"
                           if faers["serious_reports"] is not None
                           else "unknown"))
        body.append("<table><tr><th>Reaction</th><th>Reports</th></tr>")
        for term, count in faers["top_reactions"]:
            body.append("<tr><td>%s</td><td>%s</td></tr>"
                        % (html.escape(term), f"{count:,}"))
        body.append("</table>")
    else:
        body.append("<p><strong>Source unavailable:</strong> %s</p>"
                    % html.escape(faers["error"]))
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<title>%s</title>\n"
        "<style>body{font-family:sans-serif;max-width:760px;margin:2em auto;"
        "padding:0 1em;line-height:1.5}table{border-collapse:collapse}"
        "td,th{border:1px solid #ccc;padding:4px 8px;text-align:left}"
        "</style>\n</head>\n<body>\n<h1>%s</h1>\n%s\n</body>\n</html>\n"
        % (md_title, md_title, "\n".join(body)))
