'use strict';
// Read-only adapter for the Argentina tables in data/argentina (D-AR-01): Colombia-shaped CSVs read from files,
// served like Mexico and Peru. The province (INDEC 2-digit code, department_code) is the main level: province
// values come from the province tables (fact_*_department), never from summing departments, because some sources
// are only published by province or mask small departments. National facts stay national; EPH persona counts exist
// only for the urban agglomerates of each province and are never split across departments.
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const ROOT = path.join(__dirname, '..', 'data', 'argentina');
const CSV_DIR = path.join(ROOT, 'geodb', 'csv');
const OUT_DIR = path.join(ROOT, 'outputs');
// Same persona ids as Peru and Mexico, keyed by the first ISCO code of each template persona.
const PERSONA_ID = { 2511: 'P01', 2521: 'P02', 3511: 'P03', 1330: 'P04', 2163: 'P05', 2421: 'P06', 2412: 'P07',
  2120: 'P08', 2431: 'P09', 2411: 'P10', 2141: 'P11', 1211: 'P12', 2310: 'P13' };
// Core personas that the EPH occupation code (CNO-2001) can identify (D-AR-09); P02 and P04 have no code.
const CORE_IDENTIFIED = ['P01', 'P03'];
const LAYER_NAMES = { A: 'Comunidad de desarrolladores', B: 'Uso de IA entre desarrolladores', C: 'Estudiantes universitarios y TIC',
  D: 'Empresas TIC por provincia', E: 'Población', F: 'Personas y empleo', G: 'Personal TI en cada industria',
  H: 'Segmentos: persona × aglomerado × comprador', I: 'Precio frente al ingreso', J: 'Zonas de CABA y Gran Buenos Aires',
  K: 'Escuelas: años 9 a 12', L: 'Educación superior', M: 'Micronegocios', N: 'Empresas formales y almacenes',
  O: 'Contexto del país', P: 'Programa de secundaria', Q: 'Geografía y códigos', R: 'Comprobaciones y fuentes' };
// Layers drawn as territories; the rest are national indicator layers.
const GEOGRAPHIC_LAYERS = { C: 'Provincias', D: 'Provincias y departamentos', E: 'Provincias y departamentos', F: 'Provincias (aglomerados EPH)',
  G: 'Nacional (ficha de persona)', H: 'Aglomerados EPH (ficha)', J: 'Zonas', K: 'Provincias y departamentos', L: 'Provincias',
  M: 'Provincias (aglomerados EPH)', N: 'Provincias y departamentos', Q: 'Mapa base' };
// Display rule (D-AR-15): polygon parts lying entirely south of 60°S (the Antarctic sector of Tierra del Fuego) are
// left out of the web map, which uses Web Mercator; the CSV keeps the geometry as published by Georef.
const ANTARCTIC_LIMIT = -60;
// Continental view used to frame the country (the South Atlantic islands would otherwise stretch the view).
const COUNTRY_BOUNDS = [[-55.3, -73.6], [-21.7, -53.5]];

let cache = null;
const csv = (name) => parse(fs.readFileSync(path.join(CSV_DIR, `${name}.csv`), 'utf8'), { columns: true, skip_empty_lines: true });
const outCsv = (name) => parse(fs.readFileSync(path.join(OUT_DIR, `${name}.csv`), 'utf8'), { columns: true, skip_empty_lines: true });
const num = (v) => (v === '' || v === null || v === undefined ? null : Number(v));

function finite(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function boundsOf(geometry) {
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  (function visit(node) {
    if (typeof node[0] === 'number') {
      b[0] = Math.min(b[0], node[0]); b[1] = Math.min(b[1], node[1]);
      b[2] = Math.max(b[2], node[0]); b[3] = Math.max(b[3], node[1]);
      return;
    }
    node.forEach(visit);
  }(geometry.coordinates));
  return b;
}

// Keeps the polygons that reach north of 60°S; returns null when nothing is left (Antártida Argentina, 94028).
function displayGeometry(geometry) {
  const parts = geometry.coordinates.filter((poly) => poly[0].some(([, lat]) => lat > ANTARCTIC_LIMIT));
  return parts.length ? { type: 'MultiPolygon', coordinates: parts } : null;
}

function load() {
  if (cache) return cache;
  const profile = csv('fact_persona_profile').map((r) => ({
    ...r, group_id: PERSONA_ID[r.isco_codes.split(' ')[0]], employed: num(r.employed), interviews: num(r.interviews),
    median_income_ars: num(r.median_income_ars), pct_university: num(r.pct_university), pct_women: num(r.pct_women),
    identified: r.cno2001_codes !== '',
  }));
  const idOf = new Map(profile.map((p) => [p.persona, p.group_id]));
  const crossref = fs.existsSync(path.join(OUT_DIR, 'f_persona_crossref_ar.csv')) ? outCsv('f_persona_crossref_ar') : [];
  cache = {
    provinces: csv('geo_department'),
    profile, idOf, crossref,
    personaProvince: csv('fact_persona_department').map((r) => ({ ...r, group_id: idOf.get(r.persona) })),
    micro: new Map(csv('fact_micro_department').map((r) => [r.department_code, r])),
    companiesProvince: new Map(csv('fact_companies_department').map((r) => [r.department_code, r])),
    schoolsProvince: new Map(csv('fact_schools_department').map((r) => [r.department_code, r])),
    higherProvince: new Map(csv('fact_higher_ed_department').map((r) => [r.department_code, r])),
    populationProvince: new Map(csv('fact_population_department').map((r) => [r.department_code, r])),
    companies: new Map(csv('fact_companies_municipality').map((r) => [r.municipality_code, r])),
    schools: new Map(csv('fact_schools_municipality').map((r) => [r.municipality_code, r])),
    population: new Map(csv('fact_population_municipality').map((r) => [r.municipality_code, num(r.population)])),
    indicators: csv('fact_map_indicator'),
    zones: csv('geo_zone'),
    zoneFacts: new Map(csv('fact_companies_zone').map((r) => [r.zone_id, r])),
    provinceShapes: null, departmentFeatures: null, provinceMap: null,
  };
  return cache;
}

function provinceShapes() {
  const d = load();
  if (!d.provinceShapes) {
    d.provinceShapes = csv('geo_department_shape').map((r) => ({ code: r.department_code, name: r.name, geometry: displayGeometry(JSON.parse(r.geojson)) }))
      .filter((s) => s.geometry);
  }
  return d.provinceShapes;
}

const COMPANY_YEAR = 'CEP XXI 2022';
// Values shared by provinces and departments.
function departmentIndicators() {
  return [
    { key: 'it_establishments', label: 'Establecimientos TI (software y servicios informáticos)', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'software_620100', label: 'Establecimientos de software (CLAE 620100)', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'businesses', label: 'Empresas con empleo registrado (CUIT distintos)', unit: 'empresas', source: { year: COMPANY_YEAR } },
    { key: 'establishments', label: 'Establecimientos con empleo registrado', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'micro_1_9', label: 'Establecimientos micro (1 a 9 empleados)', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'medium_large_50_plus', label: 'Establecimientos medianos y grandes (50+ empleados)', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'shops_4711', label: 'Almacenes y supermercados (CLAE 4711)', unit: 'establecimientos', source: { year: COMPANY_YEAR } },
    { key: 'students_target', label: 'Alumnos de los años 9 a 12', unit: 'estudiantes', source: { year: 'RA 2025' } },
    { key: 'schools', label: 'Escuelas con secundaria común', unit: 'escuelas', source: { year: 'Padrón 2026' } },
    { key: 'population', label: 'Población', unit: 'habitantes', source: { year: 'Censo 2022' } },
  ];
}

function provinceIndicators() {
  return [
    { key: 'core_it', label: 'TI núcleo identificable (P01 y P03, EPH)', unit: 'personas ocupadas', source: { year: 'EPH 2025' } },
    { key: 'personas_identified', label: 'Personas identificables (8 de 13, EPH)', unit: 'personas ocupadas', source: { year: 'EPH 2025' } },
    ...departmentIndicators(),
    { key: 'businesses_per_school', label: 'Empresas por escuela secundaria', unit: 'empresas por escuela', source: { year: '2022 / 2026' } },
    { key: 'mean_students_per_school', label: 'Promedio de alumnos (años 9 a 12) por escuela', unit: 'estudiantes', source: { year: 'RA 2025' } },
    { key: 'university_students_census2022', label: 'Estudiantes universitarios (por residencia)', unit: 'estudiantes', source: { year: 'Censo 2022' } },
    { key: 'university_students_per_100k', label: 'Estudiantes universitarios por 100.000 habitantes', unit: 'por 100.000 hab.', source: { year: 'Censo 2022' } },
    { key: 'snu_students_ra2025', label: 'Superior no universitario (institutos)', unit: 'estudiantes', source: { year: 'RA 2025' } },
    { key: 'micro_businesses', label: 'Micronegocios (EPH, hasta 10 personas)', unit: 'micronegocios', source: { year: 'EPH 2025' } },
  ];
}

function departmentValues(code) {
  const d = load();
  const c = d.companies.get(code) || {};
  const s = d.schools.get(code);
  return {
    it_establishments: num(c.it_establishments), software_620100: num(c.software_620100), businesses: num(c.businesses),
    establishments: num(c.establishments), micro_1_9: num(c.micro_1_9), medium_large_50_plus: num(c.medium_large_50_plus),
    shops_4711: num(c.shops_4711),
    // The aggregated RA masks small departments, so a department absent from the school table is unknown, not zero.
    students_target: s ? num(s.students_target) : null, schools: s ? num(s.schools) : null,
    population: d.population.has(code) ? d.population.get(code) : null,
  };
}

function getProvinceMap() {
  const d = load();
  if (d.provinceMap) return d.provinceMap;
  const persona = new Map();
  for (const r of d.personaProvince) {
    const cur = persona.get(r.department_code) || { estimates: {}, interviews: {} };
    cur.estimates[r.group_id] = num(r.employed);
    cur.interviews[r.group_id] = num(r.interviews);
    persona.set(r.department_code, cur);
  }
  const features = provinceShapes().map((s) => {
    const p = persona.get(s.code) || { estimates: {}, interviews: {} };
    const c = d.companiesProvince.get(s.code) || {};
    const sc = d.schoolsProvince.get(s.code) || {};
    const h = d.higherProvince.get(s.code) || {};
    const pop = d.populationProvince.get(s.code) || {};
    const m = d.micro.get(s.code) || {};
    return {
      type: 'Feature', id: s.code, geometry: s.geometry,
      properties: {
        name: s.name, department_code: s.code,
        values: {
          core_it: CORE_IDENTIFIED.reduce((a, id) => a + (p.estimates[id] || 0), 0),
          personas_identified: Object.values(p.estimates).reduce((a, b) => a + (b || 0), 0),
          it_establishments: num(c.it_establishments), software_620100: num(c.software_620100), businesses: num(c.businesses),
          establishments: num(c.establishments), micro_1_9: num(c.micro_1_9), medium_large_50_plus: num(c.medium_large_50_plus),
          shops_4711: num(c.shops_4711), businesses_per_school: num(c.businesses_per_school),
          students_target: num(sc.students_target), schools: num(sc.schools), mean_students_per_school: num(sc.mean_students_per_school),
          population: num(pop.population),
          university_students_census2022: num(h.university_students_census2022), university_students_per_100k: num(h.university_students_per_100k),
          snu_students_ra2025: num(h.snu_students_ra2025),
          micro_businesses: num(m.micro_businesses),
        },
        observed_persona_estimates: p.estimates, persona_interviews: p.interviews,
      },
    };
  });
  d.provinceMap = {
    type: 'FeatureCollection', layer: 'argentina_provinces', indicators: provinceIndicators(), features, bounds: COUNTRY_BOUNDS,
    geometry_source: 'Georef (IGN), provincias, 2023-12-05; sin el sector antártico al sur de 60°S (solo visualización)',
    observed_persona_estimates: {
      source: 'INDEC EPH 2025, promedio de los cuatro trimestres; ocupación CNO-2001 → personas (D-AR-09)',
      personas: d.profile.filter((p) => p.identified).map((p) => p.group_id),
      limitations: 'La EPH cubre 31 aglomerados urbanos: cada provincia muestra sus aglomerados, no la provincia completa. Cada celda lleva su número de entrevistas; con menos de 100 es indicativa.',
    },
  };
  return d.provinceMap;
}

function departmentFeatures() {
  const d = load();
  if (!d.departmentFeatures) {
    const names = new Map(d.provinces.map((s) => [s.department_code, s.name]));
    d.departmentFeatures = csv('geo_municipality_shape').map((r) => {
      const geometry = displayGeometry(JSON.parse(r.geojson));
      if (!geometry) return null;
      return {
        type: 'Feature', id: r.municipality_code, geometry,
        properties: { name: r.name, department: names.get(r.department_code) || '', municipality_code: r.municipality_code, values: departmentValues(r.municipality_code) },
        _bounds: boundsOf(geometry),
      };
    }).filter(Boolean);
  }
  return d.departmentFeatures;
}

function getDepartmentMap(query = {}) {
  const all = departmentFeatures();
  const west = finite(query.west, -74); const east = finite(query.east, -25);
  const south = finite(query.south, -60); const north = finite(query.north, -21);
  const limit = Math.max(100, Math.min(800, Math.floor(finite(query.limit, 600))));
  const matching = all.filter((f) => f._bounds[0] <= east && f._bounds[2] >= west && f._bounds[1] <= north && f._bounds[3] >= south);
  const step = Math.max(1, Math.ceil(matching.length / limit));
  const features = (step === 1 ? matching : matching.filter((_, i) => i % step === 0).slice(0, limit)).map(({ _bounds, ...f }) => f);
  return {
    type: 'FeatureCollection', layer: 'argentina_departments', indicators: departmentIndicators(), features,
    total: matching.length, returned: features.length, sampled: features.length < matching.length,
    geometry_source: 'Georef (IGN), departamentos, 2023-12-05',
    note: 'Departamentos, partidos y comunas. Las personas de la EPH no se publican por departamento: la encuesta cubre 31 aglomerados urbanos.',
  };
}

// Layer J zones by zone-id prefix (scripts/build-argentina-d-n-j-companies.py, D-AR-07).
const ZONE_CITIES = { CABA: 'Ciudad Autónoma de Buenos Aires (15 comunas)', GBA: 'Gran Buenos Aires (24 partidos)' };

function getZoneMap() {
  const d = load();
  const indicators = [
    { key: 'companies_total', label: 'Establecimientos con empleo registrado', unit: 'establecimientos' },
    { key: 'businesses', label: 'Empresas (CUIT distintos)', unit: 'empresas' },
    { key: 'software_it', label: 'Software y TI', unit: 'establecimientos' },
    { key: 'medium_large', label: 'Medianos y grandes (50+ empleados)', unit: 'establecimientos' },
    { key: 'micro', label: 'Micro (1 a 9 empleados)', unit: 'establecimientos' },
    { key: 'design', label: 'Diseño', unit: 'establecimientos' },
    { key: 'accounting_audit', label: 'Contabilidad y auditoría', unit: 'establecimientos' },
    { key: 'management_consulting', label: 'Consultoría en gestión', unit: 'establecimientos' },
    { key: 'research_market_studies', label: 'Investigación y estudios de mercado', unit: 'establecimientos' },
    { key: 'higher_education_training', label: 'Educación superior y formación', unit: 'establecimientos' },
    { key: 'private_schools', label: 'Escuelas privadas', unit: 'establecimientos' },
    { key: 'shops_4711', label: 'Almacenes y supermercados', unit: 'establecimientos' },
  ].map((x) => ({ ...x, source: { year: COMPANY_YEAR } }));
  const features = d.zones.map((z) => {
    const f = d.zoneFacts.get(z.zone_id) || {};
    return {
      type: 'Feature', id: z.zone_id, geometry: JSON.parse(z.geojson),
      properties: { name: z.name, zone_id: z.zone_id, municipality_code: z.municipality_code, city: ZONE_CITIES[z.zone_id.split('-')[0]],
        values: Object.fromEntries(indicators.map((x) => [x.key, num(f[x.key])])) },
    };
  });
  const cities = Object.entries(ZONE_CITIES).map(([prefix, name]) => ({ prefix, name, zones: features.filter((f) => f.id.startsWith(prefix + '-')).length }));
  return { type: 'FeatureCollection', layer: 'argentina_zones', indicators, features, cities,
    note: 'CABA por comuna y los 24 partidos del Gran Buenos Aires (INDEC). Universo: establecimientos con empleo registrado (SIPA), CEP XXI 2022.' };
}

function layerSummary() {
  const d = load();
  const rPath = path.join(ROOT, 'validation', 'r_checks_ar.json');
  const r = fs.existsSync(rPath) ? JSON.parse(fs.readFileSync(rPath, 'utf8')) : null;
  return Object.keys(LAYER_NAMES).map((layer) => {
    if (layer === 'R') {
      return { layer, name: LAYER_NAMES.R, geography: 'Validación', national_values: 0,
        status: r ? `${r.R1_published_totals.passed}/${r.R1_published_totals.total} totales publicados; ${r.R2_sources_register.complete}/${r.R2_sources_register.sources} fuentes completas` : 'pending' };
    }
    // Layer B counts only Argentina's own rows, the ones getMap() puts in the selector.
    const rows = d.indicators.filter((x) => x.layer === layer && (layer !== 'B' || x.group_id === 'AR'));
    const values = rows.filter((x) => x.value !== '').length;
    return { layer, name: LAYER_NAMES[layer], geography: GEOGRAPHIC_LAYERS[layer] || 'Nacional', national_values: values,
      status: rows.length ? (values ? 'populated' : 'pending') : (GEOGRAPHIC_LAYERS[layer] ? 'territorial' : 'pending') };
  });
}

// Spanish wording of the cross-reference reasons (the CSV keeps them in English, like the other output tables).
function whyEs(why) {
  if (why.startsWith('included')) return 'incluido: la mayoría de sus ocupados son de esta persona';
  const m = /^code belongs to (P\d\d)$/.exec(why);
  if (m) return `pertenece a ${m[1]}`;
  if (why.includes('fewer than 5')) return 'no usado: menos de 5 entrevistas en 2015';
  if (why.includes('reaches 50%')) return 'no usado: ninguna persona llega al 50 % del código';
  if (why.includes('outside the 13')) return 'no usado: la mayoría de sus ocupados está fuera de las 13 personas';
  return why;
}

// CNO-2001 codes behind each persona (outputs/f_persona_crossref_ar.csv): the codes it holds, or where its workers sit.
function personaCodes(groupId) {
  const rows = load().crossref.filter((r) => r.persona_id === groupId);
  const pick = (r) => ({ code: r.cno2001_code, label: r.cno2001_label, included: r.included_in_persona === 'yes', why: whyEs(r.why),
    pct_code_workers_in_persona: num(r.pct_code_workers_in_persona), pct_persona_workers_in_code: num(r.pct_persona_workers_in_code),
    employed_2025: num(r.employed_2025) });
  return { included: rows.filter((r) => r.included_in_persona === 'yes').map(pick), other: rows.filter((r) => r.included_in_persona !== 'yes').slice(0, 3).map(pick) };
}

function getMap() {
  const d = load();
  // Layer B keeps only Argentina's own rows; the comparison groups stay in the outputs, not in the map selector.
  const indicators = d.indicators.filter((r) => r.layer !== 'B' || r.group_id === 'AR');
  return {
    country: { code: 'AR', name: 'Argentina', center: [-38.4, -63.6], zoom: 4, bounds: COUNTRY_BOUNDS },
    national_geometry: { type: 'FeatureCollection', source: 'Georef (IGN), provincias',
      features: provinceShapes().map((s) => ({ type: 'Feature', geometry: s.geometry, properties: {} })) },
    catalog: { layer_summary: layerSummary() },
    indicators,
    personas: d.profile.map((p) => ({ group_id: p.group_id, name: p.persona, label: p.identified ? p.persona : `${p.persona} (sin código en la EPH)`, ring: p.ring,
      employed: p.employed, interviews: p.interviews, identified: p.identified, reference_year: 2025 })),
    persona_blocks: {
      national_profile: { source: 'INDEC EPH 2025 (promedio anual, 31 aglomerados urbanos)', geography: 'country',
        profiles: d.profile.map((p) => ({ ...p, codes: personaCodes(p.group_id) })),
        note: 'Perfil nacional urbano de las 13 personas. Por provincia se muestran las estimaciones observadas de la misma encuesta.' },
    },
    warnings: [
      'Los indicadores nacionales (A, B, I, O, P) no se reparten por provincia o departamento.',
      'Las personas (EPH) se publican por provincia (sus aglomerados urbanos) y nunca por departamento.',
      'P02, P04, P05, P08 y P09 no tienen código propio en la EPH (CNO-2001): sus celdas quedan vacías, nunca en cero.',
      'Un valor nulo significa no disponible o pendiente; nunca equivale a cero.',
    ],
  };
}

module.exports = { getMap, getProvinceMap, getDepartmentMap, getZoneMap, layerSummary };
