#!/usr/bin/env python3
"""Layer B JSON (same structure as layer_b_mx.json) from the layer B CSVs. Usage: build-argentina-b-json.py <raw_dir> <out_dir>"""
import csv, hashlib, json, os, sys


def _clean(o):
    """Replace NaN/inf with None so the JSON stays valid for JavaScript (JSON.parse rejects NaN)."""
    import math
    if isinstance(o, float):
        return None if math.isnan(o) or math.isinf(o) else o
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    try:
        import numpy as _np
        if isinstance(o, _np.floating):
            return None if _np.isnan(o) or _np.isinf(o) else float(o)
        if isinstance(o, _np.integer):
            return int(o)
    except ImportError:
        pass
    return o

raw, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(out, "b_survey_indicators_ar.csv"), encoding="utf-8")))
grp = list(csv.DictReader(open(os.path.join(out, "b_comparison_groups_ar.csv"), encoding="utf-8")))
foc = [r for r in rows if r["group_code"] == "AR" and r["survey_segment"] == "all_respondents"]
def head(iid):
    r = [x for x in foc if x["indicator_id"] == iid][0]
    return dict(item=r["item"], proportion=float(r["proportion"]), numerator=r["numerator"], valid_n=r["valid_n"],
                ci_95=[r["ci_low"], r["ci_high"]])
n = int([g for g in grp if g["group_code"] == "AR" and g["survey_segment"] == "all_respondents"][0]["respondents"])
sha = lambda f: hashlib.sha256(open(os.path.join(raw, f), "rb").read()).hexdigest()
d = dict(country="AR", layer="B", source_id="SRC_SO_2025", survey="Stack Overflow Developer Survey", survey_year=2025,
         source=dict(repository="https://github.com/StackExchange/Survey", commit="c9c23dc6f385d5be1a3011c238deb6c23b617e93",
                     path="packages/archive/2025/results.csv", sha256=sha("results.csv"),
                     official_aggregate=dict(file="ai.json", sha256=sha("ai.json"))),
         engine=dict(script="scripts/build-argentina-b-survey.py",
                     note="Re-implementation of the Peru/Mexico layer_b_engine.py rules; run with Mexico as focus it reproduces "
                          "the 1,264 indicator rows, 280 distribution rows and 8 group rows of the Mexico package exactly."),
         headline={k: head(k) for k in ["B1", "B2", "B3"]},
         B5_respondents=n, B5_confidence="low (below 300)" if n < 300 else "medium or high (300 or more)",
         checks=dict(mexico_package_reproduction=dict(indicator_rows=1264, distribution_rows=280, group_rows=8, differences=0),
                     argentina_rows_in_mexico_package=dict(note="The Mexico package already published Argentina as a comparison "
                                                                "group (158 rows); the AR all-respondents rows here are the same cells.")),
         notes=dict(edition="2025 edition, the same file as Colombia's template example and the Peru and Mexico packages, so the "
                            "countries compare on one survey.",
                    comparison_groups="Argentina, Argentina professional developers, LATAM excluding Argentina (18 countries), "
                                      "global, and Brazil, Mexico, Colombia and Chile."),
         limitations="Self-selected online survey: unweighted, not representative of all developers in Argentina. Cells with fewer "
                     "than 30 valid answers are suppressed (empty), never zero.")
json.dump(_clean(d), open(os.path.join(out, "layer_b_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(d["headline"], indent=0)[:600], n)
