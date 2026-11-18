# Argentina: datos del estudio de país

Estructura para incorporar los datos de Argentina siguiendo la plantilla de investigación por países (capas A–R) y la misma organización del paquete de México (`research-mexico`). Las tablas de salida conservan la forma de Colombia y México (`geodb/csv/`, `geodb/diccionario.md`) para compararse entre países; algunas columnas cambian por país (por ejemplo `median_income_ars` en lugar de `median_income_mxn`).

**Nivel principal: provincia.** La aplicación lee Argentina desde estos archivos (`lib/argentinaData.js`, rutas `/api/argentina/*`), como México y Perú. Los datos se dividen en las 24 jurisdicciones de Argentina: 23 provincias y la Ciudad Autónoma de Buenos Aires (`department_code`, código INDEC de 2 dígitos). Debajo de la provincia están los 529 departamentos, partidos y comunas (`municipality_code`, código INDEC de 5 dígitos) cuando la fuente lo permite (D-AR-01).

## Carpetas

| Carpeta | Contenido | ¿Se versiona? |
|---|---|---|
| `raw/` | Archivos oficiales descargados una sola vez, sin modificar. Ver `raw/README.md` (con la lista de SHA-256). No se incluyen en este paquete. | No (solo su README) |
| `outputs/` | Un JSON por capa (`layer_<x>_ar.json`) y las tablas de trabajo de las capas A, B y F (`*_ar.csv`), producidos por los scripts. | Sí |
| `geodb/csv/` | Tablas con la forma de Colombia y México (`geo_department`, `geo_municipality`, `fact_persona_profile`, …) y `meta_sources.csv`. El contrato de cada tabla está en `geodb/diccionario.md`. | Sí |
| `validation/` | Resultados de las comprobaciones de la capa R (`r_checks_ar.json`): totales publicados (R1) y registro de fuentes (R2). | Sí |
| `sources_register.csv` | Registro de fuentes (R2): fuente, URL, periodo, archivo, SHA-256, licencia y script de cada cifra. | Sí |
| `decisions_log.csv` | Decisiones metodológicas y desviaciones de la plantilla (D-AR-01 a D-AR-16). | Sí |
| `f_mapping_overrides.csv` | Ajustes manuales al mapeo CNO-2001 → personas. Vacío: no se aplicó ninguno (D-AR-09). | Sí |

### Tablas por provincia (24 filas, una por jurisdicción)

| Tabla | Contenido | Fuente y periodo |
|---|---|---|
| `geo_department`, `geo_department_shape` | Provincias y sus polígonos | Georef (IGN), 2023-12-05 |
| `fact_population_department` | Población 2010 y 2022 | INDEC, Censo 2022 |
| `fact_schools_department` | Alumnos de los años 9 a 12 y escuelas secundarias | Relevamiento Anual 2025; Padrón 2026 |
| `fact_higher_ed_department` | Universitarios, posgrado, terciario no universitario, institutos y centros de formación profesional | Censo 2022; RA 2025; Padrón 2026 |
| `fact_companies_department` | Establecimientos, empresas, micro y medianas-grandes, almacenes y TI | CEP XXI (SIPA), 2022 |
| `fact_persona_department` | Ocupados por persona (aglomerados EPH de cada provincia) | INDEC EPH 2025 |
| `fact_micro_department` | Micronegocios (aglomerados EPH de cada provincia) | INDEC EPH 2025 |

Las tablas por departamento (`geo_municipality`, `geo_municipality_shape`, `fact_population_municipality`, `fact_schools_municipality`, `fact_companies_municipality`) llevan también `department_code`, así que se agregan a provincia sin otra tabla. Las zonas de la capa J son las 15 comunas de CABA y los 24 partidos del Gran Buenos Aires (`geo_zone`, `fact_companies_zone`).

## Reglas

- Solo se versionan agregados. Ningún microdato, registro individual ni dirección de establecimiento entra al paquete.
- Claves geográficas INDEC como texto con ceros a la izquierda: provincia (`department_code`, 2 dígitos) y departamento, partido o comuna (`municipality_code`, 5 dígitos = provincia + departamento).
- Celda vacía (`null`) significa suprimido, no disponible o pendiente; nunca se convierte en cero. En las tablas de empresas, 0 sí es cero (ningún establecimiento registrado).
- No se inventan cifras: cada valor sale de una fuente del registro o se deriva de ellas con el método indicado. Las cifras nacionales no se reparten entre provincias o departamentos.
- La EPH solo cubre 31 aglomerados urbanos: las filas por provincia de las capas F, G, H y M son los aglomerados de esa provincia, no la provincia completa (D-AR-08). No hay cifras EPH por departamento.
- Cada cifra de encuesta lleva su número de entrevistas y su nivel de confianza.
- Totales contra la publicación oficial (`validation/r_checks_ar.json`): tasas de empleo y desocupación EPH por trimestre dentro de 0,05 puntos; población del Censo 2022, matrícula RA 2025, Anuario universitario 2024 y establecimientos CEP XXI exactos. Resultado: 15 de 15 comprobaciones superadas.

## Periodos de referencia

Últimas fuentes completas disponibles el 18-11-2026:

| Capas | Periodo previsto en la plantilla | Periodo usado |
|---|---|---|
| A | GitHub Innovation Graph, último trimestre | 2026 Q1 frente a 2025 Q1 (release 1.0.10, igual que México y Perú) |
| B | Stack Overflow Developer Survey, última edición | Encuesta 2025 (222 respuestas de Argentina, confianza baja) |
| C, K, L | Último ciclo escolar | RA 2025 (años 9 a 12); Padrón de establecimientos 16-06-2026; Anuario universitario 2024 (adelanto 14-08-2026); asistencia universitaria por provincia: Censo 2022 (D-AR-05) |
| D, J, N | Último registro de empresas | CEP XXI, establecimientos con empleo registrado, 2022 (última publicación abierta); D3: OPSSI-CESSI, 1.er trimestre de 2026 |
| E | Población del año de la matrícula | Censo 2022, resultados definitivos (no hay proyecciones provinciales; D-AR-03) |
| F, G, H, M | Encuesta de empleo 2025, promedio de los trimestres 1 a 4 | INDEC EPH 2025, trimestres 1 a 4 |
| I, O | 2025; leyes vigentes | Tipo de cambio A 3500 2025; SMVM 2025; FMI WEO octubre de 2026; Findex 2025; BCRA (dic. 2025); TIC INDEC 4.º trimestre de 2024 (última edición); leyes vigentes en 2026 |
| P | Ciclo actual + registro de empresas | RA 2025 + Padrón 2026 + CEP XXI 2022 |
| Q | Catálogo geográfico vigente | Georef (IGN), archivos del 2023-12-05 |

## Limitaciones principales

- Personas sin código CNO-2001 identificable (filas vacías, nunca cero): P02 bases de datos, sistemas y redes; P04 gerentes TIC; P05 diseñadores; P08 datos y estadística; P09 marketing. La EPH codifica la ocupación en CNO-2001, cuya correspondencia oficial con CIUO-08 es solo a 2 dígitos; el mapeo usa la doble codificación del INDEC de 2015 por mayoría (D-AR-09, `outputs/f_persona_correspondence_ar.csv`). La correspondencia código por código está en `outputs/f_persona_crossref_ar.csv`: qué códigos CNO-2001 forman cada persona, qué parte de sus ocupados son de esa persona y, para las personas vacías, en qué códigos están sus trabajadores.
- Capa K: desde 2024 el RA se publica agregado por departamento; no hay mediana por escuela, distribución por tamaño ni alcance con tope de 100 (K5, K6, P1).
- Capas C y L: la Secretaría de Políticas Universitarias no publica alumnos por provincia; se usa la asistencia del Censo 2022 por lugar de residencia. La matrícula de formación profesional no está en los datos abiertos.
- Capas D, J y N: el CEP XXI solo cuenta empleadores registrados (SIPA), no empresas sin empleados, y su última publicación es 2022. No hay forma jurídica (N2).
- Capa M: no existe encuesta de micronegocios; M4 (adopción digital) no está disponible.

## Cómo reproducir

Desde la raíz del repositorio, con las descargas en `data/argentina/raw/` (ver `raw/README.md`). Los scripts están en `scripts/build-argentina-*.py`:

```
python3 scripts/build-argentina-q-e-geo-population.py data/argentina/raw data/argentina          # Q, E
python3 scripts/build-argentina-a-github.py data/argentina/raw/github_innovationgraph data/argentina/outputs --focus AR   # A
python3 scripts/build-argentina-b-survey.py data/argentina/raw/stackoverflow_survey/so_2025 data/argentina/outputs --focus AR   # B
python3 scripts/build-argentina-b-json.py data/argentina/raw/stackoverflow_survey/so_2025 data/argentina/outputs
python3 scripts/build-argentina-f-cno-mapping.py data/argentina/raw data/argentina/outputs     # mapeo CNO-2001 → personas
python3 scripts/build-argentina-eph.py data/argentina/raw data/argentina                       # F, G, H, M
python3 scripts/build-argentina-f-crossref.py data/argentina/raw data/argentina                # correspondencia código por código
python3 scripts/build-argentina-k-c-l-education.py data/argentina/raw data/argentina           # K, C, L
python3 scripts/build-argentina-d-n-j-companies.py data/argentina/raw data/argentina           # D, N, J
python3 scripts/build-argentina-i-o-p.py data/argentina/raw data/argentina                     # I, O, P (después de D/N, K y F)
python3 scripts/build-argentina-map-indicator.py data/argentina                                # fact_map_indicator, fact_developers_country
python3 scripts/build-argentina-docs-registers.py data/argentina/raw data/argentina             # registros y capa R
node scripts/check-argentina.js                                                                 # comprobaciones del mapa
```

`build-argentina-i-o-p.py` y `build-argentina-a-github.py` dejan dos archivos intermedios (`outputs/_iop_rows_ar.csv`, `outputs/_a_engine_ar.json`) que lee `build-argentina-map-indicator.py`; no se versionan.
