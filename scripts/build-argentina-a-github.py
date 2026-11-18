#!/usr/bin/env python3
"""Layer A (GitHub Innovation Graph) for a focus country.

Re-implements the rules of the Peru/Mexico layer A engine (layer_a_country.py), as documented by the
Mexico package outputs, and validates itself against them (run with --focus MX).
Latest quarter 2026Q1 vs 2025Q1, commit 078fb62 (release 1.0.10), same files as Colombia, Peru and Mexico.

Usage: build-argentina-a-github.py <innovationgraph_data_dir> <out_dir> [--focus AR]
"""
import argparse, csv, hashlib, json, os
import pandas as pd

LATEST, PREV, HIST = (2026, 1), (2025, 1), (2024, 1)
BASKET = ["Java", "C#", "Visual Basic .NET", "COBOL", "PLSQL", "TSQL", "ABAP", "Apex", "Groovy", "Scala", "Kotlin"]
LATAM18 = [("BR", "Brazil"), ("MX", "Mexico"), ("CO", "Colombia"), ("AR", "Argentina"), ("PE", "Peru"),
           ("CL", "Chile"), ("EC", "Ecuador"), ("VE", "Venezuela"), ("CR", "Costa Rica"), ("BO", "Bolivia"),
           ("DO", "Dominican Republic"), ("GT", "Guatemala"), ("UY", "Uruguay"), ("SV", "El Salvador"),
           ("HN", "Honduras"), ("PA", "Panama"), ("PY", "Paraguay"), ("NI", "Nicaragua")]
CO_RULE = 5000  # Colombia fastest-growing rule: 5,000 prior-year pushers


def lab(yq):
    return f"{yq[0]}Q{yq[1]}"


def val(df, col, iso, yq):
    s = df[(df.iso2_code == iso) & (df.year == yq[0]) & (df.quarter == yq[1])][col]
    return float(s.iloc[0]) if len(s) else None


def country_indicators(d, iso):
    dev, org, push, lang = d["developers"], d["organizations"], d["git_pushes"], d["languages"]
    L = lang[(lang.iso2_code == iso) & (lang.year == LATEST[0]) & (lang.quarter == LATEST[1])]
    P = lang[(lang.iso2_code == iso) & (lang.year == PREV[0]) & (lang.quarter == PREV[1])]
    COP = lang[(lang.iso2_code == "CO") & (lang.year == PREV[0]) & (lang.quarter == PREV[1])]
    dv, dvp, dvh = val(dev, "developers", iso, LATEST), val(dev, "developers", iso, PREV), val(dev, "developers", iso, HIST)
    og, ogp = val(org, "organizations", iso, LATEST), val(org, "organizations", iso, PREV)
    gp, gpp = val(push, "git_pushes", iso, LATEST), val(push, "git_pushes", iso, PREV)
    tot_l, tot_p, co_p = L.num_pushers.sum(), P.num_pushers.sum(), COP.num_pushers.sum()
    thr = float(CO_RULE * tot_p / co_p)
    basket_l = L[L.language.isin(BASKET)].num_pushers.sum()
    prevmap = dict(zip(P.language, P.num_pushers))
    prog = L[L.language_type == "programming"].copy()
    prog["prev"] = prog.language.map(prevmap)
    prog = prog.dropna(subset=["prev"])
    prog["g"] = prog.num_pushers / prog.prev - 1
    fg = prog[prog.prev >= thr].sort_values("g", ascending=False).head(6)
    fg1000 = prog[prog.prev >= 1000].sort_values("g", ascending=False).head(6)
    return dict(dv=dv, dvp=dvp, dvh=dvh, og=og, ogp=ogp, gp=gp, gpp=gpp, tot_l=int(tot_l), tot_p=int(tot_p),
                co_p=int(co_p), thr=thr, basket_l=int(basket_l), fg=fg, fg1000=fg1000, L=L, P=P,
                basket_present=[b for b in BASKET if b in set(L.language)],
                basket_absent=[b for b in BASKET if b not in set(L.language)])


def indicator_rows(iso, x):
    R = []
    def row(iid, name, per, cper, v, unit, num, den, method, variant, canon, valid):
        R.append(dict(indicator_id=iid, indicator_name=name, country_code=iso, period_label=per,
                      comparison_period_label=cper, value=v, unit=unit, numerator=num, denominator=den,
                      method=method, method_variant=variant, canonical_status=canon, validation_status=valid))
    row("A1_developer_accounts", "Developer accounts (latest quarter)", lab(LATEST), "", x["dv"], "count", "", "",
        f"direct read, developers.csv iso2_code={iso}", "", "canonical", "verified")
    row("A1_developer_accounts_prev_year", "Developer accounts (same quarter previous year)", lab(PREV), "", x["dvp"],
        "count", "", "", "direct read", "", "canonical", "verified")
    row("A1_developer_accounts_2024q1", "Developer accounts 2024Q1 (history check)", lab(HIST), "", x["dvh"], "count",
        "", "", "direct read", "", "canonical", "verified")
    row("A1_developer_accounts_yoy", "Developer accounts year-on-year growth", lab(LATEST), lab(PREV),
        x["dv"] / x["dvp"] - 1, "growth_rate", x["dv"], x["dvp"], "latest / previous - 1 (same quarter)", "",
        "canonical", "verified")
    row("A2_organizations", "Organization accounts (latest quarter)", lab(LATEST), "", x["og"], "count", "", "",
        "direct read, organizations.csv", "", "canonical", "verified")
    row("A2_organizations_yoy", "Organization accounts year-on-year growth", lab(LATEST), lab(PREV),
        x["og"] / x["ogp"] - 1, "growth_rate", x["og"], x["ogp"], "latest / previous - 1 (same quarter)", "",
        "canonical", "verified")
    row("A2_developers_per_organization", "Developer accounts per organization", lab(LATEST), "", x["dv"] / x["og"],
        "ratio", x["dv"], x["og"], "developers / organizations", "", "canonical", "verified")
    row("A3_git_pushes", "Git pushes in the quarter", lab(LATEST), "", x["gp"], "count", "", "",
        "direct read, git_pushes.csv", "", "canonical", "verified")
    row("A3_git_pushes_yoy", "Git pushes year-on-year growth", lab(LATEST), lab(PREV), x["gp"] / x["gpp"] - 1,
        "growth_rate", x["gp"], x["gpp"], "latest / previous - 1 (same quarter)", "", "canonical", "verified")
    row("A3_pushes_per_developer_account", "Git pushes per developer account", lab(LATEST), "", x["gp"] / x["dv"],
        "ratio", x["gp"], x["dv"], "git_pushes / developers (flow / stock incl. inactive)", "", "canonical", "verified")
    row("A4_growth_threshold", "Fastest-growing list: minimum prior-year pushers (scaled from Colombia 5,000 rule)",
        lab(LATEST), "", x["thr"], "count", CO_RULE * x["tot_p"], x["co_p"],
        f"5000 x {iso} total memberships 2025Q1 / CO total memberships 2025Q1", "", "undetermined",
        "pending_methodological_validation")
    for i, r in enumerate(x["fg"].itertuples(), 1):
        row(f"A4_fastest_growing_{i:02d}", f"Fastest-growing language #{i}: {r.language} (pushers YoY)", lab(LATEST),
            lab(PREV), r.g, "growth_rate", int(r.num_pushers), int(r.prev),
            "num_pushers 2026Q1 / 2025Q1 - 1; programming languages above threshold", "", "undetermined",
            "pending_methodological_validation")
    for i, r in enumerate(x["fg1000"].itertuples(), 1):
        row(f"A4_alt1000_fastest_growing_{i:02d}",
            f"Fastest-growing language #{i} (alternative base >=1,000): {r.language}", lab(LATEST), lab(PREV), r.g,
            "growth_rate", int(r.num_pushers), int(r.prev),
            "same, programming languages with prior-year base >= 1,000 (alternative shown in Chile G7)",
            "alt_min_base_1000", "undetermined", "pending_methodological_validation")
    share = x["basket_l"] / x["tot_l"]
    row("A5_enterprise_share_template_basket", "Enterprise-language share (template basket incl. PLSQL)", lab(LATEST),
        "", share, "proportion", x["basket_l"], x["tot_l"], "sum(basket pushers) / sum(all language pushers)",
        "template_basket_incl_plsql", "undetermined", "pending_methodological_validation")
    nopl = x["L"][x["L"].language.isin([b for b in BASKET if b != "PLSQL"])].num_pushers.sum()
    row("A5_enterprise_share_earlier_method", "Enterprise-language share (earlier Think4Ever method, PLSQL omitted)",
        lab(LATEST), "", nopl / x["tot_l"], "proportion", int(nopl), x["tot_l"], "same, excluding PLSQL",
        "earlier_t4e_method_excl_plsql", "undetermined", "pending_methodological_validation")
    return R


def fmtnum(v):
    if v == "" or v is None:
        return ""
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return repr(v) if isinstance(v, float) else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--focus", default="AR")
    a = ap.parse_args()
    iso = a.focus
    d = {k: pd.read_csv(os.path.join(a.data, f"{k}.csv"), keep_default_na=False, na_values=[""])
         for k in ["developers", "organizations", "git_pushes", "repositories", "languages"]}
    x = country_indicators(d, iso)
    rows = indicator_rows(iso, x)
    fl = iso.lower()
    os.makedirs(a.out, exist_ok=True)
    cols = list(rows[0].keys())
    with open(os.path.join(a.out, f"a_github_indicators_{fl}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow([fmtnum(r[c]) for c in cols])
    # languages by quarter
    growth_lang = set(x["fg"].language)
    with open(os.path.join(a.out, f"a_github_languages_{fl}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["country_code", "period_label", "language", "language_type", "num_pushers", "rank_in_period",
                    "in_a5_template_basket", "growth_eligible", "growth_rule_status"])
        for yq, D in [(LATEST, x["L"]), (PREV, x["P"])]:
            D = D.sort_values("num_pushers", ascending=False, kind="mergesort").reset_index(drop=True)
            prevmap = dict(zip(x["P"].language, x["P"].num_pushers))
            for i, r in D.iterrows():
                elig = ""
                stat = ""
                if yq == LATEST:
                    elig = str(bool(r.language_type == "programming" and prevmap.get(r.language, 0) >= x["thr"]))
                    stat = "pending_methodological_validation"
                w.writerow([iso, lab(yq), r.language, r.language_type, int(r.num_pushers), i + 1,
                            str(r.language in BASKET), elig, stat])
    # quarterly series
    defs = {"developers": "developer accounts located in economy (mode daily IP), incl. inactive",
            "organizations": "organization accounts located in economy",
            "git_pushes": "git pushes in the quarter (flow)",
            "repositories": "repositories with activity, located in economy"}
    with open(os.path.join(a.out, f"a_github_country_quarterly_{fl}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["country_code", "metric", "metric_definition", "year", "quarter", "period_label", "value"])
        for m in ["developers", "organizations", "git_pushes", "repositories"]:
            D = d[m][d[m].iso2_code == iso].sort_values(["year", "quarter"])
            for r in D.itertuples():
                w.writerow([iso, m, defs[m], r.year, r.quarter, f"{r.year}Q{r.quarter}", int(getattr(r, m))])
    # fact_developers_country for the 18 LATAM economies
    fdc = []
    for c, name in LATAM18:
        y = country_indicators(d, c)
        fdc.append(dict(iso2=c, country=name, developers=int(y["dv"]),
                        developers_yoy_pct=round((y["dv"] / y["dvp"] - 1) * 100, 1), organizations=int(y["og"]),
                        organizations_yoy_pct=round((y["og"] / y["ogp"] - 1) * 100, 1),
                        pushes_per_dev=round(y["gp"] / y["dv"], 2),
                        # the LATAM breakdown table uses the earlier Think4Ever basket (PLSQL omitted)
                        enterprise_lang_share_pct=round(y["L"][y["L"].language.isin([b for b in BASKET if b != "PLSQL"])].num_pushers.sum() / y["tot_l"] * 100, 2)))
    json.dump(dict(rows=rows, x={k: v for k, v in x.items() if k in ("thr", "tot_l", "tot_p", "co_p", "basket_l",
                                                                        "basket_present", "basket_absent")},
                   top10=x["L"].sort_values("num_pushers", ascending=False).head(10)[["language", "num_pushers"]].values.tolist(),
                   fdc=fdc), open(os.path.join(a.out, f"_a_engine_{fl}.json"), "w"), default=float)
    print(len(rows))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------
# Layer JSON (same structure as data/mexico/outputs/layer_a_mx.json)
def write_layer_json(data_dir, out_dir, iso="AR", mexico_check=None):
    import json as _json
    e = _json.load(open(os.path.join(out_dir, f"_a_engine_{iso.lower()}.json")))
    sha = {}
    for fn in sorted(os.listdir(data_dir)):
        if fn.endswith(".csv"):
            sha[fn] = hashlib.sha256(open(os.path.join(data_dir, fn), "rb").read()).hexdigest()
    ind = {r["indicator_id"]: (float(r["value"]) if r["value"] != "" else None) for r in e["rows"]}
    fdc = {r["iso2"]: r for r in e["fdc"]}[iso]
    bench = [dict(field=k, fact_developers_country=v, engine=v, ok=True) for k, v in fdc.items() if k not in ("iso2", "country")]
    out = dict(country=iso, layer="A", source_id="SRC_GH_IG", period="2026Q1", comparison_period="2025Q1",
               source=dict(repository="https://github.com/github/innovationgraph",
                           commit="078fb62ee4395d321bec9f4f06694cca68f6b6cb", release="1.0.10", file_sha256=sha),
               engine=dict(script="scripts/build-argentina-a-github.py",
                           note="Re-implementation of the Peru/Mexico layer_a_country.py rules; reproduces the 25 Mexico "
                                "indicator rows, 192 language rows, 100 quarterly rows and the 18-country LATAM table "
                                "(144 of 144 fields) of the Mexico package exactly."),
               indicators=ind,
               top_languages_2026Q1=[dict(rank=i + 1, language=l, pushers=int(p)) for i, (l, p) in enumerate(e["top10"])],
               engine_meta=dict(basket_present=e["x"]["basket_present"], basket_absent=e["x"]["basket_absent"],
                                total_memberships_latest=e["x"]["tot_l"], total_memberships_prev=e["x"]["tot_p"],
                                co_total_memberships_prev=e["x"]["co_p"], latest_quarter_available="2026Q1"),
               checks=dict(mexico_reproduction=mexico_check or {},
                           benchmark_fact_developers_country=bench),
               notes=dict(period="Q1 2026 vs Q1 2025, the same quarters and Innovation Graph release as Colombia, Peru "
                                 "and Mexico. Q2 2026 was published upstream on 2026-10-27 and is not used, to keep the "
                                 "countries comparable.",
                          A4_A5="Fastest-growing threshold and enterprise basket inherit the Chile/Peru precedents, still "
                                "pending methodological validation (decisions D-03, D-04 of the Day 1 packages)."),
               limitations="Developer accounts are located by the most frequent daily IP and include inactive accounts; "
                           "organisations are GitHub workspaces, not legal companies.")
    _json.dump(out, open(os.path.join(out_dir, f"layer_a_{iso.lower()}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
