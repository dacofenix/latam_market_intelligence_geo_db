#!/usr/bin/env python3
"""Layers I (price against income), O (country context) and P (high-school programme) for Argentina.
Every figure is read from a delivered file or quoted from the official source named in its source_id; the quotes were
checked against the document (sources_register.csv). Run after the EPH (F), education (K) and companies (N) builds.
Usage: build-argentina-i-o-p.py <raw_dir> <research-argentina_dir>
"""
import sys, os, json, csv
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
LIM_I = "El precio es un escenario no aprobado (USD 25 / USD 250), mostrado con su tipo de cambio y fecha; no es una recomendación."

# Salario mínimo, vital y móvil 2025 (pesos al mes, trabajadores mensualizados de jornada completa)
SMVM_2025 = {1: 286711, 2: 292446, 3: 296832,                       # Res. CNEPYSMVyM 17/2024 (BO 26-12-2024)
             4: 302600, 5: 308200, 6: 313400, 7: 317800, 8: 322000,  # Res. 5/2025 (08-05-2025)
             9: 322000, 10: 322000,                                   # no new amount between Res. 5/2025 and Res. 9/2025
             11: 328400, 12: 334800}                                  # Res. 9/2025 (BO 03-12-2025)


def row(layer, mid, ind, value, unit, period, status, src, method="", lim="", num="", den="", comp="", group="", persona="", cat=""):
    return dict(layer=layer, metric_id=mid, scope_type="country", scope_id="AR", group_id=group, persona_id=persona,
                indicator=ind, category=cat, value="" if value is None else value, unit=unit, period=period,
                comparison_period=comp, numerator=num, denominator=den, status=status, source_id=src, method=method,
                limitations=lim)


def main():
    rows = []
    # ---------------- I ----------------
    x = pd.read_excel(os.path.join(RAW, "context", "ar_raw_bcra_com3500.xls"), sheet_name=0, header=None)
    x = x[[2, 3]].dropna(); x.columns = ["date", "rate"]
    x = x[pd.to_datetime(x.date, errors="coerce").notna()]
    x["date"] = pd.to_datetime(x.date); x["rate"] = pd.to_numeric(x.rate, errors="coerce")
    x = x.drop_duplicates("date")
    y25 = x[x.date.dt.year == 2025]
    fx = round(y25.rate.mean(), 4); fx_dec = round(y25[y25.date.dt.month == 12].rate.mean(), 4)
    fx_last = float(y25.sort_values("date").rate.iloc[-1])
    plan = round(25 * fx, 2); team = round(250 * fx, 2); plan_dec = round(25 * fx_dec, 2)
    smvm_avg = round(sum(SMVM_2025.values()) / 12, 2); smvm_dec = SMVM_2025[12]
    prof = pd.read_csv(os.path.join(CSV, "fact_persona_profile.csv"))
    rows += [row("I", "I1_a3500_2025_average", "Tipo de cambio de referencia Com. A 3500, promedio 2025", fx, "ARS por USD", "2025", "verified",
                 "BCRA_A3500", f"mean of {len(y25)} daily values, 2025", LIM_I),
             row("I", "I1_a3500_2025_december_average", "Tipo de cambio de referencia Com. A 3500, promedio de diciembre de 2025", fx_dec,
                 "ARS por USD", "2025", "verified", "BCRA_A3500", "mean of daily values, December 2025", LIM_I),
             row("I", "I1_plan_individual_ars", "Plan individual (USD 25) en pesos", plan, "ARS al mes", "2025", "verified", "BCRA_A3500",
                 "USD 25 × 2025 average A3500", LIM_I, num=25),
             row("I", "I1_plan_individual_ars_december", "Plan individual (USD 25) en pesos, al promedio de diciembre de 2025", plan_dec,
                 "ARS al mes", "2025-12", "verified", "BCRA_A3500", "USD 25 × December 2025 average A3500",
                 "Con inflación y devaluación durante 2025, el promedio anual y el de diciembre difieren; ver ambos. " + LIM_I, num=25),
             row("I", "I1_plan_team_ars", "Plan de equipo (USD 250) en pesos", team, "ARS", "2025", "verified", "BCRA_A3500",
                 "USD 250 × 2025 average A3500", LIM_I, num=250),
             row("I", "I3_min_wage_monthly_2025_average", "Salario mínimo, vital y móvil, promedio mensual 2025", smvm_avg, "ARS al mes",
                 "2025", "derived", "CNEPYSMVYM_RES_2024_17_2025_5_2025_9", "mean of the 12 monthly amounts in force in 2025",
                 "Septiembre y octubre de 2025: rige el monto de agosto (322.000), sin resolución nueva hasta la 9/2025. " + LIM_I),
             row("I", "I3_plan_pct_min_wage", "Plan individual como % del salario mínimo mensual (promedio 2025)",
                 round(100 * plan / smvm_avg, 2), "porcentaje", "2025", "verified", "CNEPYSMVYM_RES_2024_17_2025_5_2025_9",
                 "I1 ÷ average monthly minimum wage 2025", LIM_I, num=plan, den=smvm_avg),
             row("I", "I3_plan_pct_min_wage_december", "Plan individual (diciembre) como % del salario mínimo de diciembre de 2025",
                 round(100 * plan_dec / smvm_dec, 2), "porcentaje", "2025-12", "verified", "CNEPYSMVYM_RES_2024_17_2025_5_2025_9",
                 "I1 December ÷ minimum wage December 2025", LIM_I, num=plan_dec, den=smvm_dec)]
    dev = prof[prof.persona == "Software developers and analysts"].median_income_ars.iloc[0]
    rows.append(row("I", "I3_plan_pct_developer_income", "Plan individual como % del ingreso mensual mediano de los desarrolladores",
                    round(100 * plan / dev, 2), "porcentaje", "2025", "verified", "INDEC_EPH_2025",
                    "I1 ÷ persona P01 median income (EPH 2025)", LIM_I, num=plan, den=dev))
    for i, r in enumerate(prof.itertuples(), 1):
        v = None if pd.isna(r.median_income_ars) else round(100 * plan / r.median_income_ars, 2)
        rows.append(row("I", f"I2_plan_pct_income_{i:02d}", f"Plan individual como % del ingreso mediano: {r.persona}", v, "porcentaje",
                        "2025", "verified" if v is not None else "not_available", "INDEC_EPH_2025", "I1 ÷ F8 median monthly labour income",
                        LIM_I if v is not None else "Persona no identificable en la CNO-2001 (D-AR-09). " + LIM_I,
                        num=plan, den="" if v is None else r.median_income_ars))
    # ---------------- O ----------------
    imf = json.load(open(os.path.join(RAW, "context", "ar_raw_imf_datamapper_NGDPDPC_downloaded_2026-11-18.json")))["values"]["NGDPDPC"]
    gdp = imf["ARG"]["2025"]
    sc = pd.read_csv(os.path.join(RAW, "context", "ar_raw_statcounter_desktop_mobile_tablet_AR_yearly_2025.csv"))
    sc = dict(zip(sc.iloc[:, 0], sc.iloc[:, 1]))
    wb = json.load(open(os.path.join(RAW, "context", "ar_raw_worldbank_api_findex_2026-11-18.json")))
    acc = [v for v in wb["FX.OWN.TOTL.ZS"] if v[0] == "AR" and v[1] == "2024"][0][2]
    acc_f = [v for v in wb["FX.OWN.TOTL.FE.ZS"] if v[0] == "AR" and v[1] == "2024"][0][2]
    q = "quoted from the source document"
    rows += [row("O", "O1_gdp_per_capita", "PIB per cápita (FMI, WEO)", round(gdp, 1), "USD", "2025", "verified", "IMF_WEO_DATAMAPPER", "",
                 f"FMI, World Economic Outlook (octubre de 2026), indicador NGDPDPC de DataMapper (USD corrientes), consultado el 2026-11-18. "
                 f"En el mismo archivo: México {imf['MEX']['2025']:,.1f}, Colombia {imf['COL']['2025']:,.1f}, Perú {imf['PER']['2025']:,.1f}."),
             row("O", "O1_min_wage_monthly_december_2025", "Salario mínimo, vital y móvil, diciembre de 2025", smvm_dec, "ARS al mes", "2025-12",
                 "verified", "CNEPYSMVYM_RES_2024_17_2025_5_2025_9", q, "Res. 9/2025 del Consejo Nacional del Empleo, la Productividad y el SMVM: "
                 "334.800 desde el 1-12-2025; 341.000 desde el 1-1-2026 y 376.600 desde el 1-8-2026."),
             row("O", "O1_min_wage_monthly_2025_average", "Salario mínimo, vital y móvil, promedio mensual 2025", smvm_avg, "ARS al mes", "2025",
                 "derived", "CNEPYSMVYM_RES_2024_17_2025_5_2025_9", "derived", "Promedio de los 12 montos mensuales vigentes en 2025."),
             row("O", "O1_developer_median_income", "Ingreso laboral mensual mediano de los desarrolladores (persona P01)", dev, "ARS al mes",
                 "2025", "derived", "INDEC_EPH_2025", "derived", "Mediana ponderada (PONDIIO) de P21 de la EPH 2025 entre los desarrolladores "
                 "que reportan ingreso; pesos corrientes de cada trimestre (fact_persona_profile)."),
             row("O", "O2_account_ownership_findex", "Población de 15 años o más con cuenta (Global Findex 2025)", round(acc, 1), "porcentaje",
                 "2024", "verified", "WB_FINDEX_2025", "World Bank API FX.OWN.TOTL.ZS", f"Encuesta 2024 publicada como Findex 2025; mujeres {acc_f:.1f} %. "
                 "Cuenta en institución financiera o proveedor de dinero móvil."),
             row("O", "O2_adults_with_account_bcra", "Personas adultas con al menos una cuenta (bancaria o de pago)", 37.8, "millones de personas",
                 "diciembre de 2025", "verified", "BCRA_INCLUSION_2026_04", q, "BCRA, Informe de Inclusión Financiera (abril de 2026): 35,8 millones "
                 "con cuenta bancaria y 30,1 millones con cuenta de pago."),
             row("O", "O2_credit_card_holders", "Personas con financiamiento de tarjetas de crédito (deudores)", 14.8, "millones de personas",
                 "diciembre de 2025", "verified", "BCRA_INCLUSION_2026_04", q, "Personas deudoras de tarjetas de crédito según el informe; no es "
                 "la tenencia de tarjetas."),
             row("O", "O2_instant_transfers_push", "Transferencias inmediatas (push) en pesos", 753, "millones de operaciones", "diciembre de 2025",
                 "verified", "BCRA_PAGOS_MINORISTAS_2025_12", q, "Por $ 88,7 billones en el mes."),
             row("O", "O2_payments_by_transfer_pct", "Pagos con transferencia (PCT, Transferencias 3.0) interoperables", 96.4,
                 "millones de operaciones", "diciembre de 2025", "verified", "BCRA_PAGOS_MINORISTAS_2025_12", q,
                 "+44 % interanual; 98,6 % iniciados con QR (95 millones). 84 billeteras digitales interoperables registradas."),
             row("O", "O3_vat_rate", "Tasa general de IVA, incluidos los servicios digitales del exterior", 21, "porcentaje", "vigente en 2026",
                 "verified", "LEY_IVA_TO1997", q, "Ley de IVA art. 28 (alícuota del 21 %); art. 1 inc. e) grava los servicios digitales prestados "
                 "por sujetos del exterior (incorporado por la Ley 27.430, art. 87); definición en art. 3 inc. e) ap. 21 subinc. m)."),
             row("O", "O3_digital_services_collection", "IVA de servicios digitales del exterior: mecanismo de cobro", None, "", "vigente en 2026",
                 "verified", "DECRETO_354_2018", q, "Decreto 354/2018 (BO 24-04-2018): el impuesto está a cargo del prestatario (comprador); "
                 "lo percibe el intermediario residente que interviene en el pago (por ejemplo la tarjeta), con listados de prestadores de AFIP (hoy ARCA)."),
             row("O", "O4_data_protection_authority", "Protección de datos: ley y autoridad", None, "", "vigente en 2026", "verified",
                 "LEY_25326; DECRETO_746_2017", q, "Ley 25.326 de Protección de los Datos Personales (sancionada el 04-10-2000). Autoridad de "
                 "aplicación: Agencia de Acceso a la Información Pública (AAIP), por el Decreto 746/2017 (arts. 11 y 13)."),
             row("O", "O4_consent", "Protección de datos: consentimiento", None, "", "vigente en 2026", "verified", "LEY_25326", q,
                 "Art. 5: el tratamiento es ilícito sin consentimiento libre, expreso e informado, por escrito u otro medio equiparable; "
                 "excepciones en el art. 5 inc. 2. La ley no tiene un artículo sobre menores (ver P5)."),
             row("O", "O5_ai_policy", "Política nacional de IA", None, "", "2026", "verified", "DISPOSICION_2_2023_SSTI", q,
                 "No hay una ley nacional de IA. Disposición 2/2023 de la Subsecretaría de Tecnologías de la Información (BO 02-06-2023): "
                 "'Recomendaciones para una Inteligencia Artificial Fiable', de carácter recomendatorio para proyectos del sector público. "
                 "No hay un monto de financiamiento público asociado."),
             row("O", "O6_internet_users_pct", "Personas de 4 años o más que usaron internet (31 aglomerados)", 89.7, "porcentaje",
                 "cuarto trimestre de 2024", "verified", "INDEC_TIC_2024Q4", q, "Último módulo TIC de la EPH publicado (mayo de 2025); "
                 "no hay edición del cuarto trimestre de 2025 en el sitio de INDEC al 2026-11-18."),
             row("O", "O6_households_internet_pct", "Hogares con acceso a internet (31 aglomerados)", 93.7, "porcentaje", "cuarto trimestre de 2024",
                 "verified", "INDEC_TIC_2024Q4", q),
             row("O", "O6_computer_use_pct", "Personas de 4 años o más que usaron computadora (31 aglomerados)", 37.1, "porcentaje",
                 "cuarto trimestre de 2024", "verified", "INDEC_TIC_2024Q4", q, "Hogares con computadora: 60,3 %."),
             row("O", "O6_mobile_use_pct", "Personas de 4 años o más que usaron teléfono celular (31 aglomerados)", 90.5, "porcentaje",
                 "cuarto trimestre de 2024", "verified", "INDEC_TIC_2024Q4", q),
             row("O", "O6_internet_users_datareportal", "Usuarios de internet (DataReportal)", 41.6, "millones de personas", "fin de 2025",
                 "verified", "DATAREPORTAL_DIGITAL_2026_AR", q, "Estimación de Kepios: 90,6 % de penetración; población de 45,9 millones."),
             row("O", "O6_fixed_download_speed", "Velocidad mediana de descarga, internet fijo (Ookla)", 99.62, "Mbps", "fin de 2025", "verified",
                 "DATAREPORTAL_DIGITAL_2026_AR", q, "DataReportal Digital 2026 Argentina, con datos de Ookla."),
             row("O", "O6_mobile_download_speed", "Velocidad mediana de descarga, internet móvil (Ookla)", 60.40, "Mbps", "fin de 2025", "verified",
                 "DATAREPORTAL_DIGITAL_2026_AR", q, "DataReportal Digital 2026 Argentina, con datos de Ookla."),
             row("O", "O6_desktop_share", "Participación de computadoras de escritorio en el tráfico web (StatCounter)", sc.get("Desktop"),
                 "porcentaje", "2025", "verified", "STATCOUNTER_2025_AR", "", f"StatCounter, año 2025: móvil {sc.get('Mobile')} %, tableta {sc.get('Tablet')} %."),
             row("O", "O7_pestel", "Resumen PESTEL", None, "", "", "pending", "O1-O6", "", "Una línea por factor, redactada en el deck a partir de O1-O6.")]
    # ---------------- P ----------------
    K = json.load(open(os.path.join(OUTP, "layer_k_ar.json")))
    N = json.load(open(os.path.join(OUTP, "layer_n_ar.json")))
    schools = K["K1"]["schools"]
    rows += [row("P", "P1_schools", "Escuelas con oferta de secundaria común (localizaciones)", schools, "escuelas", "2025 / 2026", "verified",
                 "MEN_PADRON_2026", "", "Capa K1: Padrón Oficial de Establecimientos (16-06-2026), Cueanexo con secundario común o INET."),
             row("P", "P1_mean_students_per_school", "Promedio de alumnos de los años 9 a 12 por escuela", K["K5"]["mean_students_per_school"],
                 "alumnos", "2025", "derived", "MEN_RA_2025", "K2 total ÷ K1",
                 "Promedio, no mediana: las bases abiertas del RA desde 2024 están agregadas por departamento (D-AR-04)."),
             row("P", "P1_students_reached_cap100", "Alumnos alcanzables con un tope de 100 por escuela", None, "alumnos", "2025", "not_available",
                 "MEN_RA_2025", "", "Requiere matrícula por escuela, que no se publica desde 2024 (K6)."),
             row("P", "P1_paid_users_at_10pct", "Usuarios de pago con la conversión supuesta", None, "usuarios", "2025", "not_available",
                 "MEN_RA_2025", "", "Depende de P1 alcanzables; la conversión del 10 % es un supuesto de la plantilla, no una tasa medida."),
             row("P", "P2_sponsored_team_plans_usd", "Planes de equipo patrocinados al año (escuelas × USD 250)", schools * 250, "USD", "2025 / 2026",
                 "scenario", "MEN_PADRON_2026", "", "USD 250 por escuela es un escenario de precio no aprobado."),
             row("P", "P2_sponsored_team_plans_ars", "Planes de equipo patrocinados al año, en pesos", round(schools * 250 * fx), "ARS", "2025 / 2026",
                 "scenario", "BCRA_A3500", "", f"Al tipo de cambio A3500 promedio de 2025, {fx:,.2f} ARS por USD."),
             row("P", "P3_businesses_per_school", "Empresas privadas empleadoras por escuela", N["N4_businesses_per_school_national"],
                 "empresas por escuela", "2022 / 2026", "verified", "CEP_XXI_ESTABLECIMIENTOS_2022",
                 "", "N1 (CEP XXI 2022, empleadores registrados) ÷ K1 (Padrón 2026); periodos distintos, como indica la plantilla."),
             row("P", "P4_donation_incentive", "Incentivo fiscal a donaciones (educación)", 5, "porcentaje de la ganancia neta (tope)", "vigente en 2026",
                 "to_confirm_with_legal", "LEY_GANANCIAS_TO2019", "", "Ley de Impuesto a las Ganancias (t.o. 2019) art. 85 inc. c) (antes art. 81 "
                 "inc. c): donaciones al Estado y a entidades exentas del art. 26 inc. e) y f) deducibles hasta el 5 % de la ganancia neta del "
                 "ejercicio. Confirmar artículo y tope con el área legal."),
             row("P", "P5_minors_data", "Reglas para datos de menores", None, "", "vigente en 2026", "verified", "LEY_25326; AAIP_RES_4_2019",
                 "", "La Ley 25.326 no tiene un artículo sobre menores. AAIP Res. 4/2019, criterio 5: el menor con madurez suficiente puede "
                 "consentir (autonomía progresiva, CCyC arts. 26 y 639); si no, consienten padres o tutores; el responsable debe hacer esfuerzos "
                 "razonables para verificarlo (confirmar con el área legal).")]
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUTP, "_iop_rows_ar.csv"), index=False)
    li = dict(country="AR", layer="I", source_id="BCRA_A3500; CNEPYSMVYM_RES_2024_17_2025_5_2025_9; INDEC_EPH_2025",
              exchange_rate=dict(series="Com. A 3500 (mayorista)", average_2025=fx, average_december_2025=fx_dec, last_2025=fx_last,
                                 business_days=int(len(y25))),
              plans=dict(individual_usd=25, team_usd=250, individual_ars=plan, team_ars=team, individual_ars_december=plan_dec),
              minimum_wage_2025=SMVM_2025, minimum_wage_2025_average=smvm_avg,
              rows=[r for r in rows if r["layer"] == "I"])
    lo = dict(country="AR", layer="O", rows=[r for r in rows if r["layer"] == "O"])
    lp = dict(country="AR", layer="P", rows=[r for r in rows if r["layer"] == "P"],
              note="Built from K (schools), N (businesses) and I (exchange rate); conversion stated as an assumption, never a measured rate.")
    for n, d in [("i", li), ("o", lo), ("p", lp)]:
        json.dump(_clean(d), open(os.path.join(OUTP, f"layer_{n}_ar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(fx, fx_dec, plan, team, smvm_avg, gdp, acc, sc)


if __name__ == "__main__":
    main()
