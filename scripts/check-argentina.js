'use strict';
// Argentina acceptance checks on data/argentina/geodb/csv (no database): the file-adapter counterpart of
// lib/acceptance.js, like scripts/check-mexico.js. Codes stay strings; every fact table must join to
// geo_department (provinces) / geo_municipality (departments); every table needs a meta_sources row.
// Usage: node scripts/check-argentina.js   (exit 1 when any check fails)
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const ROOT = path.join(__dirname, '..', 'data', 'argentina');
const CSV_DIR = path.join(ROOT, 'geodb', 'csv');
// Georef includes the Antarctic sector and the South Atlantic islands, so the box reaches 90°S and 25°W.
const AR_BBOX = { south: -90.01, north: -21, west: -74.1, east: -24.9 };
// rule_axis_order: Comuna 1 (CABA) must read lat ≈ -34.61, lon ≈ -58.37.
const AXIS = { code: '02007', lat: -34.61, lon: -58.37, tol: 0.05 };

const read = (table) => {
  const file = path.join(CSV_DIR, `${table}.csv`);
  if (!fs.existsSync(file)) return null;
  const text = fs.readFileSync(file, 'utf8');
  return { bom: text.charCodeAt(0) === 0xfeff, rows: parse(text, { columns: true, skip_empty_lines: true, bom: true }) };
};
const readJson = (rel) => {
  const file = path.join(ROOT, rel);
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
};

const checks = [];
const check = (id, label, expected, actual, ok = expected === actual) => checks.push({ id, label, expected, actual, ok });
const n = (v) => Number(v);
const sum = (rows, k) => rows.reduce((s, r) => s + (r[k] === '' ? 0 : Number(r[k])), 0);

const tables = fs.readdirSync(CSV_DIR).filter((f) => f.endsWith('.csv')).map((f) => f.slice(0, -4));
const data = Object.fromEntries(tables.map((t) => [t, read(t)]));
const prov = data.geo_department ? data.geo_department.rows : [];
const dept = data.geo_municipality ? data.geo_municipality.rows : [];
const provCodes = new Set(prov.map((r) => r.department_code));
const deptCodes = new Set(dept.map((r) => r.municipality_code));

// Layer Q: 24 jurisdictions (23 provinces + CABA) and 529 departments, partidos and comunas.
check('provinces', 'Provincias (23 + CABA, geo_department)', 24, prov.length);
check('provinces_unique', 'Códigos de provincia únicos de 2 dígitos', prov.length, prov.filter((r) => /^\d{2}$/.test(r.department_code)).length,
  provCodes.size === prov.length && prov.every((r) => /^\d{2}$/.test(r.department_code)));
check('departments', 'Departamentos, partidos y comunas (Georef)', 529, dept.length);
check('departments_unique', 'Códigos de departamento únicos de 5 dígitos (provincia + departamento)', dept.length,
  dept.filter((r) => /^\d{5}$/.test(r.municipality_code) && r.municipality_code.startsWith(r.department_code)).length,
  deptCodes.size === dept.length && dept.every((r) => /^\d{5}$/.test(r.municipality_code) && r.municipality_code.startsWith(r.department_code)));
check('caba_comunas', 'CABA: 15 comunas como departamentos', 15, dept.filter((r) => r.department_code === '02').length);
const inBox = (r) => n(r.lat) > AR_BBOX.south && n(r.lat) < AR_BBOX.north && n(r.lon) > AR_BBOX.west && n(r.lon) < AR_BBOX.east;
check('department_points', 'Departamentos con punto dentro de Argentina', dept.length, dept.filter(inBox).length);
const wktOk = dept.filter((r) => {
  const m = /^POINT\((-?[\d.]+) (-?[\d.]+)\)$/.exec(r.wkt || '');
  return m && Math.abs(n(m[1]) - n(r.lon)) < 1e-5 && Math.abs(n(m[2]) - n(r.lat)) < 1e-5;
}).length;
check('department_wkt', 'WKT en orden lon lat, igual a lat/lon', dept.length, wktOk);
const axis = dept.find((r) => r.municipality_code === AXIS.code);
check('axis_order', `Punto de ${AXIS.code} en lat ${AXIS.lat} / lon ${AXIS.lon}`, true,
  !!axis && Math.abs(n(axis.lat) - AXIS.lat) < AXIS.tol && Math.abs(n(axis.lon) - AXIS.lon) < AXIS.tol);

const validRing = (ring) => Array.isArray(ring) && ring.length >= 4
  && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1]
  && ring.every(([x, y]) => x > AR_BBOX.west && x < AR_BBOX.east && y > AR_BBOX.south && y < AR_BBOX.north);
const validShape = (text) => {
  try {
    const g = JSON.parse(text);
    return g.type === 'MultiPolygon' && g.coordinates.length > 0 && g.coordinates.every((poly) => poly.length > 0 && poly.every(validRing));
  } catch (_) { return false; }
};
for (const [table, codeCol, codes] of [['geo_department_shape', 'department_code', provCodes], ['geo_municipality_shape', 'municipality_code', deptCodes]]) {
  if (!data[table]) continue;
  const rows = data[table].rows;
  const shapeCodes = new Set(rows.map((r) => r[codeCol]));
  check(`${table}_coverage`, `${table}: un polígono por código`, codes.size, rows.length,
    rows.length === codes.size && shapeCodes.size === rows.length && [...codes].every((c) => shapeCodes.has(c)));
  check(`${table}_valid`, `${table}: polígonos WGS84 válidos y cerrados`, rows.length, rows.filter((r) => validShape(r.geojson)).length);
}
// Display rule D-AR-15: what remains north of 60°S must cover every province and every department except Antártida (94028).
const north60 = (text) => JSON.parse(text).coordinates.some((poly) => poly[0].some(([, lat]) => lat > -60));
if (data.geo_department_shape && data.geo_municipality_shape) {
  check('display_provinces', 'Mapa web: las 24 provincias quedan dibujadas al quitar el sector antártico', 24,
    data.geo_department_shape.rows.filter((r) => north60(r.geojson)).length);
  const hidden = data.geo_municipality_shape.rows.filter((r) => !north60(r.geojson)).map((r) => r.municipality_code);
  check('display_departments', 'Mapa web: solo Antártida Argentina (94028) queda fuera del mapa', '94028', hidden.join(','));
}

// Layers D and N (CEP XXI 2022): published total, parts, provinces vs departments.
const PUBLISHED = { cep_establishments_2022: 715377 }; // CEP XXI department file, 2022 rows, exact
if (data.fact_companies_municipality && data.fact_companies_department) {
  const rows = data.fact_companies_municipality.rows;
  const provRows = data.fact_companies_department.rows;
  check('cep_total', 'CEP XXI 2022: establecimientos = total publicado (exacto)', PUBLISHED.cep_establishments_2022, sum(rows, 'establishments'));
  check('cep_total_provinces', 'CEP XXI 2022: provincias suman el mismo total', PUBLISHED.cep_establishments_2022, sum(provRows, 'establishments'));
  check('cep_rows', 'fact_companies_municipality: una fila por departamento', dept.length, rows.length);
  check('cep_province_rows', 'fact_companies_department: una fila por provincia', 24, provRows.length);
  const byProv = new Map();
  for (const r of rows) byProv.set(r.department_code, (byProv.get(r.department_code) || 0) + n(r.establishments));
  check('cep_departments_add_up', 'Establecimientos: los departamentos suman su provincia', 24,
    provRows.filter((r) => byProv.get(r.department_code) === n(r.establishments)).length);
  check('cep_parts', 'Empresas, micro, medianas, almacenes y TI ≤ establecimientos; TI = suma de sus códigos', rows.length + provRows.length,
    rows.concat(provRows).filter((r) => n(r.businesses) <= n(r.establishments) && n(r.micro_1_9) + n(r.medium_large_50_plus) <= n(r.establishments)
      && n(r.shops_4711) <= n(r.establishments) && n(r.it_firms) <= n(r.it_establishments)
      && n(r.it_establishments) === n(r.software_620100) + n(r.it_620200_620300_620900) + n(r.it_631110_631120_631190_631200)).length);
}

// Layer J zones: 15 CABA comunas + 24 GBA partidos, valid polygons, joins, each zone equals its department.
if (data.geo_zone && data.fact_companies_zone) {
  const zones = data.geo_zone.rows;
  const facts = data.fact_companies_zone.rows;
  const zoneIds = new Set(zones.map((z) => z.zone_id));
  const est = new Map((data.fact_companies_municipality ? data.fact_companies_municipality.rows : []).map((r) => [r.municipality_code, n(r.establishments)]));
  check('zones', 'Zonas J: 15 comunas de CABA + 24 partidos del GBA', 39, zones.length,
    zones.length === 39 && zoneIds.size === 39 && zones.filter((z) => z.zone_id.startsWith('CABA-')).length === 15 && zones.filter((z) => z.zone_id.startsWith('GBA-')).length === 24);
  check('zones_valid', 'geo_zone: polígonos WGS84 válidos y cerrados', zones.length, zones.filter((z) => validShape(z.geojson)).length);
  check('zones_join', 'fact_companies_zone.zone_id une con geo_zone', 0, facts.filter((f) => !zoneIds.has(f.zone_id)).length);
  const zoneDept = new Map(zones.map((z) => [z.zone_id, z.municipality_code]));
  check('zones_equal_department', 'Establecimientos por zona = establecimientos de su departamento', facts.length,
    facts.filter((f) => n(f.companies_total) === est.get(zoneDept.get(f.zone_id))).length);
  const parts = ['businesses', 'micro', 'medium_large', 'software_it', 'design', 'accounting_audit', 'management_consulting',
    'research_market_studies', 'higher_education_training', 'shops_4711', 'private_schools'];
  check('zones_parts', 'Cada indicador de zona ≤ total de la zona; micro + medianas/grandes ≤ total', facts.length,
    facts.filter((f) => parts.every((k) => n(f[k]) <= n(f.companies_total)) && n(f.micro) + n(f.medium_large) <= n(f.companies_total)).length);
  const capital = data.fact_companies_department ? data.fact_companies_department.rows.find((r) => r.department_code === '02') : null;
  check('zones_caba_total', 'Las 15 comunas suman los establecimientos de CABA', capital && n(capital.establishments),
    sum(facts.filter((f) => f.zone_id.startsWith('CABA-')), 'companies_total'));
}

// National indicators (layers A, B, I, O, P): Peru's fact_map_indicator format, AR scope, nulls kept empty.
if (data.fact_map_indicator) {
  const rows = data.fact_map_indicator.rows;
  const a = rows.filter((r) => r.layer === 'A');
  const b = rows.filter((r) => r.layer === 'B');
  check('national_scope', 'fact_map_indicator: ámbito nacional AR en todas las filas', rows.length,
    rows.filter((r) => r.scope_type === 'country' && r.scope_id === 'AR').length);
  check('layer_a_rows', 'Capa A: 25 indicadores, todos con valor', 25, a.filter((r) => r.value !== '').length, a.length === 25 && a.every((r) => r.value !== ''));
  if (data.fact_developers_country) {
    const dev = data.fact_developers_country.rows.find((r) => r.iso2 === 'AR');
    const a1 = a.find((r) => r.metric_id === 'A1_developer_accounts');
    check('layer_a_benchmark', 'A1 = developers de fact_developers_country (AR)', dev && n(dev.developers), a1 && n(a1.value));
    check('developers_18', 'fact_developers_country: las 18 economías de la tabla de Colombia', 18, new Set(data.fact_developers_country.rows.map((r) => r.iso2)).size);
  }
  const proportionsOk = b.filter((r) => r.value === '' || (n(r.value) >= 0 && n(r.value) <= 1)).length;
  check('layer_b_proportions', 'Capa B: proporciones entre 0 y 1 o vacías (suprimidas)', b.length, proportionsOk, b.length > 0 && proportionsOk === b.length);
  check('layer_b_suppressed', 'Capa B: celdas suprimidas sin valor (nunca cero)', 0, b.filter((r) => /suppress=suppressed/.test(r.limitations) && r.value !== '').length);
  check('layer_b_argentina', 'Capa B: 158 filas del grupo Argentina (todos los encuestados)', 158, b.filter((r) => r.metric_id.includes(':country:AR:all_respondents:')).length);
  const oRows = rows.filter((r) => r.layer === 'O');
  check('layer_o_verified', 'Capa O: datos verificados con valor o texto y fuente', oRows.filter((r) => r.status === 'verified').length,
    oRows.filter((r) => r.status === 'verified' && r.source_id && (r.value !== '' || r.limitations)).length);
  const pRows = rows.filter((r) => r.layer === 'P');
  const pv = (id) => n((pRows.find((r) => r.metric_id === id) || {}).value);
  const layerN = readJson('outputs/layer_n_ar.json');
  if (data.fact_schools_department && layerN) {
    const schools = sum(data.fact_schools_department.rows, 'schools');
    check('layer_p_schools', 'Capa P: escuelas = K1 (suma provincial)', schools, pv('P1_schools'));
    check('layer_p_per_school', 'Capa P: empresas por escuela = N1 ÷ K1', Math.round((layerN.N1_formal_businesses / schools) * 10) / 10, pv('P3_businesses_per_school'));
    check('layer_p_not_available', 'Capa P: alcance con tope de 100 vacío (sin matrícula por escuela), nunca cero', '',
      (pRows.find((r) => r.metric_id === 'P1_students_reached_cap100') || {}).value);
  }
  const iRows = rows.filter((r) => r.layer === 'I');
  const iv = (id) => n((iRows.find((r) => r.metric_id === id) || {}).value);
  check('layer_i_plans', 'Capa I: plan individual = USD 25 × A 3500 promedio 2025', Math.round(25 * iv('I1_a3500_2025_average') * 100) / 100,
    Math.round(iv('I1_plan_individual_ars') * 100) / 100);
}

// Layers F, G, H, M (EPH 2025): 13 personas, unidentifiable ones empty, parts add up, published rates (R1).
const PERSONA_NAMES = ['Software developers and analysts', 'Database, systems and network professionals', 'ICT technicians and user support', 'ICT managers'];
if (data.fact_persona_profile) {
  const profile = data.fact_persona_profile.rows;
  check('personas', 'Personas (13 personas, mismos nombres que Colombia)', 13, profile.length);
  const empty = profile.filter((p) => p.cno2001_codes === '');
  check('personas_unidentified', 'Personas sin código CNO-2001 (P02, P04, P05, P08, P09): ocupados vacíos, nunca cero', 5,
    empty.filter((p) => p.employed === '').length, empty.length === 5 && empty.every((p) => p.employed === ''));
  const total = new Map(profile.filter((p) => p.employed !== '').map((p) => [p.persona, n(p.employed)]));
  for (const t of ['fact_persona_department', 'fact_persona_metro', 'fact_persona_segment']) {
    if (!data[t]) continue;
    const sums = new Map(); const cells = new Map();
    for (const r of data[t].rows) {
      sums.set(r.persona, (sums.get(r.persona) || 0) + n(r.employed));
      cells.set(r.persona, (cells.get(r.persona) || 0) + 1);
    }
    const ok = [...total].filter(([p, v]) => sums.has(p) && Math.abs(sums.get(p) - v) <= cells.get(p)).length;
    check(`${t}_adds_up`, `${t}: las celdas de cada persona suman su total`, total.size, ok,
      ok === total.size && empty.every((p) => !sums.has(p.persona)));
  }
  const f = readJson('outputs/layer_f_ar.json');
  if (f) {
    const q = Object.values(f.checks.rates_vs_indec_cuadro_1_1);
    check('eph_rates', 'EPH 2025: tasas de empleo y desocupación por trimestre iguales a INDEC (Cuadro 1.1)', 4, q.filter((x) => x.ok).length);
  }
  if (data.fact_ict_by_sector) {
    const core = PERSONA_NAMES.reduce((s, p) => s + (total.get(p) || 0), 0);
    const g1 = sum(data.fact_ict_by_sector.rows, 'employed');
    check('g1_core', 'G1: personal TI por sector = suma de las personas núcleo identificables (P01, P03)', core, g1, Math.abs(core - g1) <= data.fact_ict_by_sector.rows.length);
  }
  const crossPath = path.join(ROOT, 'outputs', 'f_persona_crossref_ar.csv');
  if (fs.existsSync(crossPath)) {
    const cross = parse(fs.readFileSync(crossPath, 'utf8'), { columns: true, skip_empty_lines: true });
    const fromCross = (name) => cross.filter((r) => r.persona === name && r.included_in_persona === 'yes').map((r) => r.cno2001_code).sort().join(' ');
    check('crossref_codes', 'Correspondencia CNO-2001: los códigos incluidos coinciden con fact_persona_profile', 13,
      profile.filter((p) => fromCross(p.persona) === p.cno2001_codes.split(' ').filter(Boolean).sort().join(' ')).length);
  }
}

// Layer K (RA 2025 años 9-12): grades add up, provinces add to the national total, departments within provinces.
if (data.fact_schools_department && data.fact_schools_municipality) {
  const provRows = data.fact_schools_department.rows;
  const rows = data.fact_schools_municipality.rows;
  const k = readJson('outputs/layer_k_ar.json');
  if (k) check('k_total', 'K2: alumnos de los años 9 a 12 = suma provincial', k.K2.total, sum(provRows, 'students_target'));
  const grades = (r) => n(r.students_y9) + n(r.students_y10) + n(r.students_y11) + n(r.students_y12) === n(r.students_target);
  check('k_parts', 'Por provincia y departamento: años suman el total; estatales y rurales ≤ total; escuelas estatales ≤ escuelas',
    provRows.length + rows.length, provRows.concat(rows).filter((r) => grades(r) && n(r.students_public) <= n(r.students_target)
      && n(r.students_rural) <= n(r.students_target) && n(r.schools_public) <= n(r.schools)).length);
  const byProv = new Map();
  for (const r of rows) byProv.set(r.department_code, (byProv.get(r.department_code) || 0) + n(r.students_target));
  check('k_departments_within', 'Departamentos ≤ su provincia (filas enmascaradas solo en la provincia)', 24,
    provRows.filter((r) => (byProv.get(r.department_code) || 0) <= n(r.students_target)).length);
  check('k_department_cover', 'Departamentos con código cubren ≥ 98 % de los alumnos objetivo', true, sum(rows, 'students_target') / sum(provRows, 'students_target') >= 0.98);
}

// Layers C and L: one row per province, consistent rates, ICT discipline within the total.
if (data.fact_higher_ed_department && data.fact_population_department) {
  const rows = data.fact_higher_ed_department.rows;
  const pop = new Map(data.fact_population_department.rows.map((r) => [r.department_code, n(r.population)]));
  check('l_rows', 'Educación superior: una fila por provincia', 24, rows.length);
  check('l_per_100k', 'Universitarios por 100.000 hab. = universitarios ÷ población 2022', rows.length,
    rows.filter((r) => Math.abs(n(r.university_students_per_100k) - Math.round((n(r.university_students_census2022) / pop.get(r.department_code)) * 1e6) / 10) <= 0.1).length);
  const l = readJson('outputs/layer_l_ar.json');
  if (l) check('l3_ict', 'L3: estudiantes de Informática ≤ estudiantes universitarios 2024', true, l.L3.ict_students <= l.L1.university_students_2024);
}

// Layer E (Censo 2022): departments add to provinces; provinces add to the published national total.
if (data.fact_population_municipality && data.fact_population_department) {
  const rows = data.fact_population_municipality.rows;
  const provRows = data.fact_population_department.rows;
  check('e_national', 'Censo 2022: provincias suman 45.892.285 (total publicado)', 45892285, sum(provRows, 'population'));
  const byProv = new Map();
  for (const r of rows) byProv.set(r.department_code, (byProv.get(r.department_code) || 0) + n(r.population));
  check('e_departments_add_up', 'Censo 2022: los departamentos suman su provincia', 24, provRows.filter((r) => byProv.get(r.department_code) === n(r.population)).length);
  check('e_rows', 'Población 2022: 528 departamentos con valor positivo (94021 sin población censal, sin fila)', 528,
    new Set(rows.filter((r) => n(r.population) > 0 && r.year === '2022').map((r) => r.municipality_code)).size, rows.length === 528 && !rows.some((r) => r.municipality_code === '94021'));
}

// Layer M: provinces and every national breakdown add up to M1 within rounding (one unit per row).
const m = readJson('outputs/layer_m_ar.json');
if (data.fact_micro_department && data.fact_micro_national && m) {
  const m1 = m.M1_micro_businesses;
  const provRows = data.fact_micro_department.rows;
  const s = sum(provRows, 'micro_businesses');
  check('micro', 'Micronegocios por provincia = M1 (redondeo)', m1, s, provRows.length === 24 && Math.abs(s - m1) <= provRows.length);
  const dims = new Map();
  for (const r of data.fact_micro_national.rows) dims.set(r.dimension, (dims.get(r.dimension) || []).concat(r));
  const okDims = [...dims].filter(([, rs]) => Math.abs(sum(rs, 'micro_businesses') - m1) <= rs.length).length;
  check('micro_dimensions', 'fact_micro_national: cada dimensión suma M1', dims.size, okDims);
}

// Layer R: published-total checks and sources register (scripts/build-argentina-docs-registers.py).
const r = readJson('validation/r_checks_ar.json');
if (r) {
  check('r1', 'R1: totales contra cifras publicadas (todos dentro de tolerancia)', r.R1_published_totals.total, r.R1_published_totals.passed);
  check('r2', 'R2: registro de fuentes completo (URL, periodo, archivo, licencia, script)', r.R2_sources_register.sources, r.R2_sources_register.complete);
}

// Every code column in every table must join to its geography (lib/acceptance.js "Códigos sin unir").
for (const t of tables) {
  if (t === 'geo_department' || t === 'meta_sources') continue;
  const rows = data[t].rows;
  for (const [col, codes] of [['department_code', provCodes], ['municipality_code', deptCodes]]) {
    if (!rows.length || !(col in rows[0])) continue;
    const bad = rows.filter((x) => x[col] !== '' && !codes.has(x[col])).length;
    check(`unjoined_${t}_${col}`, `${t}.${col} une con su tabla geográfica`, 0, bad);
  }
}

// Every JSON output must parse in JavaScript (no NaN).
const badJson = fs.readdirSync(path.join(ROOT, 'outputs')).filter((f) => f.endsWith('.json')).filter((f) => {
  try { JSON.parse(fs.readFileSync(path.join(ROOT, 'outputs', f), 'utf8')); return false; } catch (_) { return true; }
});
check('json_valid', 'outputs/*.json válidos para JavaScript', 0, badJson.length);

const meta = data.meta_sources ? data.meta_sources.rows : [];
const missingSource = tables.filter((t) => t !== 'meta_sources' && !meta.some((x) => x.table_name === t && x.source && x.year));
check('meta_sources', 'Tablas con fuente y año en meta_sources', 0, missingSource.length);
check('utf8_no_bom', 'CSV UTF-8 sin BOM', 0, tables.filter((t) => data[t].bom).length);

for (const c of checks) console.log(`${c.ok ? 'ok  ' : 'FAIL'} ${c.label}: esperado ${c.expected}, real ${c.actual}`);
if (missingSource.length) console.log('     sin fuente:', missingSource.join(', '));
if (badJson.length) console.log('     JSON inválido:', badJson.join(', '));
const failed = checks.filter((c) => !c.ok).length;
console.log(`${checks.length - failed}/${checks.length} comprobaciones`);
process.exit(failed ? 1 : 0);
