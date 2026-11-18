#!/usr/bin/env python3
"""Layers D, N and J for Argentina from CEP XXI 'Distribución geográfica de los establecimientos productivos' (2022 rows).

Universe: private employers and majority state-owned companies registered in SIPA (AFIP form 931), establishments with
registered employees; own-account workers without employees and public administration employers are outside (D-AR-06).
Firm = anonymised CUIT; establishment = CUIT x branch. Size band = registered employees of the establishment.
Usage: build-argentina-d-n-j-companies.py <raw_dir> <research-argentina_dir>
"""
import sys, os, json, hashlib
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
F = os.path.join(RAW, "cep_xxi", "ar_raw_cep_distribucion_establecimientos_productivos_sexo.csv")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()

IT = [620100, 620200, 620300, 620900, 631110, 631120, 631190, 631200]   # ISIC 6201, 6202, 6209, 6311, 6312
SOFTWARE = [620100]                                                      # ISIC 6201 (CLAE 620100)
SHOPS = [471110, 471120, 471130, 471190]                                 # ISIC 4711 (CLAE 4711xx)
DESIGN = [741000]
ACCOUNTING = [692000]
CONSULTING = [702010, 702091, 702092, 702099]
RESEARCH = [721010, 721020, 721030, 721090, 722010, 722020, 732000]
HIGHER_TRAINING = [853100, 853200, 853300, 854910, 854920, 854930, 854990]
SCHOOLS = [851010, 851020, 852100, 852200]
GBA24 = ["Almirante Brown", "Avellaneda", "Berazategui", "Esteban Echeverría", "Ezeiza", "Florencio Varela",
         "General San Martín", "Hurlingham", "Ituzaingó", "José C. Paz", "La Matanza", "Lanús", "Lomas de Zamora",
         "Malvinas Argentinas", "Merlo", "Moreno", "Morón", "Quilmes", "San Fernando", "San Isidro", "San Miguel", "Tigre",
         "Tres de Febrero", "Vicente López"]   # INDEC, ¿Qué es el Gran Buenos Aires? (2003)


def main():
    d = pd.read_csv(F, low_memory=False)
    d = d[d.anio == 2022].copy()
    d["mun"] = d.in_departamentos.map(lambda v: f"{int(v):05d}")
    # CEP XXI uses three earlier INDEC codes; same departments under their current Georef/Censo 2022 codes (D-AR-06)
    LEGACY = {"06217": "06218", "94007": "94008", "94014": "94015"}
    d["mun"] = d.mun.replace(LEGACY)
    d["prov"] = d.provincia_id.map(lambda v: f"{int(v):02d}")
    d["micro"] = d.empleo.eq("a. 1-9"); d["ml"] = d.empleo.isin(["c. 50-199", "d. 200-499", "e. 500+"])
    for name, codes in [("it", IT), ("sw", SOFTWARE), ("shop", SHOPS), ("design", DESIGN), ("acc", ACCOUNTING),
                        ("cons", CONSULTING), ("res", RESEARCH), ("hed", HIGHER_TRAINING), ("sch", SCHOOLS)]:
        d[name] = d.clae6.isin(codes)
    gm = pd.read_csv(os.path.join(CSV, "geo_municipality.csv"), dtype=str)
    gd = pd.read_csv(os.path.join(CSV, "geo_department.csv"), dtype=str)
    k = pd.read_csv(os.path.join(CSV, "fact_schools_department.csv"), dtype={"department_code": str})
    def agg(g):
        return pd.Series(dict(establishments=len(g), businesses=g.cuit.nunique(), micro_1_9=int(g.micro.sum()),
                              medium_large_50_plus=int(g.ml.sum()), shops_4711=int(g.shop.sum()),
                              it_establishments=int(g.it.sum()), it_firms=g[g.it].cuit.nunique(),
                              software_620100=int(g.sw.sum()),
                              it_620200_620300_620900=int(g.clae6.isin([620200, 620300, 620900]).sum()),
                              it_631110_631120_631190_631200=int(g.clae6.isin([631110, 631120, 631190, 631200]).sum()),
                              employment_band_known=len(g)))
    # department (municipality) level, one row per Georef department (0 = none registered)
    md = d.groupby("mun").apply(agg, include_groups=False).reset_index().rename(columns={"mun": "municipality_code"})
    md = gm[["municipality_code", "department_code"]].merge(md, on="municipality_code", how="left").fillna(0)
    for c in md.columns[2:]:
        md[c] = md[c].astype(int)
    md = md.drop(columns=["employment_band_known"])
    md.to_csv(os.path.join(CSV, "fact_companies_municipality.csv"), index=False)
    not_in_georef = sorted(set(d.mun) - set(gm.municipality_code))
    # province level
    pdp = d.groupby("prov").apply(agg, include_groups=False).reset_index().rename(columns={"prov": "department_code"})
    pdp = gd.merge(pdp, on="department_code", how="left").rename(columns={"name": "department"})
    pdp = pdp.drop(columns=["employment_band_known"])
    pdp = pdp.merge(k[["department_code", "schools"]], on="department_code", how="left")
    pdp["businesses_per_school"] = (pdp.businesses / pdp.schools).round(1)
    pdp = pdp.drop(columns=["schools"])
    pdp.to_csv(os.path.join(CSV, "fact_companies_department.csv"), index=False)
    # zones (J): CABA comunas + 24 GBA partidos
    shapes = pd.read_csv(os.path.join(CSV, "geo_municipality_shape.csv"), dtype=str)
    caba = gm[gm.department_code == "02"]
    gba = gm[(gm.department_code == "06") & gm.name.isin(GBA24)]
    assert len(caba) == 15 and len(gba) == 24, (len(caba), len(gba), sorted(set(GBA24) - set(gba.name)))
    zones = pd.concat([caba.assign(zone_type="comuna", prefix="CABA"), gba.assign(zone_type="partido_gba", prefix="GBA")])
    zones["zone_id"] = zones.prefix + "-" + zones.municipality_code.str[2:]
    zones["zone_code"] = zones.municipality_code.str[2:]
    zones = zones.merge(shapes[["municipality_code", "geojson"]], on="municipality_code")
    gz = zones[["zone_id", "municipality_code", "zone_type", "zone_code", "name", "lat", "lon", "geojson", "wkt"]]
    gz.to_csv(os.path.join(CSV, "geo_zone.csv"), index=False)
    rows = []
    for z in zones.itertuples():
        g = d[d.mun == z.municipality_code]
        rows.append(dict(zone_id=z.zone_id, zone_name=z.name, companies_total=len(g), businesses=g.cuit.nunique(),
                         micro=int(g.micro.sum()), medium_large=int(g.ml.sum()), software_it=int(g.it.sum()),
                         design=int(g.design.sum()), accounting_audit=int(g.acc.sum()), management_consulting=int(g.cons.sum()),
                         research_market_studies=int(g.res.sum()), higher_education_training=int(g.hed.sum()),
                         shops_4711=int(g.shop.sum()), private_schools=int(g.sch.sum())))
    fz = pd.DataFrame(rows)
    fz.to_csv(os.path.join(CSV, "fact_companies_zone.csv"), index=False)
    # JSON layers
    tot = dict(establishments=int(len(d)), businesses=int(d.cuit.nunique()), it_establishments=int(d.it.sum()),
               it_firms=int(d[d.it].cuit.nunique()), software_establishments=int(d.sw.sum()), software_firms=int(d[d.sw].cuit.nunique()),
               shops=int(d.shop.sum()), micro_pct=round(100 * d.micro.mean(), 1))
    it_by_prov = pdp[["department_code", "department", "it_establishments"]].copy()
    it_by_prov["share_pct"] = (100 * it_by_prov.it_establishments / it_by_prov.it_establishments.sum()).round(1)
    it_by_prov = it_by_prov.sort_values("it_establishments", ascending=False)
    ld = dict(country="AR", layer="D", source_id="CEP_XXI_ESTABLECIMIENTOS_2022", period="2022 (SIPA, average of the year)",
              D1=dict(it_establishments=tot["it_establishments"], it_firms=tot["it_firms"], software_establishments=tot["software_establishments"],
                      software_firms=tot["software_firms"], codes_it="CLAE6 620100, 620200, 620300, 620900, 631110, 631120, 631190, 631200",
                      code_software="CLAE6 620100 (Servicios de consultores en informática y suministros de programas de informática)"),
              D2=it_by_prov.to_dict(orient="records"),
              D2_size=d[d.it].empleo.value_counts().to_dict(),
              D3=dict(source_id="CESSI_OPSSI_2026Q1_PRESS", registered_employment_software_it_services=162391, period="2026 Q1",
                      exports_usd_millions_last_12_months=2848, exports_usd_millions_2026q1=744, firms=None,
                      note="Observatorio Permanente de la Industria del Software y Servicios Informáticos (OPSSI, CESSI), Informe de la "
                           "Industria del Software, as quoted by Ámbito (29-07-2026). The press note gives no number of firms; to confirm "
                           "with the OPSSI report. Not added to, nor compared as growth with, CEP XXI 2022."), checks=dict(provinces_add_to_total=bool(int(pdp.establishments.sum()) == tot["establishments"]),
                                   departments_add_to_total=bool(int(md.establishments.sum()) == tot["establishments"] - int(d.mun.isin(not_in_georef).sum())),
                                   department_codes_not_in_georef=not_in_georef, legacy_codes_recoded=LEGACY),
              file_sha256=sha(F),
              limitations="Employer establishments registered in SIPA only: firms without registered employees (most own-account "
                          "developers) are outside. CLAE 620100 joins software development and IT consulting, so 'of them software' "
                          "is an upper bound. CEP XXI calls the base exploratory and provisional.")
    json.dump(_clean(ld), open(os.path.join(OUTP, "layer_d_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    ln = dict(country="AR", layer="N", source_id="CEP_XXI_ESTABLECIMIENTOS_2022", period="2022",
              N1_formal_businesses=tot["businesses"], N1_establishments=tot["establishments"],
              N1_definition="Distinct anonymised CUIT with at least one establishment with registered employees in 2022 (private and "
                            "majority state-owned companies; public administration excluded by the source).",
              N2=None, N2_note="Legal form is not published (CUIT anonymised).",
              N3_shops_4711=tot["shops"], N4_by_province=pdp.to_dict(orient="records"),
              N4_businesses_per_school_national=round(tot["businesses"] / int(k.schools.sum()), 1),
              checks=dict(capital_vs_zones=dict(caba_establishments=int(pdp[pdp.department_code == "02"].establishments.iloc[0]),
                                                caba_comunas_sum=int(fz[fz.zone_id.str.startswith("CABA")].companies_total.sum()))),
              limitations="Registered employers only; Colombia's N1 (RUES renewed merchants) and Mexico's (DENUE) include businesses "
                          "without employees, so Argentina's N1 is smaller by construction.")
    json.dump(_clean(ln), open(os.path.join(OUTP, "layer_n_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    lj = dict(country="AR", layer="J", source_id="CEP_XXI_ESTABLECIMIENTOS_2022; GEOREF_IGN_202312; INDEC_GBA_2003",
              zones="CABA by its 15 comunas (CABA-) and the 24 partidos of Gran Buenos Aires as defined by INDEC (GBA-) (D-AR-07)",
              groups=dict(software_it=IT, design=DESIGN, accounting_audit=ACCOUNTING, management_consulting=CONSULTING,
                          research_market_studies=RESEARCH, higher_education_training=HIGHER_TRAINING, shops_4711=SHOPS,
                          private_schools=SCHOOLS),
              size="micro = 1-9 registered employees; medium_large = 50 or more (CEP XXI bands)",
              zones_rows=fz.to_dict(orient="records"),
              checks=dict(caba_comunas_add_to_caba=bool(int(fz[fz.zone_id.str.startswith("CABA")].companies_total.sum()) ==
                                                        int(pdp[pdp.department_code == "02"].establishments.iloc[0]))),
              limitations="Zone = whole comuna or partido (no finer official zoning with open business data). Establishments with "
                          "registered employees only.")
    json.dump(_clean(lj), open(os.path.join(OUTP, "layer_j_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=int)
    print(tot); print(pdp[["department_code", "establishments", "businesses", "it_establishments", "shops_4711", "businesses_per_school"]].to_string())
    print(not_in_georef, ld["checks"], lj["checks"])


if __name__ == "__main__":
    main()
