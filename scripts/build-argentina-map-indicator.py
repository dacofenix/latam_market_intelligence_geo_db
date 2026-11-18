#!/usr/bin/env python3
"""fact_map_indicator (Peru/Mexico format, scope_id = AR) for layers A, B, I, O, P, and fact_developers_country.
Usage: build-argentina-map-indicator.py <research-argentina_dir>
"""
import sys, os, csv, json
import pandas as pd

OUT = sys.argv[1]
CSV = os.path.join(OUT, "geodb", "csv"); OUTP = os.path.join(OUT, "outputs")
COLS = ["layer", "metric_id", "scope_type", "scope_id", "group_id", "persona_id", "indicator", "category", "value", "unit", "period",
        "comparison_period", "numerator", "denominator", "status", "source_id", "method", "limitations"]


def main():
    rows = []
    a = pd.read_csv(os.path.join(OUTP, "a_github_indicators_ar.csv"), dtype=str, keep_default_na=False)
    for r in a.itertuples():
        rows.append(dict(layer="A", metric_id=r.indicator_id, scope_type="country", scope_id="AR", group_id="", persona_id="",
                         indicator=r.indicator_name, category="", value=r.value, unit=r.unit, period=r.period_label,
                         comparison_period=r.comparison_period_label, numerator=r.numerator, denominator=r.denominator,
                         status=f"{r.canonical_status};{r.validation_status}", source_id="SRC_GH_IG", method=r.method,
                         limitations="Matches the Think4ever LATAM breakdown (data/geodb-v2/csv/fact_developers_country.csv, AR row)."))
    b = pd.read_csv(os.path.join(OUTP, "b_survey_indicators_ar.csv"), dtype=str, keep_default_na=False)
    idx = {}
    for r in b.itertuples():
        k = (r.group_type, r.group_code, r.survey_segment)
        idx[k] = idx.get(k, 0) + 1
        rows.append(dict(layer="B", metric_id=f"B:{r.survey_year}:{r.indicator_id}:{r.group_type}:{r.group_code}:{r.survey_segment}:{idx[k]}",
                         scope_type="country", scope_id="AR", group_id=r.group_code, persona_id="", indicator=r.item, category="",
                         value=r.proportion, unit="proportion", period=r.survey_year, comparison_period="", numerator=r.numerator,
                         denominator=r.valid_n, status="low_confidence_self_selected_survey", source_id=r.source_id, method="",
                         limitations=f"{r.group_type}:{r.group_definition}; suppress={r.base_flag}; low_n={r.small_numerator_flag}"))
    iop = pd.read_csv(os.path.join(OUTP, "_iop_rows_ar.csv"), dtype=str, keep_default_na=False)
    for r in iop.to_dict(orient="records"):
        rows.append({c: r.get(c, "") for c in COLS})
    with open(os.path.join(CSV, "fact_map_indicator.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    e = json.load(open(os.path.join(OUTP, "_a_engine_ar.json")))
    pd.DataFrame(e["fdc"]).to_csv(os.path.join(CSV, "fact_developers_country.csv"), index=False)
    print(pd.DataFrame(rows).layer.value_counts().to_dict())


if __name__ == "__main__":
    main()
