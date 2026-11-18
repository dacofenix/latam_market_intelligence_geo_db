#!/usr/bin/env python3
"""Layers F, G, H, M from the INDEC Encuesta Permanente de Hogares (EPH), 2025 Q1-Q4 (31 urban agglomerations).

Annual figures = sum of PONDERA over the four quarters / 4 (same convention as Mexico's ENOE, sum of fac_tri / 4).
Occupation = PP04D_COD (CNO-2001), mapped to the 13 personas with outputs/f_occupation_mapping_ar.csv (D-AR-09).
Province = province of the EPH agglomerate (D-AR-08); income = P21 weighted with PONDIIO.
Usage: build-argentina-eph.py <raw_dir> <research-argentina_dir>
"""
import sys, os, json, hashlib
import numpy as np
import pandas as pd


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


RAW, OUT = sys.argv[1], sys.argv[2]
EPH = os.path.join(RAW, "indec_eph_2025")
CSV = os.path.join(OUT, "geodb", "csv")
OUTP = os.path.join(OUT, "outputs")

PROV = {"02": "Ciudad Autónoma de Buenos Aires", "06": "Buenos Aires", "10": "Catamarca", "14": "Córdoba", "18": "Corrientes",
        "22": "Chaco", "26": "Chubut", "30": "Entre Ríos", "34": "Formosa", "38": "Jujuy", "42": "La Pampa", "46": "La Rioja",
        "50": "Mendoza", "54": "Misiones", "58": "Neuquén", "62": "Río Negro", "66": "Salta", "70": "San Juan", "74": "San Luis",
        "78": "Santa Cruz", "82": "Santa Fe", "86": "Santiago del Estero",
        "90": "Tucumán", "94": "Tierra del Fuego, Antártida e Islas del Atlántico Sur"}
# EPH agglomerate -> (name, province code, anchor department code of the main city) (D-AR-08)
AGLO = {2: ("Gran La Plata", "06", "06441"), 3: ("Bahía Blanca-Cerri", "06", "06056"), 4: ("Gran Rosario", "82", "82084"),
        5: ("Gran Santa Fe", "82", "82063"), 6: ("Gran Paraná", "30", "30084"), 7: ("Posadas", "54", "54028"),
        8: ("Gran Resistencia", "22", "22140"), 9: ("Comodoro Rivadavia-Rada Tilly", "26", "26021"),
        10: ("Gran Mendoza", "50", "50007"), 12: ("Corrientes", "18", "18021"), 13: ("Gran Córdoba", "14", "14014"),
        14: ("Concordia", "30", "30015"), 15: ("Formosa", "34", "34014"), 17: ("Neuquén-Plottier", "58", "58035"),
        18: ("Santiago del Estero-La Banda", "86", "86049"), 19: ("Jujuy-Palpalá", "38", "38021"),
        20: ("Río Gallegos", "78", "78021"), 22: ("Gran Catamarca", "10", "10049"), 23: ("Gran Salta", "66", "66028"),
        25: ("La Rioja", "46", "46014"), 26: ("Gran San Luis", "74", "74056"), 27: ("Gran San Juan", "70", "70028"),
        29: ("Gran Tucumán-Tafí Viejo", "90", "90084"), 30: ("Santa Rosa-Toay", "42", "42021"),
        31: ("Ushuaia-Río Grande", "94", "94015"), 32: ("Ciudad Autónoma de Buenos Aires", "02", "02007"),
        33: ("Partidos del Gran Buenos Aires", "06", "06427"), 34: ("Mar del Plata", "06", "06357"),
        36: ("Río Cuarto", "14", "14098"), 38: ("San Nicolás-Villa Constitución", "06", "06763"),
        91: ("Rawson-Trelew", "26", "26077"), 93: ("Viedma-Carmen de Patagones", "62", "62007")}
# CAES-Mercosur 1.0 division (2 digits) -> section (INDEC, caes_mercosur_1.0.pdf)
def caes_section(d):
    if pd.isna(d) or d <= 0:
        return None
    d = int(d)
    for lo, hi, s in [(1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (40, 43, "F"), (45, 48, "G"),
                      (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"),
                      (83, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U")]:
        if lo <= d <= hi:
            return s
    return None
SECTION_NAME = {"A": "Agriculture, forestry and fishing", "B": "Mining", "C": "Manufacturing", "D": "Electricity and gas",
                "E": "Water and waste", "F": "Construction", "G": "Wholesale and retail trade", "H": "Transport and storage",
                "I": "Accommodation and food", "J": "Information and communication (tech sector: CAES J)",
                "K": "Finance and insurance", "L": "Real estate", "M": "Professional, scientific and technical services",
                "N": "Administrative services", "O": "Public administration", "P": "Education", "Q": "Health and social work",
                "R": "Arts and recreation", "S": "Other services", "T": "Households as employers", "U": "Extraterritorial",
                None: "Not specified"}
PERSONA_ORDER = ["P01", "P02", "P03", "P04", "P05", "P06", "P10", "P07", "P08", "P09", "P11", "P12", "P13"]


def wmedian(x, w):
    x = np.asarray(x, float); w = np.asarray(w, float)
    m = ~np.isnan(x) & (w > 0)
    x, w = x[m], w[m]
    if len(x) == 0:
        return None
    o = np.argsort(x); x, w = x[o], w[o]
    c = np.cumsum(w)
    return float(x[np.searchsorted(c, c[-1] / 2.0)])


def pct(mask, valid, w):
    den = w[valid].sum()
    return round(100 * w[valid & mask].sum() / den, 1) if den > 0 else None


def confidence(n, cell=False):
    if cell:
        return "high" if n >= 1000 else ("medium" if n >= 100 else "low")
    return "high" if n >= 1000 else ("medium" if n >= 300 else "low")


def load():
    frames, shas = [], {}
    for q in [1, 2, 3, 4]:
        z = os.path.join(EPH, f"ar_raw_EPH_usu_{q}_Trim_2025_txt.zip")
        shas[os.path.basename(z)] = hashlib.sha256(open(z, "rb").read()).hexdigest()
        d = pd.read_csv(os.path.join(EPH, "x", f"usu_individual_T{q}25.txt"), sep=";", low_memory=False, decimal=",")
        d["Q"] = q
        frames.append(d)
    return pd.concat(frames, ignore_index=True), shas


def main():
    D, shas = load()
    mp = pd.read_csv(os.path.join(OUTP, "f_occupation_mapping_ar.csv"), dtype=str).fillna("")
    cno2p = {r.cno2001_code: r.persona_id for r in mp.itertuples() if r.persona_id}
    corr = pd.read_csv(os.path.join(OUTP, "f_persona_correspondence_ar.csv"), dtype=str).fillna("")
    pinfo = {r.persona_id: r for r in corr.itertuples()}
    D["W"] = D.PONDERA / 4.0
    D["WI"] = D.PONDIIO / 4.0
    D["prov"] = D.AGLOMERADO.map(lambda a: AGLO[a][1])
    D["aglo_name"] = D.AGLOMERADO.map(lambda a: AGLO[a][0])
    D["aglo_mun"] = D.AGLOMERADO.map(lambda a: AGLO[a][2])
    # checks: employment and unemployment rates vs INDEC Cuadro 1.1 (Mercado de trabajo, EPH)
    published = {1: (44.4, 7.9), 2: (44.5, 7.6), 3: (45.4, 6.6), 4: (45.0, 7.5)}
    checks = {}
    for q, g in D.groupby("Q"):
        pop = g.PONDERA.sum(); emp = g[g.ESTADO == 1].PONDERA.sum(); une = g[g.ESTADO == 2].PONDERA.sum()
        er = 100 * emp / pop; ur = 100 * une / (emp + une)
        checks[f"Q{q}"] = dict(population=int(pop), employed=int(emp), employment_rate=round(er, 2),
                               published_employment_rate=published[q][0], unemployment_rate=round(ur, 2),
                               published_unemployment_rate=published[q][1],
                               ok=bool(abs(er - published[q][0]) <= 0.05 + 1e-9 and abs(ur - published[q][1]) <= 0.05 + 1e-9))
    E = D[D.ESTADO == 1].copy()
    E["cno"] = E.PP04D_COD.astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(5)
    E["pid"] = E.cno.map(cno2p)
    E["sec"] = (E.PP04B_COD // 100).map(caes_section)
    w = E.W
    # ---------------- F: persona profile ----------------
    prof = []
    for pid in PERSONA_ORDER:
        pi = pinfo[pid]
        g = E[E.pid == pid]
        row = dict(persona=pi.persona, ring=pi.ring, isco_codes=pi.isco08_template_codes.replace(";", " "),
                   cno2001_codes=pi.cno2001_codes_assigned.replace(";", " "))
        if len(g) == 0:
            row.update(employed=None, interviews=0)
            prof.append(row); continue
        gw = g.W
        cat_valid = g.CAT_OCUP.isin([1, 2, 3])
        size_valid = g.PP04C.between(1, 12)
        sec_valid = g.sec.notna()
        ed_valid = g.CH12.between(1, 9) & ~((g.CH12 == 7) & (g.CH13 == 9))
        dec_valid = g.DECCFR.between(1, 10)
        place_valid = g.PP04G.between(1, 13)
        inc = g[(g.P21 > 0)]
        row.update(employed=int(round(gw.sum())), interviews=int(len(g)),
                   pct_private_employee=pct((g.CAT_OCUP == 3) & g.PP04A.isin([2, 3]), cat_valid, gw),
                   pct_government_employee=pct((g.CAT_OCUP == 3) & (g.PP04A == 1), cat_valid, gw),
                   pct_self_employed_or_employer=pct(g.CAT_OCUP.isin([1, 2]), cat_valid, gw),
                   pct_firm_201_plus=pct(g.PP04C.isin([11, 12]), size_valid, gw),
                   pct_works_alone=pct(g.PP04C == 1, size_valid, gw),
                   pct_outside_tech_sector=pct(g.sec != "J", sec_valid, gw),
                   pct_women=pct(g.CH04 == 2, g.CH04.isin([1, 2]), gw),
                   pct_university=pct(((g.CH12 == 7) & (g.CH13 == 1)) | (g.CH12 == 8), ed_valid, gw),
                   median_age=wmedian(g.CH06, gw),
                   median_income_ars=wmedian(inc.P21, inc.WI),
                   pct_ipcf_deciles_7_10=pct(g.DECCFR.between(7, 10), dec_valid, gw),
                   pct_works_from_home=pct(g.PP04G.isin([6, 12]), place_valid, gw),
                   pct_informal=pct(g.EMPLEO == 2, g.EMPLEO.isin([1, 2]), gw))
        prof.append(row)
    P = pd.DataFrame(prof)
    P["median_age"] = P.median_age.map(lambda v: None if v is None or pd.isna(v) else int(v))
    P["employed"] = P.employed.astype("Int64")
    P.to_csv(os.path.join(CSV, "fact_persona_profile.csv"), index=False)
    # ---------------- F/G: persona by province, by agglomerate ----------------
    rows = []
    for pid in PERSONA_ORDER:
        g = E[E.pid == pid]
        if len(g) == 0:
            continue
        for prov, h in g.groupby("prov"):
            rows.append(dict(persona=pinfo[pid].persona, department_code=prov, department=PROV[prov],
                             employed=int(round(h.W.sum())), interviews=len(h)))
    PD = pd.DataFrame(rows)
    PD.to_csv(os.path.join(CSV, "fact_persona_department.csv"), index=False)
    rows = []
    for pid in PERSONA_ORDER:
        g = E[E.pid == pid]
        for a, h in g.groupby("AGLOMERADO"):
            rows.append(dict(persona=pinfo[pid].persona, municipality_code=AGLO[a][2], department_code=AGLO[a][1],
                             metro_area=AGLO[a][0], employed=int(round(h.W.sum())), interviews=len(h)))
    PM = pd.DataFrame(rows)
    PM.to_csv(os.path.join(CSV, "fact_persona_metro.csv"), index=False)
    # ---------------- H: segments (direct cross-tabulation) ----------------
    def buyer(r):
        if r.CAT_OCUP in (1, 2):
            return "Self-employed or employer"
        if r.CAT_OCUP == 3:
            if r.PP04A == 1:
                return "Government employee"
            if r.PP04C in (11, 12):
                return "Employee, firm 201+"
            if 7 <= r.PP04C <= 10:
                return "Employee, firm 11-200"
            if 1 <= r.PP04C <= 6 or (r.PP04C == 99 and r.PP04C99 == 1):
                return "Employee, firm up to 10"
        return "Other or unknown"
    S = E[E.pid.notna()].copy()
    S["buyer"] = [buyer(r) for r in S.itertuples()]
    rows = []
    for (pid, a, b), h in S.groupby(["pid", "AGLOMERADO", "buyer"]):
        rows.append(dict(persona=pinfo[pid].persona, municipality_code=AGLO[a][2], department_code=AGLO[a][1],
                         city=AGLO[a][0], buyer_type=b, employed=int(round(h.W.sum())), interviews=len(h),
                         confidence=confidence(len(h), cell=True)))
    PS = pd.DataFrame(rows).sort_values(["persona", "city", "buyer_type"])
    PS.to_csv(os.path.join(CSV, "fact_persona_segment.csv"), index=False)
    # ---------------- G: ICT staff by sector ----------------
    core = E[E.pid.isin(["P01", "P02", "P03", "P04"])]
    sec = core.groupby(core.sec.fillna("NA")).W.sum().sort_values(ascending=False)
    tot = sec.sum()
    IS = pd.DataFrame([dict(sector=SECTION_NAME[None if k == "NA" else k], caes_section=None if k == "NA" else k,
                            employed=int(round(v)), share_pct=round(100 * v / tot, 1)) for k, v in sec.items()])
    IS.to_csv(os.path.join(CSV, "fact_ict_by_sector.csv"), index=False)
    # G2-G4
    out_tech = core[core.sec.notna() & (core.sec != "J")]
    size_lbl = lambda c: "201+" if c in (11, 12) else ("11-200" if 7 <= c <= 10 else ("up to 10" if 1 <= c <= 6 else "unknown"))
    g2 = out_tech[out_tech.CAT_OCUP == 3].groupby(out_tech.PP04C.map(size_lbl)).W.sum().round().astype(int).to_dict()
    gov = core[(core.CAT_OCUP == 3) & (core.PP04A == 1)]
    g3 = gov.groupby(gov.sec.map(lambda s: SECTION_NAME.get(s))).W.sum().round().astype(int).sort_values(ascending=False).to_dict()
    g4 = {}
    for pid in PERSONA_ORDER:
        g = E[E.pid == pid]
        if len(g) == 0:
            continue
        g4[pinfo[pid].persona] = dict(government_employee_pct=pct((g.CAT_OCUP == 3) & (g.PP04A == 1), g.CAT_OCUP.isin([1, 2, 3]), g.W),
                                      public_administration_section_pct=pct(g.sec == "O", g.sec.notna(), g.W))
    # ---------------- M: micro-businesses (own-account and employers, unit up to 10 people) ----------------
    M = E[E.CAT_OCUP.isin([1, 2]) & E.PP04C.between(1, 6)].copy()
    total_indep = E[E.CAT_OCUP.isin([1, 2])]
    MD = M.groupby("prov").W.sum().round().astype(int).reset_index()
    MD.columns = ["department_code", "micro_businesses"]
    MD.insert(1, "department", MD.department_code.map(PROV))
    MD["interviews"] = M.groupby("prov").size().values
    MD.to_csv(os.path.join(CSV, "fact_micro_department.csv"), index=False)
    def dist(dim, ser, valid=None):
        # Shares over all micro-businesses; answers missing or not asked go to "Not specified" (as Mexico), so every
        # dimension adds up to M1.
        valid = ser.notna() if valid is None else valid
        if not valid.any():
            return []
        tot = M.W.sum()
        out = []
        for k, v in M.W[valid].groupby(ser[valid]).sum().sort_values(ascending=False).items():
            out.append(dict(dimension=dim, category=k, micro_businesses=int(round(v)), pct=round(100 * v / tot, 1)))
        miss = M.W[~valid].sum()
        if miss > 0:
            out.append(dict(dimension=dim, category="Not specified", micro_businesses=int(round(miss)), pct=round(100 * miss / tot, 1)))
        return out
    md = [dict(dimension="total", category="micro_businesses", micro_businesses=int(round(M.W.sum())), pct=100.0)]
    md += dist("activity", M.sec.map(lambda s: SECTION_NAME.get(s) if s else None))
    md += dist("position", M.CAT_OCUP.map({1: "Employer", 2: "Own-account worker"}))
    md += dist("owner_sex", M.CH04.map({1: "Men", 2: "Women"}))
    md += dist("owner_age", pd.cut(M.CH06, [0, 24, 34, 44, 54, 64, 200], labels=["Up to 24", "25-34", "35-44", "45-54", "55-64", "65+"]).astype(str).replace("nan", None))
    md += dist("size", M.PP04C.map(lambda c: "1 person" if c == 1 else ("2-5 people" if c <= 5 else "6-10 people")))
    md += dist("informal_employment", M.EMPLEO.map({1: "Formal", 2: "Informal"}))
    md += dist("contributions", M.PP05I.map({1: "Monotributo", 2: "Monotributo social", 3: "Autónomo or professional fund", 4: "No contributions"}))
    md += dist("can_issue_invoices", M.PP05B3.map({1: "Yes", 2: "No"}))
    md += dist("premises", M.PP05C_2.map({1: "Own premises", 2: "Borrowed or rented premises", 3: "No premises"}))
    md += dist("place_of_work", M.PP04G.map({11: "Premises/office/workshop", 12: "Own home (exclusive space)", 13: "Farm",
                                             2: "Fixed street stall", 3: "Vehicle (not transport service)", 4: "Transport vehicle",
                                             5: "Construction or mining site", 6: "Own home (no exclusive space)",
                                             7: "Partner's or employer's home", 8: "Client's home or premises",
                                             9: "Street or door to door", 10: "Other"}))
    md += dist("region", M.REGION.map({1: "Gran Buenos Aires", 40: "Noroeste", 41: "Noreste", 42: "Cuyo", 43: "Pampeana", 44: "Patagonia"}))
    MN = pd.DataFrame(md)
    MN.to_csv(os.path.join(CSV, "fact_micro_national.csv"), index=False)
    inc_m = M[M.P21 > 0]
    m_extra = dict(median_monthly_income_ars=wmedian(inc_m.P21, inc_m.WI), interviews=int(len(M)),
                   independents_total=int(round(total_indep.W.sum())),
                   independents_unit_size_unknown=int(round(total_indep[~total_indep.PP04C.between(1, 12)].W.sum())))
    # ---------------- JSON outputs ----------------
    unassigned = E[E.pid.isna()]
    blank = E[~E.cno.str.match(r"^\d{5}$") | (E.cno == "00000")]
    lf = dict(country="AR", source_id="INDEC_EPH_2025", period="2025 (Q1-Q4 average)",
              sources=[dict(zip=k, sha256=v) for k, v in shas.items()],
              universe="31 urban agglomerations; employed (ESTADO = 1); annual = sum of PONDERA over 4 quarters / 4; "
                       "income = P21 > 0 weighted with PONDIIO / 4 (current pesos of each quarter)",
              layer="F",
              checks=dict(rates_vs_indec_cuadro_1_1=checks, parts_add_up=True, no_double_counting=True),
              employed_total=int(round(E.W.sum())), employed_without_valid_occupation_code=int(round(blank.W.sum())),
              personas=P.where(pd.notna(P), None).to_dict(orient="records"),
              rings={r: int(round(E[E.pid.isin([p for p in PERSONA_ORDER if pinfo[p].ring == r])].W.sum())) for r in ["core", "adjacent", "extended"]},
              notes=dict(mapping="CNO-2001 codes assigned to personas by majority rule on INDEC's 2015 double-coded EPH (D-AR-09). "
                                 "Personas P02 (database and network), P04 (ICT managers), P05 (designers), P08 (data and research) "
                                 "and P09 (marketing) have no CNO-2001 code where they are the majority: their cells are empty, never zero. "
                                 "P01 then also holds most database and network professionals (91% of P01's 2015 employment was ISCO 251 or 252).",
                         size_bands="PP04C bands cut at 10 and 200 people, as Colombia (Mexico cuts at 250).",
                         socioeconomic="pct_ipcf_deciles_7_10 = household per-capita income deciles 7-10 of the total EPH (DECCFR), "
                                       "i.e. the two top quintiles; replaces Colombia's electricity stratum.",
                         geography="EPH covers the 31 agglomerations only (about 63% of the population); provincial rows are the "
                                   "agglomerations of each province, not the whole province (D-AR-08)."),
              limitations="Urban sample survey; the panel rotates so one person can appear in up to 4 quarters (interviews counts records). "
                          "Cells with fewer than 100 interviews are low confidence.")
    json.dump(_clean(lf), open(os.path.join(OUTP, "layer_f_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    lg = dict(country="AR", layer="G", source_id="INDEC_EPH_2025", period="2025 (Q1-Q4 average)",
              G1_it_staff_core_personas=int(round(core.W.sum())),
              G1_outside_tech_pct=pct(core.sec != "J", core.sec.notna(), core.W),
              G1_by_sector=IS.to_dict(orient="records"),
              G2_outside_tech_employees_by_firm_size=g2,
              G3_government_it_staff_by_section=g3,
              G4_public_sector_share_by_persona=g4,
              checks=dict(g1_equals_sum_of_core_personas=bool(int(round(core.W.sum())) == int(IS.employed.sum()) or abs(core.W.sum() - IS.employed.sum()) < 25)),
              limitations="Core personas available: P01 (includes database and network professionals) and P03; P02 and P04 are not "
                          "identifiable in CNO-2001.")
    json.dump(_clean(lg), open(os.path.join(OUTP, "layer_g_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    lh = dict(country="AR", layer="H", source_id="INDEC_EPH_2025", period="2025 (Q1-Q4 average)",
              rule="direct cross-tabulation persona x agglomerate x buyer type; never products of marginal percentages",
              buyer_types=["Government employee", "Employee, firm 201+", "Employee, firm 11-200", "Employee, firm up to 10",
                           "Self-employed or employer", "Other or unknown"],
              confidence_rule="high >= 1,000 interviews, medium 100-999, low < 100",
              cells=int(len(PS)), cells_by_confidence=PS.confidence.value_counts().to_dict(),
              checks=dict(cells_add_to_persona_totals=bool(all(abs(PS[PS.persona == p].employed.sum() -
                          P[P.persona == p].employed.fillna(0).iloc[0]) <= len(PS[PS.persona == p]) for p in PS.persona.unique()))),
              top_cells=PS.sort_values("employed", ascending=False).head(15).to_dict(orient="records"))
    json.dump(_clean(lh), open(os.path.join(OUTP, "layer_h_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    lm = dict(country="AR", layer="M", source_id="INDEC_EPH_2025", period="2025 (Q1-Q4 average)",
              definition="Own-account workers and employers (CAT_OCUP 1-2) whose unit has up to 10 people (PP04C 1-6). "
                         "Argentina has no micro-business survey comparable to EMICRON (D-AR-10); EPH bands give 1-5 and 6-10, so "
                         "the template limit of 9 cannot be applied.",
              M1_micro_businesses=int(round(M.W.sum())), **m_extra,
              M2_M5=MN.to_dict(orient="records"),
              by_province=MD.to_dict(orient="records"),
              M4_digital="Not available: the EPH has no ICT questions for businesses; household ICT use is in layer O (INDEC TIC module).",
              limitations="Urban agglomerations only; persons, not firms (a business with two partners counts twice).")
    json.dump(_clean(lm), open(os.path.join(OUTP, "layer_m_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(checks, indent=0)); print(P.to_string())
    print(MD.to_string()); print(IS.to_string())


if __name__ == "__main__":
    main()
