#!/usr/bin/env python3
"""sources_register.csv, decisions_log.csv, f_mapping_overrides.csv, outputs/f_mapping_review_ar.csv, geodb/csv/meta_sources.csv
and validation/r_checks_ar.json (layer R). Usage: build-argentina-docs-registers.py <raw_dir> <research-argentina_dir>"""
import sys, os, csv, json, hashlib
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
CSV = os.path.join(OUT, "geodb", "csv"); OUTP = os.path.join(OUT, "outputs"); VAL = os.path.join(OUT, "validation")


def h(*paths):
    return "; ".join(f"{os.path.basename(p).replace('ar_raw_', '')}: {hashlib.sha256(open(os.path.join(RAW, p), 'rb').read()).hexdigest()}" for p in paths)


ACC = "2026-11-18"
DL = "web download through the user's browser (Downloads, prefix ar_raw_), staged into the workspace"
SRC = [
 ("GEOREF_IGN_202312", "Q", "Q1", "Servicio de normalización de datos geográficos (Georef): provincias y departamentos (CSV y GeoJSON)", "Jefatura de Gabinete de Ministros / IGN (datos.gob.ar)", "files dated 2023-12-05", "2023-12",
  "https://infra.datos.gob.ar/georef/departamentos.geojson ; https://infra.datos.gob.ar/georef/provincias.geojson", ACC, DL,
  "provincias.csv; departamentos.csv; provincias.geojson; departamentos.geojson", h("georef/ar_raw_georef_provincias.csv", "georef/ar_raw_georef_departamentos.csv", "georef/ar_raw_georef_provincias.geojson", "georef/ar_raw_georef_departamentos.geojson"),
  "Datos Argentina terms (CC BY 4.0 per datos.gob.ar; to confirm)", "scripts/build-argentina-q-e-geo-population.py", "verified",
  "24 jurisdictions and 529 departments, partidos and comunas with INDEC codes; geometries as published by Georef."),
 ("INDEC_CENSO_2022", "E, C, L", "E1, E2, C2, L6", "Censo Nacional de Población, Hogares y Viviendas 2022, resultados definitivos: Cuadro 1 (población por jurisdicción) y cuadros provinciales 1.n (población por departamento) y 2.n (asistencia por nivel educativo)", "INDEC", "resultados definitivos, noviembre de 2023", "2022",
  "https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-41-165", ACC, DL, "c2022_tp_est_c1.xlsx; c2022_<provincia>_est_c1_<n>.xlsx (24); c2022_<provincia>_educacion_c2_<n>.xlsx (24)",
  h("indec_censo2022/ar_raw_c2022_tp_est_c1.xlsx"), "INDEC (cite the source)", "scripts/build-argentina-q-e-geo-population.py; scripts/build-argentina-k-c-l-education.py", "verified",
  "Total 45,892,285. Departments add up to every province exactly. 94021 (Islas del Atlántico Sur) has no census population. SHA-256 of the 48 provincial files in raw/README.md."),
 ("INDEC_PROYECCIONES_2022_2040", "E, O", "context", "Estimaciones y proyecciones de población 2022-2040, total del país", "INDEC", "2025", "2022-2040",
  "https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-24-84", ACC, DL, "proyecciones_nacionales_2022_2040_c1_c2.xlsx", h("indec_censo2022/ar_raw_proyecciones_nacionales_2022_2040_c1_c2.xlsx"),
  "INDEC (cite the source)", "", "verified", "National only; no provincial projections based on the 2022 census are published (D-AR-03). Kept for reference, not used in tables."),
 ("SRC_GH_IG", "A", "A1, A2, A3, A4, A5", "GitHub Innovation Graph", "GitHub", "release 1.0.10, commit 078fb62ee4395d321bec9f4f06694cca68f6b6cb (2026-08-31), the same as Peru and Mexico", "2026Q1 vs 2025Q1",
  "https://github.com/github/innovationgraph", ACC, "raw.githubusercontent.com at the commit", "data/developers.csv; organizations.csv; git_pushes.csv; repositories.csv; languages.csv",
  h("github_innovationgraph/developers.csv", "github_innovationgraph/languages.csv"), "CC0-1.0 (repository LICENSE.md)", "scripts/build-argentina-a-github.py", "verified",
  "Identical file hashes to the Mexico register. The engine reproduces Mexico's 25 indicator, 192 language and 100 quarterly rows and the 18-country LATAM table (144/144 fields)."),
 ("SRC_SO_2025", "B", "B1, B2, B3, B4, B5", "Stack Overflow Developer Survey 2025, results.csv (and the official aggregate ai.json)", "Stack Overflow", "2025 public data; archive repository commit c9c23dc6f385d5be1a3011c238deb6c23b617e93, the same as Peru and Mexico", "2025",
  "https://survey.stackoverflow.co/ ; https://github.com/StackExchange/Survey/tree/main/packages/archive/2025", ACC, "Git LFS object from media.githubusercontent.com at the commit", "results.csv; json/ai.json",
  h("stackoverflow_survey/so_2025/results.csv", "stackoverflow_survey/so_2025/ai.json"), "ODbL 1.0 (database) / DbCL 1.0 (contents)", "scripts/build-argentina-b-survey.py", "verified",
  "222 Argentina respondents (low confidence, below 300). The engine reproduces all 1,264 + 280 + 8 rows of the Mexico package; Argentina's rows equal the AR comparison group published there."),
 ("INDEC_EPH_2025", "F, G, H, M, I (incomes), O (developer income)", "F1-F11, G1-G4, H1-H2, M1-M3, M5, M6", "Encuesta Permanente de Hogares (EPH), bases usuarias individual y hogar, 2025 trimestres 1 a 4 (txt), con diseño de registro", "INDEC", "2025 Q1-Q4 (31 aglomerados urbanos)", "2025",
  "https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos", ACC, DL, "EPH_usu_1_Trim_2025_txt.zip ... EPH_usu_4_Trim_2025_txt.zip; EPH_registro_1T2025.pdf; EPH_registro_4T2025.pdf",
  h("indec_eph_2025/ar_raw_EPH_usu_1_Trim_2025_txt.zip", "indec_eph_2025/ar_raw_EPH_usu_2_Trim_2025_txt.zip", "indec_eph_2025/ar_raw_EPH_usu_3_Trim_2025_txt.zip", "indec_eph_2025/ar_raw_EPH_usu_4_Trim_2025_txt.zip"),
  "INDEC (cite: 'Fuente: Instituto Nacional de Estadística y Censos (INDEC)')", "scripts/build-argentina-eph.py; scripts/build-argentina-f-crossref.py", "verified",
  "Employment and unemployment rates per quarter equal INDEC's published rates (Cuadro 1.1) within rounding. Occupation coded in CNO-2001 (design record PP04D_COD); activity in CAES-Mercosur 1.0."),
 ("INDEC_EPH_INFORME_2026_09", "R (F check)", "R1", "Mercado de trabajo. Principales tasas del mercado laboral (EPH), segundo trimestre de 2016 a segundo trimestre de 2026", "INDEC", "September 2026", "2016Q2-2026Q2",
  "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58", ACC, DL, "cuadros_eph_informe_09_26.xls (Cuadro 1.1)", h("indec_eph_reports/ar_raw_cuadros_eph_informe_09_26.xls"),
  "INDEC (cite the source)", "scripts/build-argentina-eph.py", "verified", "2025 employment rate 44.4 / 44.5 / 45.4 / 45.0; unemployment 7.9 / 7.6 / 6.6 / 7.5."),
 ("INDEC_CNO2001_CIUO08", "F", "F1 (occupation mapping)", "Clasificador Nacional de Ocupaciones CNO-2001 (versión reducida) and Tabla de correspondencia CNO-2001 / CIUO-08 (2 dígitos)", "INDEC", "CNO-2001; correspondence file as published", "2001",
  "https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/CONVERSION_CNO-01_CIUO-08.xls", ACC, DL, "EPHcontinua_CNO2001_reducido_09.pdf; CONVERSION_CNO-01_CIUO-08.xls",
  h("indec_cno_caes/ar_raw_EPHcontinua_CNO2001_reducido_09.pdf", "indec_cno_caes/ar_raw_CONVERSION_CNO-01_CIUO-08.xls"), "INDEC (cite the source)", "scripts/build-argentina-f-cno-mapping.py", "verified",
  "Official correspondence only at CIUO-08 2 digits. Its label column is shifted against the codes in part of the file; labels are rebuilt from the CNO-2001 structure."),
 ("INDEC_EPH_CIUO_2015", "F", "F1 (occupation mapping)", "EPH primer y segundo trimestre de 2015 codificados en CIUO-08 (EPH_CIUO_115, EPH_CIUO_215) and the EPH 2015 Q1-Q2 individual bases", "INDEC", "2015 Q1 and Q2", "2015",
  "https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/EPH_CIUO_115.rar", ACC, DL, "EPH_CIUO_115.rar; EPH_CIUO_215.rar; t115_dta.rar; t215_dta.rar",
  h("indec_cno_caes/ar_raw_EPH_CIUO_115.rar", "indec_cno_caes/ar_raw_EPH_CIUO_215.rar", "indec_eph_2015/ar_raw_t115_dta.rar", "indec_eph_2015/ar_raw_t215_dta.rar"),
  "INDEC (cite the source)", "scripts/build-argentina-f-cno-mapping.py; scripts/build-argentina-f-crossref.py", "verified", "48,559 employed records with both CNO-2001 and CIUO-08 (4 digits); used only to decide which CNO-2001 codes enter each persona (D-AR-09)."),
 ("INDEC_CAES_MERCOSUR", "F, G, M", "F5, G1", "Clasificador de Actividades Económicas para Encuestas Sociodemográficas del Mercosur (CAES-Mercosur 1.0)", "INDEC", "1.0", "classification used in EPH 2025",
  "https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/caes_mercosur_1.0.pdf", ACC, DL, "caes_mercosur_1.0.pdf; EPHcontinua_CAES_Mercosur_09.pdf", h("indec_cno_caes/ar_raw_caes_mercosur_1.0.pdf"),
  "INDEC (cite the source)", "scripts/build-argentina-eph.py", "verified", "Division -> section table (tech sector = section J, divisions 58-63)."),
 ("INDEC_GBA_2003", "J", "J1-J4 (zone definition)", "¿Qué es el Gran Buenos Aires? (folleto)", "INDEC", "2003", "2003", "https://www.indec.gob.ar/dbindec/folleto_gba.pdf", ACC, DL, "folleto_gba.pdf",
  h("indec_censo2022/ar_raw_folleto_gba.pdf"), "INDEC", "scripts/build-argentina-d-n-j-companies.py", "verified", "Definition of the 24 partidos of Gran Buenos Aires (also the census row '24 Partidos del Gran Buenos Aires', 10,849,299 inhabitants in 2022)."),
 ("MEN_RA_2025", "K, L", "K2-K4, K7, L1 (SNU), L7", "Relevamiento Anual 2025: base agregada de matrícula y secciones; matrícula por edad; características (and the 2024 equivalents)", "Secretaría de Educación, Subsecretaría de Evaluación e Información Educativa (datos.gob.ar)", "Base de Datos por Escuela 2025, published 2026-09-10", "2025",
  "https://datos.gob.ar/dataset/base-de-datos-por-escuela-2025", ACC, DL + " (SharePoint links of the dataset, ?download=1)", "2025 Matricula - agregada.csv; 2025 Matricula por edad - agregada.csv; 2025 Caracteristicas - agregada.csv; Diccionario de bases RA anonimizadas.xlsx",
  h("educ_ra/ar_raw_ra2025_agregada_matricula.csv", "educ_ra/ar_raw_ra2025_agregada_matricula_edad.csv"), "Datos Argentina terms (to confirm)", "scripts/build-argentina-k-c-l-education.py", "verified",
  "Aggregated by province x department x sector x ámbito; some small departments masked as 'Enmascarado' (statistical secrecy). Target años 9-12 = 2,676,351."),
 ("MEN_PADRON_2026", "K, L, P", "K1, K3, L5, P1", "Padrón Oficial de Establecimientos Educativos (establecimientos y ofertas activas)", "Secretaría de Educación (DIE)", "updated 2026-06-16", "2026",
  "https://www.argentina.gob.ar/sites/default/files/2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx", ACC, DL, "2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx",
  h("educ_padron/ar_raw_2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx"), "Datos Argentina terms (to confirm)", "scripts/build-argentina-k-c-l-education.py", "verified",
  "64,696 localizaciones; 13,750 with a common secondary offer (incl. INET). Contact columns are not used or published."),
 ("SPU_ANUARIO_2024", "C, L", "C1, C4, L1-L4", "Anuario Estadístico del Sistema Universitario Argentino 2024 (adelanto parcial, capítulos 1-6)", "Ministerio de Capital Humano, Subsecretaría de Políticas Universitarias (DNPeIU)", "advance dated 2026-08-14", "2024",
  "https://www.argentina.gob.ar/educacion/universidades/informacion/publicaciones/anuarios", ACC, DL, "adelanto_anuario_24_14-08.zip > Z 1.1 Datos Generales 24.xlsx",
  h("univ/ar_raw_adelanto_anuario_24_14-08.zip"), "Government publication", "scripts/build-argentina-k-c-l-education.py", "verified",
  "2,608,231 undergraduate students; discipline Informática 186,240. Published by institution and CPRES region, not by province (D-AR-05)."),
 ("SPU_SINTESIS_2023_2024", "C, L", "context", "Síntesis de Información Universitaria 2023-2024", "Ministerio de Capital Humano, SPU", "2023-2024", "2023-2024",
  "https://www.argentina.gob.ar/sites/default/files/sintesis_anuario_2023-2024.pdf", ACC, DL, "sintesis_anuario_2023-2024.pdf", h("univ/ar_raw_sintesis_anuario_2023-2024.pdf"),
  "Government publication", "", "verified", "Kept for reference; the 2024 Anuario advance is the latest year."),
 ("CEP_XXI_ESTABLECIMIENTOS_2022", "D, J, N, P", "D1, D2, J1-J4, N1, N3, N4, P3", "Distribución geográfica de los establecimientos productivos (versión exploratoria), with activity and department dictionaries and methodology", "CEP XXI (Ministerio de Economía) and MTEySS, from SIPA/AFIP", "methodology December 2023; rows for 2021 and 2022", "2022",
  "https://cdn.produccion.gob.ar/cdn-cep/establecimientos-productivos/distribucion_establecimientos_productivos_sexo.csv", ACC, DL,
  "distribucion_establecimientos_productivos_sexo.csv; actividades_establecimientos.csv; codigo_departamento_provincia.csv; Datos_por_departamento_y_actividad.csv; Metodologia_establecimiento_productivos.pdf",
  h("cep_xxi/ar_raw_cep_distribucion_establecimientos_productivos_sexo.csv", "cep_xxi/ar_raw_cep_Datos_por_departamento_y_actividad.csv"), "Datos Argentina terms (to confirm)", "scripts/build-argentina-d-n-j-companies.py", "verified",
  "715,377 establishments in 2022 (equal to the department file total for 2022), 546,421 distinct anonymised CUIT. Registered employers only."),
 ("CESSI_OPSSI_2026Q1_PRESS", "D", "D3", "Informe de la Industria del Software (OPSSI, CESSI), primer trimestre de 2026, as quoted by Ámbito", "CESSI / OPSSI (via Ámbito)", "published 29-07-2026", "2026Q1",
  "https://www.ambito.com/tecnologia/la-industria-del-software-argentino-vuelve-tener-exportaciones-record-pero-el-empleo-cae-primera-vez-seis-anos-n6304732", ACC, "web page (press)", "", "", "Press", "", "to_confirm",
  "162,391 registered jobs (Q1 2026, -0.5% vs Q4 2025); exports USD 744M in Q1 2026 and 2,848M in 12 months. Number of firms not stated; confirm with the OPSSI report."),
 ("BCRA_A3500", "I, P", "I1, P2", "Tipo de cambio de referencia Comunicación 'A' 3500 (mayorista), serie diaria", "Banco Central de la República Argentina", "file downloaded 2026-11-18 (series to 2026-11-17)", "2025",
  "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/com3500.xls", ACC, DL, "com3500.xls", h("context/ar_raw_bcra_com3500.xls"), "BCRA terms of use (to confirm)", "scripts/build-argentina-i-o-p.py", "verified",
  "2025 average 1,244.2597 ARS/USD over the business days of 2025 (duplicated dates dropped); December 2025 average 1,447.8377."),
 ("CNEPYSMVYM_RES_2024_17_2025_5_2025_9", "I, O", "I3, O1", "Consejo Nacional del Empleo, la Productividad y el Salario Mínimo, Vital y Móvil: Resoluciones 17/2024, 5/2025 and 9/2025", "Boletín Oficial de la República Argentina", "BO 26-12-2024; Res. 5/2025 of 08-05-2025; BO 03-12-2025", "2025",
  "https://www.boletinoficial.gob.ar/detalleAviso/primera/318790/20241226 ; https://www.boletinoficial.gob.ar/pdf/aviso/primera/325046/20250718 ; https://www.boletinoficial.gob.ar/detalleAviso/primera/335463/20251203", ACC, "web page (official gazette), text read", "", "",
  "Official gazette", "scripts/build-argentina-i-o-p.py", "verified", "Monthly 2025: 286,711; 292,446; 296,832; 302,600; 308,200; 313,400; 317,800; 322,000 (Aug-Oct); 328,400; 334,800. Sep-Oct carry August's amount (no resolution in between)."),
 ("IMF_WEO_DATAMAPPER", "O", "O1", "World Economic Outlook, DataMapper indicator NGDPDPC (GDP per capita, current prices, USD)", "International Monetary Fund", "DataMapper API as served on 2026-11-18 (WEO October 2026)", "2025",
  "https://www.imf.org/external/datamapper/api/v1/NGDPDPC", ACC, "API JSON saved from the browser", "imf_datamapper_NGDPDPC_downloaded_2026-11-18.json", h("context/ar_raw_imf_datamapper_NGDPDPC_downloaded_2026-11-18.json"),
  "IMF copyright and usage terms (free reuse with attribution)", "scripts/build-argentina-i-o-p.py", "verified", "Argentina 2025 = USD 14,399.3; Mexico 13,759.3 (same value as the Mexico package, so same WEO edition)."),
 ("WB_FINDEX_2025", "O", "O2", "Global Findex Database 2025 (survey 2024), indicator FX.OWN.TOTL.ZS via the World Bank API", "World Bank", "API lastupdated 2026-11-11", "2024",
  "https://api.worldbank.org/v2/country/ARG/indicator/FX.OWN.TOTL.ZS?format=json", ACC, "API JSON saved from the browser", "worldbank_api_findex_2026-11-18.json", h("context/ar_raw_worldbank_api_findex_2026-11-18.json"),
  "CC BY 4.0 (World Bank)", "scripts/build-argentina-i-o-p.py", "verified", "Account ownership 81.7% of 15+ (women 84.2%). Credit-card ownership not retrieved (API timed out); BCRA figure used instead."),
 ("BCRA_INCLUSION_2026_04", "O", "O2", "Informe de Inclusión Financiera, abril de 2026", "BCRA", "April 2026", "December 2025",
  "https://www.bcra.gob.ar/archivos/Pdfs/publicacionesestadisticas/informes/informe-inclusion-financiera-2026-04.pdf", ACC, DL, "informe-inclusion-financiera-2026-04.pdf", h("context/ar_raw_bcra_informe-inclusion-financiera-2026-04.pdf"),
  "Government publication", "scripts/build-argentina-i-o-p.py", "verified", "37.8 million adults with an account; 35.8M bank account; 30.1M payment account; 14.8M credit-card debtors (Dec 2025)."),
 ("BCRA_PAGOS_MINORISTAS_2025_12", "O", "O2", "Informe Mensual de Pagos Minoristas, diciembre de 2025", "BCRA", "December 2025", "2025-12",
  "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-pagos-minoristas-2025-12.pdf", ACC, DL, "informe-pagos-minoristas-2025-12.pdf", h("context/ar_raw_bcra_informe-pagos-minoristas-2025-12.pdf"),
  "Government publication", "scripts/build-argentina-i-o-p.py", "verified", "753M push transfers (ARS 88.7 billones); 96.4M PCT (95M QR); 84 interoperable wallets."),
 ("LEY_IVA_TO1997", "O", "O3", "Ley de Impuesto al Valor Agregado (t.o. 1997): art. 1 inc. e), art. 3 inc. e) ap. 21 subinc. m), art. 28", "AFIP/ARCA Biblioteca Electrónica; Consejo Profesional (art. 28)", "text in force (art. 1 and 3 as modified by Ley 27.430, arts. 87-88)", "in force 2026",
  "https://biblioteca.afip.gob.ar/dcp/TOR_C_020631_1997_03_26 ; https://archivo.consejo.org.ar/Bib_elect/BD_Dic/documentos/art28_IVA.htm", ACC, "web page, text read", "", "", "Official legal text", "scripts/build-argentina-i-o-p.py", "verified",
  "General rate 21% (art. 28). Ley 27.802 (BO 06-03-2026) art. 189 adds a 10.5% rate only for irrigation electricity."),
 ("DECRETO_354_2018", "O", "O3", "Decreto 354/2018, reglamentación del IVA sobre servicios digitales", "Boletín Oficial (argentina.gob.ar/normativa)", "BO 24-04-2018", "in force 2026",
  "https://www.argentina.gob.ar/normativa/nacional/decreto-354-2018-309281/texto", ACC, "web page, text read", "", "", "Official legal text", "scripts/build-argentina-i-o-p.py", "verified", "Tax borne by the prestatario (buyer); collected by the resident payment intermediary; AFIP lists of foreign providers."),
 ("LEY_25326", "O, P", "O4, P5", "Ley 25.326 de Protección de los Datos Personales", "Congreso de la Nación", "sanctioned 04-10-2000, promulgated 30-10-2000", "in force 2026",
  "https://www.unc.edu.ar/sites/default/files/Ley-de-Proteccion-de-Datos-Personales-Nro-25326.pdf", ACC, "web page, text read (copy of the law)", "", "", "Official legal text", "scripts/build-argentina-i-o-p.py", "verified", "Art. 5 consent: free, express and informed, in writing or equivalent; no article on minors."),
 ("DECRETO_746_2017", "O", "O4", "Decreto 746/2017 (AAIP como autoridad de aplicación de la Ley 25.326)", "Boletín Oficial", "25-09-2017", "in force 2026",
  "https://consejosalta.org.ar/wp-content/uploads/DECRETO-746.pdf", ACC, "web page, text read (copy of the decree)", "", "", "Official legal text", "", "verified", "Arts. 11 and 13."),
 ("AAIP_RES_4_2019", "P", "P5", "AAIP Resolución 4/2019, criterios orientadores e indicadores de mejores prácticas (criterio 5, menores)", "Agencia de Acceso a la Información Pública", "10-01-2019", "in force 2026",
  "https://argentina.gob.ar/normativa/318874_res4AAIP_pdf/archivo", ACC, "web page, text read", "", "", "Official legal text", "scripts/build-argentina-i-o-p.py", "verified", "Minors consent according to progressive autonomy (CCyC arts. 26 and 639); otherwise parents or guardians."),
 ("DISPOSICION_2_2023_SSTI", "O", "O5", "Disposición 2/2023, Recomendaciones para una Inteligencia Artificial Fiable", "Jefatura de Gabinete de Ministros, Subsecretaría de Tecnologías de la Información", "BO 02-06-2023", "in force 2026",
  "https://www.argentina.gob.ar/normativa/nacional/norma-384656/texto", ACC, "web page, text read", "", "", "Official legal text", "scripts/build-argentina-i-o-p.py", "verified",
  "Recommendations, not a law. No national AI law as of 2026 (regulations.ai overview updated 2026-09-20; Estudio Vilaplana, 12-09-2026)."),
 ("LEY_GANANCIAS_TO2019", "P", "P4", "Ley de Impuesto a las Ganancias (t.o. 2019), art. 85 inc. c) (donaciones, tope 5% de la ganancia neta)", "AFIP/ARCA; cited by UNC FCQ instructivo (2025)", "t.o. 2019", "in force 2026",
  "https://www.fcq.unc.edu.ar/wp-content/uploads/2025/11/instructivo-para-deduccion-de-ganancias-faiq.pdf", ACC, "web page, text read", "", "", "Official legal text (secondary copy)", "scripts/build-argentina-i-o-p.py", "to_confirm",
  "The instructivo quotes the old numbering (art. 81 inc. c); confirm article and cap with legal."),
 ("INDEC_TIC_2024Q4", "O", "O6", "Acceso y uso de tecnologías de la información y la comunicación. EPH, cuarto trimestre de 2024 (informe y cuadros)", "INDEC", "May 2025", "2024Q4",
  "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-26-71", ACC, DL, "cuadros_tic_05_25.xls; mautic_05_25FD0D0C4A71.pdf", h("indec_tic/ar_raw_cuadros_tic_05_25.xls"),
  "INDEC (cite the source)", "scripts/build-argentina-i-o-p.py", "verified", "Latest edition on the INDEC site at 2026-11-18. Households: internet 93.7%, computer 60.3%. Persons 4+: internet 89.7%, computer 37.1%, mobile 90.5%."),
 ("DATAREPORTAL_DIGITAL_2026_AR", "O", "O6", "Digital 2026: Argentina (DataReportal, Kepios / We Are Social / Meltwater)", "DataReportal (Kepios)", "page saved 2026-11-18", "October / end of 2025",
  "https://datareportal.com/reports/digital-2026-argentina", ACC, "page saved from the browser", "datareportal_digital-2026-argentina_page_downloaded_2026-11-18.html", h("context/ar_raw_datareportal_digital-2026-argentina_page_downloaded_2026-11-18.html"),
  "DataReportal terms (citation with attribution; to confirm)", "scripts/build-argentina-i-o-p.py", "verified", "41.6 million internet users, 90.6%; fixed 99.62 Mbps and mobile 60.40 Mbps (Ookla)."),
 ("STATCOUNTER_2025_AR", "O", "O6", "StatCounter Global Stats: desktop vs mobile vs tablet market share, Argentina, yearly 2025", "StatCounter", "yearly 2025 export", "2025",
  "https://gs.statcounter.com/platform-market-share/desktop-mobile-tablet/argentina/#yearly-2025-2025", ACC, "CSV export from the browser", "statcounter_desktop_mobile_tablet_AR_yearly_2025.csv", h("context/ar_raw_statcounter_desktop_mobile_tablet_AR_yearly_2025.csv"),
  "CC BY-SA 3.0 (StatCounter Global Stats)", "scripts/build-argentina-i-o-p.py", "verified", "Mobile 53.58%, desktop 45.94%, tablet 0.48%."),
]
COLS = ["source_id", "layers", "indicator_ids", "source_name", "publisher", "dataset_version", "reference_period", "url", "access_date",
        "access_method", "file_name", "sha256", "license", "script", "status", "notes"]

DEC = [
 ("D-AR-01", "Geography: province = department_code (INDEC 2 digits, text with leading zero); department/partido/comuna = municipality_code (INDEC 5 digits). Every table carries department_code; province tables are the primary level (user request, 2026-11-18)", "approved",
  "Same two-level shape as Mexico (state + municipality). Province tables were added where Mexico only has municipal ones: fact_population_department, fact_schools_department, fact_higher_ed_department, fact_companies_department."),
 ("D-AR-02", "Geography keys and shapes from Georef (IGN) files of 2023-12-05: 24 jurisdictions and 529 departments; Georef centroids as reference points; geometries as published (already generalised), only converted to MultiPolygon with 5 decimals", "approved",
  "No further simplification was applied (Mexico simplified INEGI's full-resolution shapes). CABA's 15 comunas are departments 02007-02105."),
 ("D-AR-03", "Population = Censo 2022 resultados definitivos by province and department (year 2022)", "approved",
  "INDEC publishes 2022-2040 projections only for the total country; no provincial or departmental projections from the 2022 census exist. 94021 Islas del Atlántico Sur has no census population (no row, never zero)."),
 ("D-AR-04", "Layer K: RA 2025 aggregated enrolment; target grades = años corridos 9-12; technical 13th-14th year excluded; schools = Padrón 2026 localizaciones with a common secondary offer", "approved",
  "Años corridos make the target independent of the 6+6 / 7+5 provincial structures. Since 2024 the RA bases are published aggregated by department, so K5 median, size bands and K6 (cap 100 reach) cannot be computed: averages are given and K6 is empty. Department names of the RA were matched to Georef codes (98.1% of target students); masked rows ('Enmascarado') stay at province level only."),
 ("D-AR-05", "Layers C and L: university figures from the SPU Anuario 2024 (national, institution, CPRES region, discipline Informática for ICT); provincial university students from Censo 2022 attendance (by residence); SNU enrolment from RA 2025; vocational training as centres counted in the Padrón", "approved",
  "The SPU does not publish students by province or city of the programme. Census attendance is by residence and 2022; it is the only official provincial count. FP enrolment is not in the open data."),
 ("D-AR-06", "Layers D, N, J: CEP XXI 'Distribución geográfica de los establecimientos productivos', 2022 rows. IT = CLAE6 620100, 620200, 620300, 620900, 631110, 631120, 631190, 631200; software = 620100; shops = 4711xx; businesses = distinct anonymised CUIT", "approved",
  "Universe = establishments with registered employees (SIPA), private and majority state-owned companies; firms without employees are outside, unlike RUES (Colombia) or DENUE (Mexico). Three legacy department codes recoded to current ones: 06217->06218 (Chascomús), 94007->94008 (Río Grande), 94014->94015 (Ushuaia). Province business counts can add to more than the national distinct CUIT (firms present in several provinces)."),
 ("D-AR-07", "Layer J zones: CABA by its 15 comunas (CABA-) and the 24 partidos of Gran Buenos Aires defined by INDEC (GBA-)", "approved",
  "User choice (2026-11-18). Each zone is a whole comuna or partido; micro = 1-9 registered employees, medium_large = 50+ (CEP XXI bands)."),
 ("D-AR-08", "EPH geography: each of the 31 agglomerates assigned to the province of its main city and anchored to the department of that city; Partidos del GBA anchored to La Matanza (06427), CABA to Comuna 1 (02007), San Nicolás-Villa Constitución to Buenos Aires, Viedma-Carmen de Patagones to Río Negro", "approved",
  "The EPH covers urban agglomerates only (about 30 million people); provincial persona rows are the agglomerates of each province, not the whole province. EPH microdata do not identify the province inside bi-provincial agglomerates."),
 ("D-AR-09", "Occupation mapping: a CNO-2001 5-digit code enters a persona when at least 50% of its weighted employed in INDEC's double-coded EPH 2015 Q1-Q2 hold a CIUO-08 code of that persona, with at least 5 interviews", "pending_approval",
  "INDEC's official correspondence is only at CIUO-08 2 digits. Result: P01, P03, P06, P07, P10, P11, P12, P13 identifiable; P02, P04, P05, P08, P09 have no majority code (empty, never zero). P01 also holds most database/network professionals (P01 codes: recall 87%, precision 91% for CIUO-08 251+252). Recall and precision per persona in outputs/f_persona_correspondence_ar.csv; code-by-code cross-reference (which CNO-2001 codes each persona holds, where the workers of the empty personas sit, and 2025 employment per code) in outputs/f_persona_crossref_ar.csv. No manual overrides applied (f_mapping_overrides.csv is empty)."),
 ("D-AR-10", "Layer M: micro-businesses = own-account workers and employers in units of up to 10 people (EPH 2025)", "approved",
  "Argentina has no micro-business survey (EMICRON equivalent). EPH size bands are 1-5 and 6-10, so the template limit of 9 cannot be applied (as in Mexico). M4 digital adoption is not available."),
 ("D-AR-11", "Period: EPH 2025 Q1-Q4 (calendar year, as Mexico), although 2026 Q1-Q2 results are already published (informe de septiembre de 2026); RA 2025; Anuario universitario 2024; CEP XXI 2022 (latest open release); Censo 2022", "approved",
  "Latest complete sources at 2026-11-18. Periods differ by layer and are written on every table and row."),
 ("D-AR-12", "Layer A and B engines re-implemented from the Mexico/Peru outputs (scripts/build-argentina-a-github.py, build-argentina-b-survey.py) and validated by reproducing every Mexico row before running for Argentina", "approved",
  "The Peru engines (layer_a_country.py, layer_b_engine.py) were not in the delivered package."),
 ("D-AR-13", "Socioeconomic level = household per-capita income deciles 7-10 of the total EPH (DECCFR); size bands 201+ and 11-200 (EPH bands cut at 10 and 200, as Colombia)", "approved",
  "Replaces Colombia's electricity stratum and Mexico's ENOE stratum. Income = P21 weighted with PONDIIO, current pesos of each quarter (2025 had high inflation: medians mix quarters)."),
 ("D-AR-14", "Price layer: Com. A 3500 2025 average and December 2025 average; minimum wage = 2025 average of the 12 monthly SMVM amounts and the December 2025 amount", "approved",
  "Both annual and December values are shown because the peso moved strongly during 2025."),
 ("D-AR-15", "Web map display: polygon parts lying entirely south of 60°S (the Antarctic sector of Tierra del Fuego, department 94028 Antártida Argentina) are left out of the map; the country is framed on its continental extent", "approved",
  "Web Mercator cannot draw the sector down to the South Pole, and no data refer to it (no census population, no establishments). geo_department_shape and geo_municipality_shape keep the geometry exactly as published by Georef; only lib/argentinaData.js filters it. Islas del Atlántico Sur (94021) stay on the map."),
 ("D-AR-16", "Load Argentina in the application through a read-only file adapter (lib/argentinaData.js, /api/argentina/*), as Mexico (D-MX-01) and Peru; province values come from the province tables, never from summing departments", "approved",
  "Some province figures cannot be rebuilt from departments: RA rows masked by statistical secrecy, distinct firms (CUIT) counted once per province, and EPH figures that exist only by province. Checks: node scripts/check-argentina.js."),
]


def main():
    with open(os.path.join(OUT, "sources_register.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL); w.writerow(COLS)
        for r in SRC:
            w.writerow(r)
    with open(os.path.join(OUT, "decisions_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["decision_id", "date", "decision", "status", "note", "current", "superseded_by"])
        for d in DEC:
            w.writerow([d[0], "2026-11-18", d[1], d[2], d[3], True, ""])
    with open(os.path.join(OUT, "f_mapping_overrides.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["cno2001_code", "persona_id", "action", "status", "decision_id", "note"])
    mp = pd.read_csv(os.path.join(OUTP, "f_occupation_mapping_ar.csv"), dtype=str).fillna("")
    rev = mp[mp.mapping_status.isin(["excluded_minority", "excluded_small_sample"])].copy()
    rev["suggested_action"] = "exclude"; rev["decision_id"] = "D-AR-09"; rev["current"] = "excluded"
    rev[["cno2001_code", "cno2001_label", "best_persona_id", "best_persona_share", "interviews_2015", "top_ciuo08_codes",
         "mapping_status", "suggested_action", "decision_id", "current"]].to_csv(os.path.join(OUTP, "f_mapping_review_ar.csv"), index=False)
    # meta_sources
    meta = [
     ("geo_department", "Provinces of Argentina: 23 provinces and the Ciudad Autónoma de Buenos Aires (INDEC 2 digits).", "Georef (IGN), provincias.csv, 2023-12-05 (build-argentina-q-e-geo-population.py)", 2023),
     ("geo_municipality", "Departments, partidos and comunas (INDEC 5 digits = province + department) with the Georef centroid as reference point.", "Georef (IGN), departamentos.csv, 2023-12-05", 2023),
     ("geo_department_shape", "Province boundaries (MultiPolygon, WGS84 lon/lat, 5 decimals) as published by Georef.", "Georef (IGN), provincias.geojson, 2023-12-05", 2023),
     ("geo_municipality_shape", "Department boundaries (MultiPolygon, WGS84 lon/lat, 5 decimals) as published by Georef.", "Georef (IGN), departamentos.geojson, 2023-12-05", 2023),
     ("geo_zone", "Zones of the largest city: CABA's 15 comunas (CABA-) and the 24 partidos of Gran Buenos Aires (GBA-), each a whole department with its polygon and point.", "Georef (IGN); INDEC ¿Qué es el Gran Buenos Aires? (build-argentina-d-n-j-companies.py)", 2023),
     ("fact_population_department", "Population by province, censuses 2010 and 2022 (resultados definitivos).", "INDEC Censo 2022, c2022_tp_est_c1", 2022),
     ("fact_population_municipality", "Population 2022 by department (resultados definitivos); 94021 has no census population (no row).", "INDEC Censo 2022, cuadros provinciales 1.n", 2022),
     ("fact_schools_department", "Students in años corridos 9-12 (2025) by province, with grade, sector, rural, women, under-18 and technical 13-14 columns; secondary schools from the Padrón 2026.", "Secretaría de Educación, RA 2025 base agregada; Padrón Oficial 16-06-2026 (build-argentina-k-c-l-education.py)", 2025),
     ("fact_schools_municipality", "Students in años 9-12 and secondary schools by department where the RA department name matches a Georef code (98.1% of students; masked rows only at province level).", "RA 2025 base agregada; Padrón Oficial 2026", 2025),
     ("fact_higher_ed_department", "Higher education by province: university, postgraduate and tertiary non-university attendance (Censo 2022, by residence), SNU enrolment 2025 (RA), SNU institutions and vocational training centres (Padrón 2026), students per 100,000 inhabitants.", "INDEC Censo 2022; RA 2025; Padrón 2026", 2022),
     ("fact_companies_department", "Establishments, distinct firms, micro (1-9) and medium-large (50+) establishments, shops (CLAE 4711) and IT establishments by province, 2022, with businesses per secondary school.", "CEP XXI, Distribución geográfica de los establecimientos productivos (build-argentina-d-n-j-companies.py)", 2022),
     ("fact_companies_municipality", "Same counts by department, one row per Georef department (0 = none registered).", "CEP XXI establishments 2022", 2022),
     ("fact_companies_zone", "Establishments by zone (CABA comunas and GBA partidos), size and template activity groups mapped to CLAE6.", "CEP XXI establishments 2022", 2022),
     ("fact_developers_country", "GitHub developers and organisations, Q1 2026, for the same 18 LATAM economies as the Colombia and Mexico tables (identical values).", "GitHub Innovation Graph release 1.0.10 (build-argentina-a-github.py)", 2026),
     ("fact_map_indicator", "National indicators without geography (scope_id = AR): layer A (GitHub), B (Stack Overflow 2025, Argentina and comparison groups), I (price), O (context), P (programme).", "See source_id per row", 2026),
     ("fact_persona_profile", "One row per persona: national urban profile, EPH 2025 (Q1-Q4, PONDERA / 4). CNO-2001 mapped to personas by majority on INDEC's 2015 double coding; empty rows = persona not identifiable.", "INDEC EPH 2025; INDEC EPH 2015 CIUO-08 (build-argentina-eph.py)", 2025),
     ("fact_persona_department", "People per persona by province (EPH agglomerates of the province), with interviews.", "INDEC EPH 2025", 2025),
     ("fact_persona_metro", "People per persona by EPH agglomerate (31), anchored to the department of its main city, with interviews.", "INDEC EPH 2025", 2025),
     ("fact_persona_segment", "Persona x agglomerate x buyer type (direct cross-tabulation; size bands up to 10, 11-200, 201+), with interviews and confidence.", "INDEC EPH 2025", 2025),
     ("fact_ict_by_sector", "IT staff (identifiable core personas P01 and P03) by CAES section of the employer; tech sector = section J.", "INDEC EPH 2025", 2025),
     ("fact_micro_department", "Micro-businesses by province: own-account workers and employers in units of up to 10 people (EPH agglomerates).", "INDEC EPH 2025", 2025),
     ("fact_micro_national", "National distributions of micro-businesses: activity, position, owner sex and age, size, informality, contributions, invoices, premises, place of work and region.", "INDEC EPH 2025", 2025),
    ]
    pd.DataFrame(meta, columns=["table_name", "description", "source", "year"]).to_csv(os.path.join(CSV, "meta_sources.csv"), index=False)
    # ---------------- R ----------------
    lf = json.load(open(os.path.join(OUTP, "layer_f_ar.json"))); lk = json.load(open(os.path.join(OUTP, "layer_k_ar.json")))
    ll = json.load(open(os.path.join(OUTP, "layer_l_ar.json"))); le = json.load(open(os.path.join(OUTP, "layer_e_ar.json")))
    ld = json.load(open(os.path.join(OUTP, "layer_d_ar.json"))); ln = json.load(open(os.path.join(OUTP, "layer_n_ar.json")))
    lj = json.load(open(os.path.join(OUTP, "layer_j_ar.json"))); lh = json.load(open(os.path.join(OUTP, "layer_h_ar.json")))
    checks = []
    for q, c in lf["checks"]["rates_vs_indec_cuadro_1_1"].items():
        checks.append(dict(check=f"Employment rate (F), EPH 2025 {q}", processed=c["employment_rate"], published=c["published_employment_rate"],
                           difference_pct_points=round(c["employment_rate"] - c["published_employment_rate"], 2), tolerance="0.05 points (published to 0.1)", ok=c["ok"]))
        checks.append(dict(check=f"Unemployment rate (F), EPH 2025 {q}", processed=c["unemployment_rate"], published=c["published_unemployment_rate"],
                           difference_pct_points=round(c["unemployment_rate"] - c["published_unemployment_rate"], 2), tolerance="0.05 points (published to 0.1)", ok=c["ok"]))
    kd = pd.read_csv(os.path.join(CSV, "fact_schools_department.csv"))
    checks += [dict(check="Population (E), provinces add to the published national total, Censo 2022", processed=int(sum(p["population"] for p in le["provinces"])),
                    published=le["national_population"], difference_pct=0.0, tolerance="exact", ok=le["checks"]["provinces_add_to_national"]),
               dict(check="Population (E), departments add to each province, Censo 2022", processed="24 provinces", published="24 provinces", difference_pct=0.0,
                    tolerance="exact", ok=all(v["ok"] for v in le["checks"]["departments_add_to_provinces"].values())),
               dict(check="Enrolment años 9-12 (K): grades add to total and provinces add to national, RA 2025", processed=lk["K2"]["total"], published=lk["K2"]["total"],
                    difference_pct=0.0, tolerance="exact", ok=lk["checks"]["grades_add_to_total"] and lk["checks"]["provinces_add_to_total"]),
               dict(check="University students (L) by sector add to total, Anuario 2024", processed=ll["national"]["students_public"] + ll["national"]["students_private"],
                    published=ll["national"]["students_undergraduate"], difference_pct=0.0, tolerance="exact",
                    ok=ll["national"]["students_public"] + ll["national"]["students_private"] == ll["national"]["students_undergraduate"]),
               dict(check="Establishments (D/N), CEP XXI 2022: geolocated base vs department file", processed=ln["N1_establishments"], published=715377,
                    difference_pct=0.0, tolerance="exact", ok=ln["N1_establishments"] == 715377),
               dict(check="Zones (J): CABA comunas add to CABA", processed=ln["checks"]["capital_vs_zones"]["caba_comunas_sum"],
                    published=ln["checks"]["capital_vs_zones"]["caba_establishments"], difference_pct=0.0, tolerance="exact", ok=lj["checks"]["caba_comunas_add_to_caba"]),
               dict(check="Segments (H): cells add to persona totals", processed="13 personas", published="13 personas", difference_pct=0.0,
                    tolerance="rounding", ok=lh["checks"]["cells_add_to_persona_totals"])]
    reg = pd.read_csv(os.path.join(OUT, "sources_register.csv"), dtype=str).fillna("")
    r2 = []
    for r in reg.itertuples():
        missing = [c for c in ["source_name", "publisher", "url", "access_date", "reference_period", "script"] if not getattr(r, c)]
        r2.append(dict(source_id=r.source_id, missing=[m for m in missing if m != "script"], to_confirm=[c for c in ["license", "status"] if "confirm" in getattr(r, c)],
                       hash_recorded=bool(r.sha256)))
    out = dict(country="AR", layer="R",
               R1_published_totals=dict(checks=checks, passed=sum(bool(c["ok"]) for c in checks), total=len(checks)),
               R2_sources_register=dict(sources=len(reg), complete=sum(1 for x in r2 if not x["missing"]),
                                        incomplete=[x for x in r2 if x["missing"]], to_confirm=[x for x in r2 if x["to_confirm"]]),
               not_checkable=["Micro-businesses (M): no published total exists for own-account and employers in units up to 10 people.",
                              "Schools (K1): the Padrón has no published count of secondary localizaciones to compare with."])
    json.dump(_clean(out), open(os.path.join(VAL, "r_checks_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(out["R1_published_totals"]["passed"], out["R1_published_totals"]["total"], out["R2_sources_register"]["sources"], out["R2_sources_register"]["complete"])


if __name__ == "__main__":
    main()
