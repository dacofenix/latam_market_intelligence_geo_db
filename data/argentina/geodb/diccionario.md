# Base geoespacial de Argentina (contrato de tablas)

Llave geográfica: códigos INDEC (Georef, IGN). **Provincia** = `department_code` (2 dígitos: las 23 provincias y la Ciudad Autónoma de Buenos Aires, 24 jurisdicciones). **Departamento, partido o comuna** = `municipality_code` (5 dígitos = provincia + 3 dígitos). Los códigos son texto con ceros a la izquierda (`02` = CABA, `06` = Buenos Aires). Todo es agregado.

Las tablas copian la forma de Colombia y México (`department` = provincia, `municipality` = departamento). Regla de adaptación:

- **Mismo concepto, código nacional equivalente:** se conserva el nombre de columna y se documenta el código argentino (por ejemplo `shops_4711` = CLAE6 4711xx).
- **Unidad o escala distinta:** se renombra la columna para que no se lea como comparable (moneda, años escolares, bandas de tamaño).
- **Sin equivalente en Colombia o México:** tabla nueva, marcada como *añadida para Argentina*. Las tablas por provincia (`fact_*_department`) se añadieron porque la provincia es el nivel principal de este estudio (D-AR-01).

Estado: todas las capas tienen datos. Capa Q y E: `scripts/build-argentina-q-e-geo-population.py`. Capas K, C y L: `scripts/build-argentina-k-c-l-education.py`. Capas D, N y J: `scripts/build-argentina-d-n-j-companies.py`. Capas F, G, H y M: `scripts/build-argentina-f-cno-mapping.py` y `scripts/build-argentina-eph.py`. Capas A y B: `scripts/build-argentina-a-github.py`, `scripts/build-argentina-b-survey.py`. Capas I, O y P: `scripts/build-argentina-i-o-p.py`. `fact_map_indicator`: `scripts/build-argentina-map-indicator.py`. Capa R: `validation/r_checks_ar.json` (`scripts/build-argentina-docs-registers.py`).

En el mapa web (`lib/argentinaData.js`) se omiten las partes de polígono que quedan por completo al sur de 60°S (sector antártico, departamento 94028); los CSV conservan la geometría publicada (D-AR-15).

## Tablas geográficas (capa Q)

### geo_department
Provincias. Fuente: Georef (IGN), `provincias.csv` (2023-12-05). Filas: 24.
| department_code | name |

### geo_municipality
Departamentos, partidos y comunas con punto de referencia: el centroide publicado por Georef (no se calculan centroides). `category` = Departamento (379), Partido (135, provincia de Buenos Aires) o Comuna (15, CABA). Incluye Antártida Argentina (94028) e Islas del Atlántico Sur (94021). Fuente: Georef, `departamentos.csv` (2023-12-05). Filas: 529.
| municipality_code | department_code | name | category | lat | lon | wkt |

### geo_department_shape
Polígonos provinciales (MultiPolygon WGS84 lon/lat, 5 decimales), tal como los publica Georef (ya generalizados; D-AR-02). Filas: 24.
| department_code | name | geojson |

### geo_municipality_shape — añadida para Argentina
Polígonos de departamentos, mismo tratamiento. Fuente: Georef, `departamentos.geojson`. Filas: 529.
| municipality_code | department_code | name | geojson |

### geo_zone
Zonas de la ciudad mayor (D-AR-07): las 15 comunas de CABA (`CABA-<3 dígitos>`, `zone_type` = `comuna`) y los 24 partidos del Gran Buenos Aires según el INDEC (`GBA-<3 dígitos>`, `zone_type` = `partido_gba`). Cada zona es un departamento completo: `municipality_code` es el propio departamento, `geojson` su polígono y `lat`/`lon`/`wkt` su punto. Capa J. Filas: 39.
| zone_id | municipality_code | zone_type | zone_code | name | lat | lon | geojson | wkt |

## Tablas por provincia

### fact_population_department — añadida para Argentina
Población por provincia, censos 2010 y 2022 (resultados definitivos). Suma = 45.892.285. Fuente: INDEC, Censo 2022, Cuadro 1. Capa E. Filas: 24.
| department_code | name | year | population_2010 | population |

### fact_schools_department — añadida para Argentina
Alumnos de los años corridos 9 a 12 (último año del nivel CINE 2 + nivel CINE 3; D-AR-04) por provincia, 2025. Suma = 2.676.351. Fuente: Relevamiento Anual 2025, base agregada (matrícula y matrícula por edad), y Padrón Oficial de Establecimientos (16-06-2026). Capa K. Filas: 24.
| department_code | department | students_target | students_y9 | students_y10 | students_y11 | students_y12 | students_technical_y13_14 | students_public | students_rural | students_women | students_under_18 | schools | schools_public | schools_technical_inet | mean_students_per_school |

- Las columnas de año sustituyen a `students_g9`… (Colombia tiene 3 grados objetivo, Argentina 4). Los años corridos hacen el objetivo igual en provincias con estructura 6+6 y 7+5.
- `students_technical_y13_14`: 13.º y 14.º año de la secundaria técnica, informado aparte y fuera de `students_target`.
- `students_public`: sector estatal; `students_rural`: ámbito rural del RA; `students_under_18`: suma de edades simples menores de 18.
- `schools`: localizaciones (CUE + anexo) del Padrón con oferta de secundaria común (incluidas las técnicas INET); no todas enseñan los cuatro años objetivo. `schools_technical_inet`: escuelas técnicas registradas por el INET.
- `mean_students_per_school` = `students_target` ÷ `schools`. Es un promedio, no una mediana: desde 2024 el RA se publica agregado y no hay matrícula por escuela (K5, K6 vacíos).

### fact_higher_ed_department — añadida para Argentina
Educación superior por provincia (D-AR-05). Capas C, L. Filas: 24.
| department_code | department | university_students_census2022 | postgraduate_students_census2022 | tertiary_non_university_students_census2022 | snu_students_ra2025 | snu_institutions_padron | vocational_training_centres_padron | university_students_per_100k | higher_ed_students_per_100k |

- `*_census2022`: población que asiste a universitario (de grado), posgrado y terciario no universitario, por provincia de **residencia** (Censo 2022, cuadros provinciales de educación). La SPU no publica alumnos por provincia de la institución.
- `snu_students_ra2025`: matrícula del nivel superior no universitario (RA 2025); `snu_institutions_padron` y `vocational_training_centres_padron`: localizaciones del Padrón con esas ofertas. La matrícula de formación profesional no se publica.
- `*_per_100k`: por 100.000 habitantes del Censo 2022. `higher_ed_students_per_100k` = universitarios + terciarios no universitarios del censo.

### fact_companies_department — añadida para Argentina
Establecimientos productivos con empleo registrado por provincia, 2022. Fuente: CEP XXI, *Distribución geográfica de los establecimientos productivos* (SIPA). Capas D, N. Filas: 24.
| department_code | department | establishments | businesses | micro_1_9 | medium_large_50_plus | shops_4711 | it_establishments | it_firms | software_620100 | it_620200_620300_620900 | it_631110_631120_631190_631200 | businesses_per_school |

- `establishments`: suma nacional = 715.377. `businesses`: CUIT anonimizados distintos con al menos un establecimiento en la provincia (una empresa con sedes en varias provincias cuenta en cada una; el total nacional sin duplicar es 546.421).
- Tamaño por empleo registrado del establecimiento (bandas del CEP XXI): `micro_1_9` = 1 a 9; `medium_large_50_plus` = 50 o más.
- `shops_4711` = CLAE6 471110, 471120, 471130, 471190 (almacenes, minimercados y supermercados).
- `it_establishments` = CLAE6 620100 + 620200 + 620300 + 620900 + 631110 + 631120 + 631190 + 631200; `it_firms` = CUIT distintos con esas actividades. `software_620100` = consultores en informática y suministro de programas (código de software). D-AR-06.
- `businesses_per_school` = `businesses` ÷ `schools` de `fact_schools_department` (N4).

### fact_persona_department
Ocupados por persona y provincia. INDEC EPH 2025 (suma de `PONDERA` de los 4 trimestres / 4). Solo aglomerados urbanos: la fila de una provincia son sus aglomerados EPH, no la provincia completa (D-AR-08). Solo filas con al menos una entrevista; las personas no identificables (P02, P04, P05, P08, P09) no tienen filas. Capas F, G. Las filas de cada persona suman su total.
| persona | department_code | department | employed | interviews |

### fact_micro_department
Micronegocios por provincia: trabajadores por cuenta propia y patrones cuya unidad tiene hasta 10 personas (`CAT_OCUP` 1-2, `PP04C` 1-6). Las bandas de la EPH dan 1-5 y 6-10, así que el límite de 9 de la plantilla no se puede aplicar (D-AR-10). Aglomerados EPH de cada provincia. EPH 2025. Capa M. Filas: 24.
| department_code | department | micro_businesses | interviews |

## Tablas por departamento

### fact_population_municipality — añadida para Argentina
Población 2022 por departamento, partido o comuna (Censo 2022, cuadros provinciales 1.n). Los departamentos suman exactamente su provincia. 94021 (Islas del Atlántico Sur) no tiene población censal (sin fila, nunca cero). Capa E. Filas: 528.
| municipality_code | department_code | year | population |

### fact_schools_municipality
Alumnos de los años 9 a 12 y escuelas secundarias por departamento, 2025. El RA agregado identifica el departamento por nombre; se unió a los códigos Georef por nombre normalizado, alias y coincidencia aproximada (98,08 % de los alumnos objetivo). Las filas enmascaradas por secreto estadístico (`Enmascarado`) solo están en la tabla provincial. Capa K. Filas: 527.
| municipality_code | department_code | students_target | students_y9 | students_y10 | students_y11 | students_y12 | students_public | students_rural | schools | schools_public |

### fact_companies_municipality — añadida para Argentina
Mismas columnas que `fact_companies_department` (sin `businesses_per_school`), una fila por cada departamento de Georef (0 = ningún establecimiento registrado, no un dato faltante). Tres códigos antiguos del CEP XXI se recodificaron a los vigentes: 06217 → 06218 (Chascomús), 94007 → 94008 (Río Grande), 94014 → 94015 (Ushuaia). Capas D, N. Filas: 529.
| municipality_code | department_code | establishments | businesses | micro_1_9 | medium_large_50_plus | shops_4711 | it_establishments | it_firms | software_620100 | it_620200_620300_620900 | it_631110_631120_631190_631200 |

### fact_companies_zone
Establecimientos CEP XXI 2022 por zona de `geo_zone`, con los grupos del anexo 3 de la plantilla traducidos a CLAE6 (lista de códigos en `outputs/layer_j_ar.json`; D-AR-06). `companies_total` = establecimientos; `businesses` = CUIT distintos de la zona. `micro` = 1 a 9 empleados registrados; `medium_large` = 50 o más (Colombia mide por activos: comparable solo en dirección). Las 15 comunas suman CABA. Capa J. Filas: 39.
| zone_id | zone_name | companies_total | businesses | micro | medium_large | software_it | design | accounting_audit | management_consulting | research_market_studies | higher_education_training | shops_4711 | private_schools |

## Tablas por aglomerado (EPH)

### fact_persona_metro
Ocupados por persona y aglomerado EPH (31), anclado al código del departamento de su ciudad principal (CABA: 02007, Comuna 1; Partidos del GBA: 06427, La Matanza; D-AR-08). EPH 2025. Capas F, H. Las filas de cada persona suman su total.
| persona | municipality_code | department_code | metro_area | employed | interviews |

### fact_persona_segment
Persona × aglomerado × tipo de comprador (cruce directo, nunca producto de porcentajes). Tipos: Government employee; Employee, firm 201+; Employee, firm 11-200; Employee, firm up to 10; Self-employed or employer; Other or unknown (bandas `PP04C`, cortes en 10 y 200 como Colombia). `confidence`: alta con 1.000 entrevistas o más, media 100-999, baja menos de 100 (todas las celdas son bajas). EPH 2025. Capa H.
| persona | municipality_code | department_code | city | buyer_type | employed | interviews | confidence |

## Tablas nacionales

### fact_persona_profile
Una fila por persona: perfil nacional urbano, EPH 2025 (31 aglomerados; `PONDERA` de los 4 trimestres / 4; ocupados `ESTADO` = 1). Ocupación CNO-2001 (`PP04D_COD`) asignada a las personas con `outputs/f_occupation_mapping_ar.csv` (D-AR-09). Capa F. Filas: 13.
| persona | ring | isco_codes | cno2001_codes | employed | interviews | pct_private_employee | pct_government_employee | pct_self_employed_or_employer | pct_firm_201_plus | pct_works_alone | pct_outside_tech_sector | pct_women | pct_university | median_age | median_income_ars | pct_ipcf_deciles_7_10 | pct_works_from_home | pct_informal |

- Filas vacías (P02, P04, P05, P08, P09): ningún código CNO-2001 tiene mayoría de esa persona en la doble codificación del INDEC de 2015. P01 incluye también a la mayoría de profesionales de bases de datos y redes.
- Correspondencia código por código en `outputs/f_persona_crossref_ar.csv`: para cada persona, los códigos CNO-2001 incluidos y los principales códigos donde están sus trabajadores, con `pct_code_workers_in_persona` (de los ocupados del código, % que son de la persona), `pct_persona_workers_in_code` (de los ocupados de la persona, % que tienen ese código), entrevistas 2015 y ocupados EPH 2025 del código.
- `cno2001_codes`: códigos CNO-2001 de 5 dígitos asignados (añadida para Argentina); `isco_codes`: códigos CIUO-08 de la plantilla.
- `interviews`: registros de los 4 trimestres (panel rotativo: una persona puede contar hasta 4 veces).
- `pct_firm_201_plus`: asalariados en unidades de más de 200 personas (`PP04C`), como Colombia.
- `pct_outside_tech_sector`: sector tecnológico = sección J de CAES-Mercosur (divisiones 58-63; `PP04B_COD`).
- `pct_university`: universitario completo o posgrado (`CH12` = 7 con `CH13` = 1, o `CH12` = 8).
- `median_income_ars` sustituye a `median_income_cop`: mediana de `P21` > 0 ponderada con `PONDIIO`, pesos corrientes de cada trimestre de 2025.
- `pct_ipcf_deciles_7_10`: deciles 7 a 10 del ingreso per cápita familiar del total EPH (`DECCFR`); sustituye a `pct_stratum_4_6` (D-AR-13).
- `pct_works_from_home`: lugar de trabajo `PP04G` = 6 o 12 ("en esta vivienda", sin o con lugar exclusivo); `pct_informal`: `EMPLEO` = 2 sobre respuestas válidas (añadida para Argentina).
- Cada porcentaje usa solo respuestas válidas de su variable.

### fact_ict_by_sector
Personal TI de las personas núcleo identificables (P01 y P03) por sección CAES-Mercosur del empleador. Sector tecnológico = sección J (59,5 %). EPH 2025. Capa G. Suma = 167.582.
| sector | caes_section | employed | share_pct |

### fact_micro_national
Distribuciones nacionales de micronegocios (misma definición que `fact_micro_department`). Dimensiones: total, activity, position, owner_sex, owner_age, size, informal_employment, contributions, premises, place_of_work, region. Cada dimensión suma M1: las respuestas faltantes o no preguntadas van a `Not specified`, como en México. EPH 2025. Capa M. M4 (adopción digital) no disponible.
| dimension | category | micro_businesses | pct |

### fact_developers_country
GitHub Innovation Graph, Q1 2026: las mismas 18 economías de América Latina que las tablas de Colombia y México, calculadas con el motor de la capa A sobre el mismo archivo (valores iguales a los de México). Capa A. Filas: 18.
| iso2 | country | developers | developers_yoy_pct | organizations | organizations_yoy_pct | pushes_per_dev | enterprise_lang_share_pct |

### fact_map_indicator — formato de Perú
Indicadores nacionales sin geografía (capas A, B, I, O, P), con `scope_type=country`, `scope_id=AR`. Mismas columnas que México y Perú; un `value` vacío es una celda suprimida o no disponible, nunca cero. Filas: 1.343 (A 25, B 1.264, I 22, O 23, P 9).
| layer | metric_id | scope_type | scope_id | group_id | persona_id | indicator | category | value | unit | period | comparison_period | numerator | denominator | status | source_id | method | limitations |

- Capa A: 2026Q1 frente a 2025Q1, mismas reglas que México.
- Capa B: Stack Overflow 2025, Argentina como país foco y sus grupos de comparación (Brasil, México, Colombia, Chile; América Latina sin Argentina; global).
- Capa I: tipo de cambio Com. A 3500 (promedio 2025 y de diciembre de 2025), planes de USD 25 y USD 250 en pesos, frente al salario mínimo (promedio 2025 y diciembre de 2025; D-AR-14) y al ingreso mediano de cada persona.
- Capa O: PIB per cápita (FMI), salario mínimo, inclusión financiera (Findex, BCRA), pagos digitales (BCRA), IVA a servicios digitales (21 %, Decreto 354/2018), datos personales (Ley 25.326), inteligencia artificial (Disposición 2/2023), conectividad (INDEC TIC, DataReportal, StatCounter).
- Capa P: escuelas, promedio de alumnos (sin mediana ni alcance), USD 250 por escuela, empresas por escuela, deducción de donaciones (Ganancias, por confirmar) y datos de menores (AAIP Res. 4/2019).

## Indicadores que viven solo en los JSON de capa
- C1/L3 (`layer_c_ar.json`, `layer_l_ar.json`): disciplina Informática, 186.240 estudiantes de pregrado y grado en 2024 (7,1 %), nacional; nuevos inscriptos 61.837.
- D3 (`layer_d_ar.json`): industria del software (OPSSI-CESSI, 1.er trimestre de 2026, citado por prensa): 162.391 empleos registrados; por confirmar con el informe.
- L5 (`layer_l_ar.json`): 3.446 centros de formación profesional (1.336 INET); sin matrícula.
- N2: forma jurídica no disponible (CUIT anonimizado).

## meta_sources
Fuente y año de cada tabla.
| table_name | description | source | year |
