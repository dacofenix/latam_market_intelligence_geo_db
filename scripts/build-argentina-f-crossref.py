#!/usr/bin/env python3
"""Readable cross-reference between Argentina's occupation codes (CNO-2001, used by the EPH) and the 13 template
personas (CIUO-08 / ISCO-08 codes), so each persona row of fact_persona_profile can be traced to the job codes behind it.

For every persona it lists the CNO-2001 codes assigned to it (D-AR-09) and the other codes where its workers sit,
with two shares measured on INDEC's double-coded EPH 2015 Q1+Q2 (the same data used for the assignment):
  - pct_code_workers_in_persona: of the people with this CNO-2001 code, % whose CIUO-08 code belongs to the persona;
  - pct_persona_workers_in_code: of the people whose CIUO-08 code belongs to the persona, % who have this CNO-2001 code.
It also gives the 2025 EPH employed and interviews for each code. A code enters a persona only when the first share
is at least 50% with 5+ interviews in 2015.
Usage: build-argentina-f-crossref.py <raw_dir> <research-argentina_dir>
"""
import sys, os, importlib.util
import pandas as pd

RAW, OUT = sys.argv[1], sys.argv[2]
OUTP = os.path.join(OUT, "outputs")
spec = importlib.util.spec_from_file_location("cnomap", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-argentina-f-cno-mapping.py"))
cnomap = importlib.util.module_from_spec(spec)
sys.argv = sys.argv[:1]  # the mapping module only reads argv under __main__
spec.loader.exec_module(cnomap)
MIN_SHARE_LISTED = 3.0   # list a non-assigned code when it holds at least 3% of the persona's 2015 workers (always the top 5)
MAX_ROWS = 12


def load_2015():
    pairs = [("indec_eph_2015/ar_raw_t115_dta/Individual_t115.dta", "indec_cno_caes/ciuo115/ar_raw_EPH_CIUO_115/eph_ciuo_115.dta"),
             ("indec_eph_2015/ar_raw_t215_dta/Individual_t215.dta", "indec_cno_caes/ciuo215/ar_raw_EPH_CIUO_215/eph_ciuo_215.dta")]
    frames = []
    for ind, ciu in pairs:
        I = pd.read_stata(os.path.join(RAW, ind), convert_categoricals=False)
        C = pd.read_stata(os.path.join(RAW, ciu), convert_categoricals=False)
        I.columns = [c.lower() for c in I.columns]; C.columns = [c.lower() for c in C.columns]
        for d in (I, C):
            d["codusu"] = d["codusu"].astype(str).str.strip()
        M = I.merge(C[["codusu", "nro_hogar", "componente", "pp04d_ciuo"]], on=["codusu", "nro_hogar", "componente"], how="left")
        frames.append(M[M.estado == 1][["pp04d_cod", "pp04d_ciuo", "pondera"]])
    D = pd.concat(frames)
    D["cno"] = D.pp04d_cod.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(5)
    D["isco"] = pd.to_numeric(D.pp04d_ciuo, errors="coerce")
    D["pondera"] = D.pondera.astype(float)
    return D[D.isco.notna()]


def load_2025():
    frames = []
    for q in (1, 2, 3, 4):
        d = pd.read_csv(os.path.join(RAW, "indec_eph_2025", "x", f"usu_individual_T{q}25.txt"), sep=";", low_memory=False, decimal=",",
                        usecols=["ESTADO", "PP04D_COD", "PONDERA"])
        frames.append(d[d.ESTADO == 1])
    D = pd.concat(frames)
    D["cno"] = D.PP04D_COD.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(5)
    g = D.groupby("cno").agg(employed_2025=("PONDERA", lambda s: s.sum() / 4), interviews_2025=("PONDERA", "size"))
    g["employed_2025"] = g.employed_2025.round().astype(int)
    return g


def why(included, other, st):
    if included:
        return "included: most of this code's workers are this persona"
    if other:
        return f"code belongs to {other}"
    if st == "excluded_small_sample":
        return "not used: fewer than 5 interviews in 2015"
    if st == "excluded_minority":
        return "not used: no persona reaches 50% of this code"
    if st == "outside_personas":
        return "not used: most of this code's workers are outside the 13 personas"
    return "not used"


def main():
    D = load_2015()
    E = load_2025()
    mp = pd.read_csv(os.path.join(OUTP, "f_occupation_mapping_ar.csv"), dtype=str).fillna("")
    assigned = dict(zip(mp.cno2001_code, mp.persona_id))
    status = dict(zip(mp.cno2001_code, mp.mapping_status))
    code_w = D.groupby("cno").pondera.sum()
    code_n = D.groupby("cno").size()
    rows = []
    for pid, name, ring, isco in cnomap.PERSONAS:
        inp = D.isco.isin(isco)
        persona_w = D.loc[inp, "pondera"].sum()
        by_code = D[inp].groupby("cno").pondera.sum()
        codes = set(by_code.index) | {c for c, p in assigned.items() if p == pid}
        cand = []
        for c in codes:
            share_p = 100 * by_code.get(c, 0) / persona_w if persona_w else 0
            share_c = 100 * by_code.get(c, 0) / code_w[c] if c in code_w else 0
            inc = assigned.get(c) == pid
            cand.append((inc, share_p, share_c, c))
        cand.sort(key=lambda x: (not x[0], -x[1]))
        # assigned codes, then codes holding 3%+ of the persona's workers (at least the top 5), up to 12 rows
        keep = [x for x in cand if x[0]]
        others = [x for x in cand if not x[0]]
        keep += [x for i, x in enumerate(others) if x[1] >= MIN_SHARE_LISTED or i < 5]
        for inc, share_p, share_c, c in keep[:MAX_ROWS]:
            other = assigned.get(c, "")
            rows.append(dict(
                persona_id=pid, persona=name, ring=ring, isco08_template_codes=";".join(map(str, isco)),
                cno2001_code=c, cno2001_label=cnomap.cno_label(c),
                included_in_persona="yes" if inc else "no",
                why=why(inc, other, status.get(c, "")),
                pct_code_workers_in_persona=round(share_c, 1), pct_persona_workers_in_code=round(share_p, 1),
                interviews_2015=int(code_n.get(c, 0)),
                employed_2025=int(E.employed_2025.get(c, 0)) if c in E.index else 0,
                interviews_2025=int(E.interviews_2025.get(c, 0)) if c in E.index else 0))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTP, "f_persona_crossref_ar.csv"), index=False)
    print(out.groupby("persona_id").size().to_dict())
    print(out[out.included_in_persona == "yes"].groupby("persona_id").employed_2025.sum().to_dict())


if __name__ == "__main__":
    main()
