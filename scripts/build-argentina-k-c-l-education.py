#!/usr/bin/env python3
"""Layers K (schools), C and L (higher education) for Argentina, by province (and department where published).

K: Relevamiento Anual (RA) 2025, base agregada de matrícula (Secretaría de Educación, datos.gob.ar, published 2026-09-10):
   enrolment by province x department x sector x ámbito and año corrido. Target grades = años corridos 9, 10, 11 and 12
   (last year of ISCED 2 and the three years of ISCED 3 in both the 6+6 and 7+5 provincial structures); 13th/14th year of
   technical schools (_1314) left out, as Mexico leaves out technical 4th/5th years (D-AR-04).
   Schools = localizaciones (Cueanexo) of the Padrón Oficial de Establecimientos Educativos (16-06-2026) with a common
   secondary offer (Secundario or Secundario - INET).
C/L: Censo 2022 (attendance by level, by province of residence); Anuario Estadístico Universitario 2024 (advance, DNPeIU,
   2026-08-14) for national and CPRES-region totals and the ICT discipline (Informática); RA 2025 for non-university
   tertiary (SNU) enrolment by province; Padrón for vocational training (Formación Profesional) centres.
Usage: build-argentina-k-c-l-education.py <raw_dir> <research-argentina_dir>
"""
import sys, os, json, glob, hashlib, unicodedata, re
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
CSV = os.path.join(OUT, "geodb", "csv"); OUTP = os.path.join(OUT, "outputs")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(departamento|partido|comuna)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


PROV_NAME = {"buenos aires": "06", "catamarca": "10", "chaco": "22", "chubut": "26", "ciudad de buenos aires": "02",
             "ciudad autonoma de buenos aires": "02", "cordoba": "14", "corrientes": "18", "entre rios": "30", "formosa": "34",
             "jujuy": "38", "la pampa": "42", "la rioja": "46", "mendoza": "50", "misiones": "54", "neuquen": "58",
             "rio negro": "62", "salta": "66", "san juan": "70", "san luis": "74", "santa cruz": "78", "santa fe": "82",
             "santiago del estero": "86", "tierra del fuego": "94", "tucuman": "90"}


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def main():
    gd = pd.read_csv(os.path.join(CSV, "geo_department.csv"), dtype=str)
    gm = pd.read_csv(os.path.join(CSV, "geo_municipality.csv"), dtype=str)
    pop = pd.read_csv(os.path.join(CSV, "fact_population_department.csv"), dtype={"department_code": str})
    E = os.path.join(RAW, "educ_ra")
    ra = pd.read_csv(os.path.join(E, "ar_raw_ra2025_agregada_matricula.csv"), sep=";", na_values=[" ", ""], low_memory=False, encoding="utf-8-sig")
    ra["prov"] = ra.provincia.map(lambda s: PROV_NAME[norm(s)])
    ra = ra.copy()
    for c in ["_9", "_10", "_11", "_12", "_1314", "_snu", "v_9", "v_10", "v_11", "v_12", "v_snu", "_7", "_8"]:
        ra[c] = num(ra[c])
    ra["target"] = ra[["_9", "_10", "_11", "_12"]].sum(axis=1)
    ra["target_men"] = ra[["v_9", "v_10", "v_11", "v_12"]].sum(axis=1)
    # department name -> code (within province)
    key = {(r.department_code, norm(r.name)): r.municipality_code for r in gm.itertuples()}
    alias = {("02", lambda n: n.isdigit()): None}
    ALIAS = {("06", "coronel de marina l rosales"): "06182", ("46", "general angel v penaloza"): "46056",
             ("46", "general juan f quiroga"): "46070", ("46", "general ocampo"): "46084", ("86", "juan f ibarra"): "86098",
             ("90", "juan b alberdi"): "90042"}  # abbreviations in the RA names, checked against Georef names
    def dcode(prov, name):
        n = norm(name)
        if (prov, n) in ALIAS:
            return ALIAS[(prov, n)]
        if prov == "02" and n.isdigit():
            return f"02{int(n) * 7:03d}"
        c = key.get((prov, n))
        if c:
            return c
        cands = [v for (p, k), v in key.items() if p == prov and (k.replace(" ", "") == n.replace(" ", ""))]
        if len(cands) == 1:
            return cands[0]
        # abbreviations in the RA names (GRL, DOCTOR, L ROSALES...): best fuzzy match within the province, ratio >= 0.85
        import difflib
        strip = lambda t: re.sub(r"\b(doctor|dr|general|gral|grl|coronel|cnel|libertador|de|del|la|los|marina|presidente|pte)\b", " ", t)
        n2 = re.sub(r"\s+", " ", strip(n)).strip()
        best, score = None, 0.0
        for (p, k), v in key.items():
            if p != prov:
                continue
            r = difflib.SequenceMatcher(None, n2, re.sub(r"\s+", " ", strip(k)).strip()).ratio()
            if r > score:
                best, score = v, r
        return best if score >= 0.85 and n != "enmascarado" else None
    ra["mun"] = [dcode(p, n) for p, n in zip(ra.prov, ra.departamento)]
    unmatched = ra[ra.mun.isna()][["provincia", "departamento"]].drop_duplicates()
    # age file: share under 18 in target grades
    age = pd.read_csv(os.path.join(E, "ar_raw_ra2025_agregada_matricula_edad.csv"), sep=";", na_values=[" ", ""], low_memory=False, encoding="utf-8-sig")
    age["prov"] = age.provincia.map(lambda s: PROV_NAME[norm(s)])
    age["g"] = age.grado.astype(str).str.replace("°", "", regex=False).str.strip()
    at = age[age.g.isin(["9", "10", "11", "12"])].copy()
    single = [c for c in at.columns if re.match(r"^\d+años?$", c)]
    for c in single + ["30añosymás"]:
        at[c] = num(at[c])
    # the aggregate columns of the file are empty; ages are summed from the single-year columns (0-29) and 30 and over
    at["Menosde18años"] = at[[c for c in single if int(re.match(r"^(\d+)", c).group(1)) < 18]].sum(axis=1)
    at["18añosymás"] = at[[c for c in single if int(re.match(r"^(\d+)", c).group(1)) >= 18]].sum(axis=1) + at["30añosymás"]
    # padrón
    pf = os.path.join(RAW, "educ_padron", "ar_raw_2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx")
    pdn = pd.read_excel(pf, header=None, skiprows=13, dtype=str)
    cols = ["jurisdiccion", "sector", "ambito", "departamento", "cod_departamento", "localidad", "cod_localidad", "cueanexo",
            "nombre", "domicilio", "cp", "telefono", "mail", "comun", "especial", "adultos", "com_maternal", "com_infantes",
            "com_primario", "com_secundario", "com_secundario_inet", "com_snu", "com_snu_inet", "com_snu_cursos",
            "esp_temprana", "esp_infantes", "esp_primario", "esp_secundario", "esp_integracion", "adu_primario",
            "adu_secundario", "adu_fp", "adu_fp_inet", "adu_alfabetizacion", "hosp_inicial", "hosp_primario", "hosp_secundario",
            "talleres_artistica", "servicios_complementarios", "validez_titulos"]
    pdn = pdn.iloc[:, :len(cols)]; pdn.columns = cols[:pdn.shape[1]]
    pdn = pdn[pdn.cueanexo.notna() & pdn.cod_departamento.notna()]
    pdn["prov"] = pdn.cod_departamento.str[:2]
    flag = lambda c: pdn[c].fillna("").astype(str).str.strip().isin(["1", "1.0"])
    pdn["sec"] = flag("com_secundario") | flag("com_secundario_inet")
    pdn["sec_inet"] = flag("com_secundario_inet")
    pdn["snu"] = flag("com_snu") | flag("com_snu_inet")
    pdn["fp"] = flag("adu_fp") | flag("adu_fp_inet")
    pdn["fp_inet"] = flag("adu_fp_inet")
    pdn["public"] = pdn.sector.str.strip().str.lower().eq("estatal")
    S = pdn[pdn.sec]
    # ---------------- K by province ----------------
    rows = []
    for prov in gd.department_code:
        r = ra[ra.prov == prov]; a = at[at.prov == prov]; s = S[S.prov == prov]
        t = r.target.sum()
        rows.append(dict(department_code=prov, department=gd.set_index("department_code").name[prov],
                         students_target=int(t), students_y9=int(r._9.sum()), students_y10=int(r._10.sum()),
                         students_y11=int(r._11.sum()), students_y12=int(r._12.sum()),
                         students_technical_y13_14=int(r._1314.sum()),
                         students_public=int(r[r.sector.str.lower().str.startswith("estatal")].target.sum()),
                         students_rural=int(r[r.ambito.str.lower().str.startswith("rural")].target.sum()),
                         students_women=int(t - r.target_men.sum()),
                         students_under_18=int(a["Menosde18años"].sum()),
                         schools=int(s.cueanexo.nunique()), schools_public=int(s[s.public].cueanexo.nunique()),
                         schools_technical_inet=int(s[s.sec_inet].cueanexo.nunique()),
                         mean_students_per_school=round(t / s.cueanexo.nunique(), 1) if len(s) else None))
    K = pd.DataFrame(rows)
    K.to_csv(os.path.join(CSV, "fact_schools_department.csv"), index=False)
    # ---------------- K by department (where the RA name matches a Georef department) ----------------
    km = ra[ra.mun.notna()].groupby("mun").agg(students_target=("target", "sum"), students_y9=("_9", "sum"),
                                                students_y10=("_10", "sum"), students_y11=("_11", "sum"), students_y12=("_12", "sum")).reset_index()
    pub = ra[ra.mun.notna() & ra.sector.str.lower().str.startswith("estatal")].groupby("mun").target.sum()
    rur = ra[ra.mun.notna() & ra.ambito.str.lower().str.startswith("rural")].groupby("mun").target.sum()
    km["students_public"] = km.mun.map(pub).fillna(0); km["students_rural"] = km.mun.map(rur).fillna(0)
    sc = S.groupby("cod_departamento").cueanexo.nunique(); scp = S[S.public].groupby("cod_departamento").cueanexo.nunique()
    allm = sorted(set(km.mun) | set(sc.index))
    KM = pd.DataFrame(dict(municipality_code=allm))
    KM["department_code"] = KM.municipality_code.str[:2]
    KM = KM.merge(km.rename(columns={"mun": "municipality_code"}), on="municipality_code", how="left")
    KM["schools"] = KM.municipality_code.map(sc).fillna(0).astype(int)
    KM["schools_public"] = KM.municipality_code.map(scp).fillna(0).astype(int)
    for c in ["students_target", "students_y9", "students_y10", "students_y11", "students_y12", "students_public", "students_rural"]:
        KM[c] = KM[c].astype("Int64")
    KM = KM[KM.municipality_code.isin(gm.municipality_code)]
    KM.to_csv(os.path.join(CSV, "fact_schools_municipality.csv"), index=False)
    # ---------------- C / L ----------------
    C = os.path.join(RAW, "indec_censo2022")
    cen = []
    for f in sorted(glob.glob(os.path.join(C, "ar_raw_c2022_*_educacion_c2_*.xlsx"))):
        x = pd.read_excel(f, sheet_name=None, header=None)
        sh = [k for k in x if re.match(r"^Cuadro 2\.\d+$", k.strip())][0]
        v = x[sh]
        title = str(v.iloc[1, 0]).replace("\xa0", " ")
        tot = v[v[0].astype(str).str.strip() == "Total"].iloc[0]
        prov_name = re.split(r"\.\s+", title)[1] if re.search(r"\.\s+", title) else title
        cen.append(dict(file=os.path.basename(f), title=prov_name, attending=int(tot[3]), tertiary_non_university=int(tot[8]),
                        university=int(tot[9]), postgraduate=int(tot[10])))
    CE = pd.DataFrame(cen)
    name2code = {norm(n): c for c, n in zip(gd.department_code, gd.name)}
    def cen_code(t):
        n = norm(t.replace("Provincia de ", "").replace("Provincia del ", ""))
        if "ciudad autonoma" in n:
            return "02"
        if n.startswith("tierra del fuego"):
            return "94"
        return name2code.get(n)
    CE["department_code"] = CE.title.map(cen_code)
    snu_p = ra.groupby("prov")._snu.sum(); snu_w = ra.groupby("prov").v_snu.sum()
    fp = pdn[pdn.fp].groupby("prov").cueanexo.nunique(); snu_s = pdn[pdn.snu].groupby("prov").cueanexo.nunique()
    H = gd.rename(columns={"name": "department"}).copy()
    H = H.merge(CE[["department_code", "university", "postgraduate", "tertiary_non_university"]], on="department_code", how="left")
    H = H.rename(columns={"university": "university_students_census2022", "postgraduate": "postgraduate_students_census2022",
                          "tertiary_non_university": "tertiary_non_university_students_census2022"})
    H["snu_students_ra2025"] = H.department_code.map(snu_p).fillna(0).astype(int)
    H["snu_institutions_padron"] = H.department_code.map(snu_s).fillna(0).astype(int)
    H["vocational_training_centres_padron"] = H.department_code.map(fp).fillna(0).astype(int)
    H = H.merge(pop[["department_code", "population"]], on="department_code")
    H["university_students_per_100k"] = (100000 * H.university_students_census2022 / H.population).round(1)
    H["higher_ed_students_per_100k"] = (100000 * (H.university_students_census2022 + H.tertiary_non_university_students_census2022) / H.population).round(1)
    H = H.drop(columns=["population"])
    H.to_csv(os.path.join(CSV, "fact_higher_ed_department.csv"), index=False)
    # Anuario 2024 national and CPRES regions
    A = os.path.join(RAW, "univ", "a24", "Z 1.1 Datos Generales 24.xlsx")
    c112 = pd.read_excel(A, sheet_name="C1.1.1-C1.1.2", header=None)
    c120 = pd.read_excel(A, sheet_name="C 1.1.20 ", header=None)
    c121 = pd.read_excel(A, sheet_name="C 1.1.21", header=None)
    c138 = pd.read_excel(A, sheet_name="C 1.1.38 a 41", header=None)
    c114 = pd.read_excel(A, sheet_name="C 1.1.14", header=None)
    def row(df, label, col0=1):
        m = df[df[col0].astype(str).str.strip() == label]
        return m.iloc[0]
    start = c112[c112[1].astype(str).str.startswith("Cuadro 1.1.2")].index[0]
    c112 = c112.loc[start:]
    tot = row(c112, "Total"); est = row(c112, "Estatal"); pri = row(c112, "Privado")
    inf = c120[c120[1].astype(str).str.strip() == "Informática"].iloc[0]
    tot_dist = row(c138, "A Distancia")
    wom = row(c114, "Total")
    regions = []
    cur = None
    for r in c121.itertuples(index=False):
        lab = str(r[1]).strip()
        if lab in ("Bonaerense", "Centro", "Metropolitana", "Noreste", "Noroeste", "Nuevo Cuyo", "Sur"):
            regions.append(dict(region_cpres=lab, students=int(r[2]), new_entrants=int(r[3]), graduates=int(r[5]),
                                applied_sciences_students=int(r[6])))
    ict_students = int(inf[2]) + int(inf[6]); ict_new = int(inf[3]) + int(inf[7]); ict_grad = int(inf[5]) + int(inf[9])
    nat = dict(students_undergraduate=int(tot[2]), new_entrants=int(tot[3]), graduates=int(tot[5]),
               students_public=int(est[2]), students_private=int(pri[2]), students_postgraduate=int(tot[8]),
               students_distance=int(tot_dist[12]), pct_distance=round(100 * int(tot_dist[12]) / int(tot[2]), 1),
               pct_public=round(100 * int(est[2]) / int(tot[2]), 1), pct_women=round(float(wom[4]), 1),
               ict_discipline_informatica_students=ict_students, ict_discipline_informatica_new_entrants=ict_new,
               ict_discipline_informatica_graduates=ict_grad,
               ict_share_pct=round(100 * ict_students / int(tot[2]), 1))
    snu_total = int(ra._snu.sum())
    lc = dict(country="AR", layer="C", source_id="SPU_ANUARIO_2024; INDEC_CENSO_2022",
              period="2024 (university year); 2022 (census)",
              C1_ict_students=dict(value=ict_students, definition="Discipline 'Informática' (rama Ciencias Aplicadas), pregrado y grado, "
                                   "state and private universities, 2024 (Anuario Cuadro 1.1.20)", share_of_undergraduate_pct=nat["ict_share_pct"]),
              C2_students_by_province=dict(source="Censo 2022, population attending university (de grado) by province of residence",
                                           rows=H[["department_code", "department", "university_students_census2022",
                                                   "university_students_per_100k"]].to_dict(orient="records")),
              C3_concentration=None, C4=dict(pct_public=nat["pct_public"], pct_women=nat["pct_women"], pct_distance=nat["pct_distance"]),
              by_cpres_region_2024=regions,
              limitations="The SPU publishes university statistics by institution and by CPRES region, not by province or city of the "
                          "programme (D-AR-05). Provincial counts come from the 2022 census and refer to the province where students live, "
                          "all modalities. ICT students are available nationally (discipline Informática), not by province.")
    srt = H.sort_values("university_students_census2022", ascending=False)
    cum = (srt.university_students_census2022.cumsum() / srt.university_students_census2022.sum())
    lc["C3_concentration"] = {f"provinces_to_{int(p*100)}pct": int((cum < p).sum() + 1) for p in (0.5, 0.75, 0.9)}
    json.dump(_clean(lc), open(os.path.join(OUTP, "layer_c_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ll = dict(country="AR", layer="L", source_id="SPU_ANUARIO_2024; MEN_RA_2025; INDEC_CENSO_2022; MEN_PADRON_2026",
              L1=dict(university_students_2024=nat["students_undergraduate"], postgraduate_students_2024=nat["students_postgraduate"],
                      institutions_2024=142, snu_students_2025=snu_total),
              L2=dict(pct_public=nat["pct_public"], pct_distance=nat["pct_distance"],
                      university_vs_non_university_pct=round(100 * nat["students_undergraduate"] / (nat["students_undergraduate"] + snu_total), 1)),
              L3=dict(ict_students=ict_students, ict_share_pct=nat["ict_share_pct"]),
              L4=dict(university_new_entrants_2024=nat["new_entrants"], ict_new_entrants_2024=ict_new),
              L5=dict(vocational_training_centres=int(pdn[pdn.fp].cueanexo.nunique()),
                      of_them_inet=int(pdn[pdn.fp_inet].cueanexo.nunique()),
                      enrolment=None, note="Vocational training (Formación Profesional, INET) enrolment is not in the RA open bases; "
                                           "only centres are counted, from the Padrón (D-AR-05)."),
              L6=dict(by_province=H.to_dict(orient="records")),
              L7=dict(last_school_year_y12_2025=int(ra._12.sum()), university_new_entrants_2024=nat["new_entrants"],
                      technical_y13_14_2025=int(ra._1314.sum())),
              national=nat, regions_cpres=regions,
              checks=dict(snu_women_share_pct=round(100 * (1 - ra.v_snu.sum() / snu_total), 1)),
              limitations="University data are from the SPU Anuario 2024 (advance, published 2026-08-14). Province figures are census "
                          "attendance by residence (2022).")
    json.dump(_clean(ll), open(os.path.join(OUTP, "layer_l_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # K JSON
    tt = K.students_target.sum()
    sizes = None
    lk = dict(country="AR", layer="K", source_id="MEN_RA_2025; MEN_PADRON_2026", period="2025 school year (RA 2025); register 16-06-2026",
              target_grades="años corridos 9-12 (last year of ISCED 2 + ISCED 3); technical 13th-14th year excluded",
              K1=dict(schools=int(S.cueanexo.nunique()), schools_public=int(S[S.public].cueanexo.nunique()),
                      note="localizaciones (Cueanexo) with a common secondary offer; not every one teaches all four target years"),
              K2=dict(y9=int(K.students_y9.sum()), y10=int(K.students_y10.sum()), y11=int(K.students_y11.sum()), y12=int(K.students_y12.sum()), total=int(tt)),
              K3=dict(students_public_pct=round(100 * K.students_public.sum() / tt, 1),
                      schools_public_pct=round(100 * S.public.mean(), 1)),
              K4=dict(under_18_pct=round(100 * K.students_under_18.sum() / at[["Menosde18años", "18añosymás"]].sum().sum(), 1),
                      women_pct=round(100 * K.students_women.sum() / tt, 1), rural_pct=round(100 * K.students_rural.sum() / tt, 1),
                      technical_schools_inet=int(S[S.sec_inet].cueanexo.nunique()), technical_y13_14_students=int(K.students_technical_y13_14.sum())),
              K5=dict(mean_students_per_school=round(tt / S.cueanexo.nunique(), 1), median=None,
                      note="Since 2024 the RA open bases are published aggregated by department (no school-level records), so the "
                           "size distribution and the median per school cannot be computed (D-AR-04)."),
              K6=dict(reach_cap100=None, note="Needs school-level enrolment; not available in the open data."),
              K7=K.to_dict(orient="records"),
              unmatched_ra_departments=unmatched.to_dict(orient="records"),
              checks=dict(grades_add_to_total=bool(int(K[["students_y9", "students_y10", "students_y11", "students_y12"]].sum().sum()) == int(tt)),
                          provinces_add_to_total=bool(int(K.students_target.sum()) == int(ra.target.sum())),
                          department_rows_cover_pct=round(100 * ra[ra.mun.notna()].target.sum() / ra.target.sum(), 2)),
              files=dict(ra_matricula=sha(os.path.join(E, "ar_raw_ra2025_agregada_matricula.csv")),
                         ra_edad=sha(os.path.join(E, "ar_raw_ra2025_agregada_matricula_edad.csv")), padron=sha(pf)))
    json.dump(_clean(lk), open(os.path.join(OUTP, "layer_k_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    print(K.to_string()); print(H.to_string()); print(json.dumps(nat)); print(unmatched.to_string()); print(lk["checks"], lc["C3_concentration"])


if __name__ == "__main__":
    main()
