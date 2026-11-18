#!/usr/bin/env python3
"""Layers Q (geography keys and shapes) and E (population) for Argentina.

Q: Georef (Servicio de normalización de datos geográficos, datos.gob.ar; source IGN), files dated 2023-12-05:
   24 jurisdictions (INDEC 2-digit codes) and 529 departments/partidos/comunas (INDEC 5-digit codes).
E: INDEC Censo 2022, resultados definitivos (November 2023): population by province (c2022_tp_est_c1) and by department
   (c2022_<province>_est_c1_<n>). INDEC has no provincial or departmental projections based on the 2022 census (D-AR-03).
Usage: build-argentina-q-e-geo-population.py <raw_dir> <research-argentina_dir>
"""
import sys, os, json, hashlib, glob, re
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


def rnd(c):
    if isinstance(c, (int, float)):
        return round(c, 5)
    return [rnd(x) for x in c]


def to_multi(g):
    if g["type"] == "Polygon":
        return {"type": "MultiPolygon", "coordinates": rnd([g["coordinates"]])}
    return {"type": "MultiPolygon", "coordinates": rnd(g["coordinates"])}


def main():
    G = os.path.join(RAW, "georef")
    prov = pd.read_csv(os.path.join(G, "ar_raw_georef_provincias.csv"), dtype={"id": str})
    dept = pd.read_csv(os.path.join(G, "ar_raw_georef_departamentos.csv"), dtype={"id": str, "provincia_id": str})
    prov = prov.sort_values("id")
    gd = prov[["id", "nombre"]].rename(columns={"id": "department_code", "nombre": "name"})
    gd.to_csv(os.path.join(CSV, "geo_department.csv"), index=False)
    dept = dept.sort_values("id")
    gm = pd.DataFrame(dict(municipality_code=dept.id, department_code=dept.provincia_id, name=dept.nombre,
                           category=dept.categoria,
                           lat=dept.centroide_lat.map(lambda v: f"{v:.8f}"), lon=dept.centroide_lon.map(lambda v: f"{v:.8f}")))
    gm["wkt"] = [f"POINT({float(lo):.6f} {float(la):.6f})" for lo, la in zip(gm.lon, gm.lat)]
    gm.to_csv(os.path.join(CSV, "geo_municipality.csv"), index=False)
    pj = json.load(open(os.path.join(G, "ar_raw_georef_provincias.geojson"), encoding="utf-8"))
    rows = [dict(department_code=f["properties"]["id"], name=f["properties"]["nombre"],
                 geojson=json.dumps(to_multi(f["geometry"]), separators=(",", ":"))) for f in pj["features"]]
    pd.DataFrame(rows).sort_values("department_code").to_csv(os.path.join(CSV, "geo_department_shape.csv"), index=False)
    dj = json.load(open(os.path.join(G, "ar_raw_georef_departamentos.geojson"), encoding="utf-8"))
    rows = [dict(municipality_code=f["properties"]["id"], department_code=f["properties"]["provincia"]["id"],
                 name=f["properties"]["nombre"], geojson=json.dumps(to_multi(f["geometry"]), separators=(",", ":")))
            for f in dj["features"]]
    gms = pd.DataFrame(rows).sort_values("municipality_code")
    gms.to_csv(os.path.join(CSV, "geo_municipality_shape.csv"), index=False)
    # ---------------- E ----------------
    C = os.path.join(RAW, "indec_censo2022")
    t = pd.read_excel(os.path.join(C, "ar_raw_c2022_tp_est_c1.xlsx"), sheet_name="Cuadro 1 ", header=None)
    t = t[t[0].astype(str).str.match(r"^\d{2}$")]
    pp = pd.DataFrame(dict(department_code=t[0].astype(int).map(lambda v: f"{v:02d}"), population_2010=t[2].astype(int),
                           population_2022=t[3].astype(int)))
    tot_row = pd.read_excel(os.path.join(C, "ar_raw_c2022_tp_est_c1.xlsx"), sheet_name="Cuadro 1 ", header=None)
    national = int(tot_row[tot_row[1].astype(str).str.strip() == "Total"][3].iloc[0])
    depts = []
    files = sorted(glob.glob(os.path.join(C, "ar_raw_c2022_*_est_c1_*.xlsx")))
    for f in files:
        x = pd.read_excel(f, sheet_name=None, header=None)
        sh = [k for k in x if k.startswith("Cuadro")][0]
        v = x[sh]
        v = v[v[0].astype(str).str.match(r"^\d{4,5}$")]
        for r in v.itertuples():
            depts.append(dict(municipality_code=f"{int(r[1]):05d}", name_census=str(r[2]).strip(),
                              population_2010=None if str(r[3]).strip() in ("///", "-", "nan") else int(r[3]),
                              population_2022=int(r[4])))
    PDp = pd.DataFrame(depts)
    PDp["department_code"] = PDp.municipality_code.str[:2]
    # join to Georef keys
    j = PDp.merge(gm[["municipality_code", "name"]], on="municipality_code", how="outer", indicator=True)
    unmatched = j[j._merge != "both"][["municipality_code", "name_census", "name", "_merge"]].astype(str).to_dict(orient="records")
    fp = PDp[PDp.municipality_code.isin(gm.municipality_code)][["municipality_code", "department_code", "population_2022"]].copy()
    fp.insert(2, "year", 2022)
    fp = fp.rename(columns={"population_2022": "population"}).sort_values("municipality_code")
    fp.to_csv(os.path.join(CSV, "fact_population_municipality.csv"), index=False)
    pdp = pp.merge(gd, on="department_code")
    pdp = pdp[["department_code", "name", "population_2010", "population_2022"]]
    pdp.insert(2, "year", 2022)
    pdp = pdp.rename(columns={"population_2022": "population"})
    pdp.to_csv(os.path.join(CSV, "fact_population_department.csv"), index=False)
    sums = PDp.groupby("department_code").population_2022.sum()
    check_prov = {k: dict(departments=int(sums.get(k, 0)), province=int(v), ok=bool(int(sums.get(k, 0)) == int(v)))
                  for k, v in zip(pp.department_code, pp.population_2022)}
    lq = dict(country="AR", layer="Q", source_id="GEOREF_IGN_202312",
              sources=dict(provincias=dict(file="provincias.csv / provincias.geojson", sha256=[sha(os.path.join(G, "ar_raw_georef_provincias.csv")), sha(os.path.join(G, "ar_raw_georef_provincias.geojson"))], file_date="2023-12-05", rows=int(len(prov))),
                           departamentos=dict(file="departamentos.csv / departamentos.geojson", sha256=[sha(os.path.join(G, "ar_raw_georef_departamentos.csv")), sha(os.path.join(G, "ar_raw_georef_departamentos.geojson"))], file_date="2023-12-05", rows=int(len(dept)))),
              counts=dict(provinces=int(len(prov)), departments=int(len(dept)),
                          departments_per_province=dept.provincia_id.value_counts().sort_index().to_dict(),
                          categories=dept.categoria.value_counts().to_dict()),
              key=dict(province="INDEC 2-digit jurisdiction code (department_code, text with leading zero)",
                       department="INDEC 5-digit code = province + 3 digits (municipality_code); CABA's 15 comunas are its departments (02007-02105)"),
              point_method="Georef centroid of each department (centroide_lat/lon), as published; no centroids computed here.",
              boundaries=dict(source="Georef GeoJSON (IGN), as published (already generalised by Georef); converted to MultiPolygon, 5 decimals",
                              crs="WGS 84 (EPSG:4326), lon/lat"),
              census_join=dict(census_departments=int(len(PDp)), georef_departments=int(len(gm)), unmatched=unmatched),
              limitations="Georef has 529 departments including Antártida Argentina (94028) and Islas del Atlántico Sur (94021). "
                          "Census tables publish Tierra del Fuego by department as listed in unmatched when codes differ.")
    json.dump(_clean(lq), open(os.path.join(OUTP, "layer_q_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    le = dict(country="AR", layer="E", source_id="INDEC_CENSO_2022", period="2022 (census day 18-05-2022)",
              national_population=national, provinces=pdp.to_dict(orient="records"),
              checks=dict(provinces_add_to_national=bool(int(pp.population_2022.sum()) == national),
                          departments_add_to_provinces=check_prov),
              files=[os.path.basename(f) for f in files],
              note="Population counted by the 2022 census (resultados definitivos). INDEC publishes projections 2022-2040 only for the "
                   "total country (2025: see layer O), not by province or department (D-AR-03).")
    json.dump(_clean(le), open(os.path.join(OUTP, "layer_e_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(gd), len(gm), national, pp.population_2022.sum(), unmatched)
    print({k: v["ok"] for k, v in check_prov.items()})


if __name__ == "__main__":
    main()
