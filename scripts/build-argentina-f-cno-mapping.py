#!/usr/bin/env python3
"""Layer F occupation mapping: CNO-2001 (EPH) -> the 13 template personas (CIUO-08).

INDEC publishes only a 2-digit CNO-2001 -> CIUO-08 correspondence, but it also published the EPH 2015 Q1 and Q2
bases double-coded in CIUO-08 at 4 digits (EPH_CIUO_115/215, linkable by CODUSU, NRO_HOGAR, COMPONENTE).
Rule (D-AR-09): a 5-digit CNO-2001 code enters persona P when at least 50% of its weighted employed in 2015 Q1+Q2
hold a CIUO-08 code of P (template annex 2) and the code has at least 5 interviews. Every other code stays outside.
Usage: build-argentina-f-cno-mapping.py <raw_dir> <out_dir>
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


PERSONAS = [
    ("P01", "Software developers and analysts", "core", [2511, 2512, 2513, 2514, 2519]),
    ("P02", "Database, systems and network professionals", "core", [2521, 2522, 2523, 2529]),
    ("P03", "ICT technicians and user support", "core", [3511, 3512, 3513, 3514, 3521, 3522]),
    ("P04", "ICT managers", "core", [1330]),
    ("P05", "Designers (graphic, multimedia, product)", "adjacent", [2163, 2166]),
    ("P06", "Business and management analysts", "adjacent", [2421, 2422]),
    ("P07", "Finance and investment analysts", "adjacent", [2412, 2413]),
    ("P08", "Data, statistics and research specialists", "adjacent", [2120, 2631, 2632, 3314]),
    ("P09", "Marketing and advertising professionals", "adjacent", [2431, 2432]),
    ("P10", "Accountants and auditors", "extended", [2411]),
    ("P11", "Engineers (non-ICT)", "extended", [2141, 2142, 2143, 2144, 2145, 2146, 2149, 2151, 2152, 2153]),
    ("P12", "Business and operations managers", "extended",
     [1211, 1212, 1213, 1219, 1221, 1222, 1223, 1321, 1322, 1323, 1324, 1341, 1342, 1343, 1344, 1345, 1346, 1349]),
    ("P13", "Higher-education and IT educators", "extended", [2310, 2356]),
]
THRESHOLD, MIN_N = 0.5, 5
# CNO-2001 structure (INDEC, CNO-2001 versión reducida, EPHcontinua_CNO2001_reducido_09.pdf, pp. 1-3)
CARACTER = {"00": "Funcionarios del poder ejecutivo", "01": "Funcionarios del poder legislativo", "02": "Funcionarios del poder judicial",
    "03": "Directivos de organismos, empresas e instituciones estatales", "04": "Directivos de instituciones sociales",
    "05": "Directivos de pequeñas y microempresas", "06": "Directivos de medianas empresas privadas",
    "07": "Directivos de grandes empresas privadas", "10": "Gestión administrativa, planificación y control de gestión",
    "11": "Gestión jurídico-legal", "20": "Gestión presupuestaria, contable y financiera", "30": "Comercialización directa",
    "31": "Corretaje comercial, venta domiciliaria, viajantes y promotores", "32": "Comercialización indirecta",
    "33": "Comercialización ambulante y callejera", "34": "Transporte", "35": "Telecomunicaciones", "36": "Almacenaje",
    "40": "Salud y sanidad", "41": "Educación", "42": "Investigación", "43": "Asesoría y consultoría",
    "44": "Prevención de siniestros y medio ambiente", "45": "Comunicación de masas",
    "46": "Servicios sociales, comunales, políticos, gremiales y religiosos", "47": "Vigilancia y seguridad civil",
    "48": "Servicios policiales", "49": "FF.AA., Gendarmería y Prefectura", "50": "Arte", "51": "Deporte",
    "52": "Servicios de recreación", "53": "Servicios gastronómicos", "54": "Alojamiento y turismo",
    "55": "Servicios domésticos", "56": "Limpieza no doméstica", "57": "Cuidado y atención de personas",
    "58": "Servicios sociales varios", "60": "Producción agrícola", "61": "Producción ganadera", "62": "Producción forestal",
    "63": "Producción apícola, avícola y otras especies menores", "64": "Producción pesquera", "65": "Caza",
    "70": "Producción extractiva", "71": "Producción de energía, agua y gas", "72": "Construcción e infraestructura",
    "80": "Producción industrial y artesanal", "81": "Producción de software", "82": "Reparación de bienes de consumo",
    "90": "Instalación y mantenimiento de maquinaria (producción de bienes)", "91": "Desarrollo tecnológico productivo",
    "92": "Instalación y mantenimiento de maquinaria, equipos y sistemas (prestación de servicios)"}
JER = {"0": "dirección", "1": "cuenta propia", "2": "jefes", "3": "trabajadores asalariados"}
TEC = {"0": "", "1": "sin operación de maquinaria", "2": "maquinaria y equipos electromecánicos", "3": "sistemas y equipos informatizados"}
CAL = {"1": "profesional", "2": "técnica", "3": "operativa", "4": "no calificada"}


def cno_label(c):
    if c[:2] not in CARACTER:
        return ""
    parts = [CARACTER[c[:2]], JER.get(c[2], ""), TEC.get(c[3], ""), CAL.get(c[4], "")]
    return " | ".join(p for p in parts if p)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(raw, out):
    pairs = [("indec_eph_2015/ar_raw_t115_dta/Individual_t115.dta", "indec_cno_caes/ciuo115/ar_raw_EPH_CIUO_115/eph_ciuo_115.dta"),
             ("indec_eph_2015/ar_raw_t215_dta/Individual_t215.dta", "indec_cno_caes/ciuo215/ar_raw_EPH_CIUO_215/eph_ciuo_215.dta")]
    frames = []
    for ind, ciu in pairs:
        I = pd.read_stata(os.path.join(raw, ind), convert_categoricals=False)
        C = pd.read_stata(os.path.join(raw, ciu), convert_categoricals=False)
        I.columns = [c.lower() for c in I.columns]; C.columns = [c.lower() for c in C.columns]
        for d in (I, C):
            d["codusu"] = d["codusu"].astype(str).str.strip()
        M = I.merge(C[["codusu", "nro_hogar", "componente", "pp04d_ciuo"]], on=["codusu", "nro_hogar", "componente"], how="left")
        frames.append(M[M.estado == 1][["pp04d_cod", "pp04d_ciuo", "pondera"]])
    D = pd.concat(frames)
    D["cno"] = D.pp04d_cod.astype(str).str.strip().str.zfill(5)
    D["isco"] = D.pp04d_ciuo.astype(str).str.strip()
    i2p = {str(c): pid for pid, _, _, cs in PERSONAS for c in cs}
    D["pid"] = D.isco.map(i2p)
    # CNO-2001 labels and official 2-digit CIUO-08 from INDEC's conversion table
    conv = pd.read_excel(os.path.join(raw, "indec_cno_caes/ar_raw_CONVERSION_CNO-01_CIUO-08.xls"), header=None, skiprows=2)
    conv = conv.iloc[:, :4]; conv.columns = ["label", "code", "ciuo2", "ciuo2_label"]
    conv = conv[conv.code.astype(str).str.match(r"^\d\d\.\d\.\d\.\d$")]
    conv["cno"] = conv.code.str.replace(".", "", regex=False)
    lab = dict(zip(conv.cno, conv.label)); c2 = dict(zip(conv.cno, conv.ciuo2.astype(str)))
    g = D.groupby("cno")
    rows = []
    for cno, sub in g:
        w = sub.pondera.sum(); n = len(sub)
        shares = sub.groupby("pid").pondera.sum() / w if sub.pid.notna().any() else pd.Series(dtype=float)
        best = shares.idxmax() if len(shares) else None
        bshare = float(shares.max()) if len(shares) else 0.0
        top = sub.groupby("isco").pondera.sum().sort_values(ascending=False).head(3)
        status = "outside_personas"
        if best is not None:
            if bshare >= THRESHOLD and n >= MIN_N:
                status = "majority_within_persona"
            elif bshare >= THRESHOLD:
                status = "excluded_small_sample"
            elif bshare >= 0.2:
                status = "excluded_minority"
        rows.append(dict(cno2001_code=cno, cno2001_label=cno_label(cno), ciuo08_2digit_official=c2.get(cno, ""),
                         interviews_2015=n, employed_weighted_2015=int(w),
                         best_persona_id=best or "", best_persona_share=round(bshare, 4),
                         top_ciuo08_codes=";".join(f"{k}:{v / w:.2f}" for k, v in top.items()),
                         mapping_status=status,
                         persona_id=best if status == "majority_within_persona" else ""))
    M = pd.DataFrame(rows).sort_values(["persona_id", "cno2001_code"])
    # quality per persona
    cno2p = dict(zip(M.cno2001_code, M.persona_id))
    D["pid_cno"] = D.cno.map(cno2p).replace("", None)
    qual = []
    for pid, name, ring, codes in PERSONAS:
        tp = D[(D.pid == pid) & (D.pid_cno == pid)].pondera.sum()
        truth = D[D.pid == pid].pondera.sum(); pred = D[D.pid_cno == pid].pondera.sum()
        codes_in = M[M.persona_id == pid].cno2001_code.tolist()
        qual.append(dict(persona_id=pid, persona=name, ring=ring, isco08_template_codes=";".join(map(str, codes)),
                         cno2001_codes_assigned=";".join(codes_in),
                         recall_2015=round(tp / truth, 4) if truth else None,
                         precision_2015=round(tp / pred, 4) if pred else None,
                         size_ratio_cno_vs_ciuo_2015=round(pred / truth, 3) if truth else None,
                         ciuo08_employed_2015=int(truth), cno_employed_2015=int(pred),
                         review_status="identifiable" if codes_in else "not_identifiable_in_cno2001"))
    Q = pd.DataFrame(qual)
    os.makedirs(out, exist_ok=True)
    M.to_csv(os.path.join(out, "f_occupation_mapping_ar.csv"), index=False)
    Q.to_csv(os.path.join(out, "f_persona_correspondence_ar.csv"), index=False)
    conv["label_rebuilt"] = conv.cno.map(cno_label)
    conv[["cno", "label_rebuilt", "label", "ciuo2", "ciuo2_label"]].rename(columns={"cno": "cno2001_code",
        "label_rebuilt": "cno2001_label_from_structure", "label": "cno2001_label_as_published",
        "ciuo2": "ciuo08_2digit", "ciuo2_label": "ciuo08_2digit_label"}).to_csv(
        os.path.join(out, "f_cno2001_ciuo08_correspondence_ar.csv"), index=False)
    meta = dict(country="AR", layer="F",
                purpose="Occupation mapping for EPH 2025 (CNO-2001) to the 13 template personas (CIUO-08). Pending approval.",
                rule=f"majority_within_persona: >= {THRESHOLD:.0%} of the CNO-2001 code's weighted employed in EPH 2015 Q1+Q2 "
                     f"have a CIUO-08 code of the persona, with at least {MIN_N} interviews (D-AR-09).",
                sources=dict(dual_coded=dict(files=["EPH_CIUO_115.rar", "EPH_CIUO_215.rar"],
                                             sha256=[sha(os.path.join(raw, "indec_cno_caes/ar_raw_EPH_CIUO_115.rar")),
                                                     sha(os.path.join(raw, "indec_cno_caes/ar_raw_EPH_CIUO_215.rar"))]),
                             eph_2015=dict(files=["t115_dta.rar", "t215_dta.rar"],
                                           sha256=[sha(os.path.join(raw, "indec_eph_2015/ar_raw_t115_dta.rar")),
                                                   sha(os.path.join(raw, "indec_eph_2015/ar_raw_t215_dta.rar"))]),
                             official_2digit=dict(file="CONVERSION_CNO-01_CIUO-08.xls",
                                                  sha256=sha(os.path.join(raw, "indec_cno_caes/ar_raw_CONVERSION_CNO-01_CIUO-08.xls")))),
                employed_records_2015=int(len(D)), counts_by_status=M.mapping_status.value_counts().to_dict(),
                personas=Q.to_dict(orient="records"))
    json.dump(_clean(meta), open(os.path.join(out, "f_cno_mapping_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(Q.to_string())
    print(M[M.persona_id != ""][["cno2001_code", "persona_id", "best_persona_share", "interviews_2015", "cno2001_label"]].to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
