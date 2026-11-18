# Argentina: descargas originales

Todo lo que se guarde aquí, salvo este archivo, queda fuera de Git y de este paquete. Los archivos se dejan tal como se descargaron. En la descarga se les añadió el prefijo `ar_raw_` (para separarlos de otros archivos de la carpeta de descargas); el resto del nombre es el original. Cada descarga está en `../sources_register.csv` (URL, fecha, SHA-256) y la lista completa de SHA-256 está al final de este archivo.

Muchos sitios oficiales argentinos (`*.gob.ar`, INDEC, BCRA) rechazan accesos automatizados; las descargas se hicieron desde un navegador el 18-11-2026.

| Subcarpeta | Fuente | Capas | Qué descargar |
|---|---|---|---|
| `georef/` | Georef (IGN, datos.gob.ar), archivos del 2023-12-05 | Q | `provincias.csv`, `departamentos.csv`, `provincias.geojson`, `departamentos.geojson` (https://infra.datos.gob.ar/georef/) |
| `indec_censo2022/` | INDEC, Censo 2022, resultados definitivos | E, C, L | `c2022_tp_est_c1.xlsx` (población por jurisdicción); por provincia `c2022_<prov>_est_c1_<n>.xlsx` (población por departamento) y `c2022_<prov>_educacion_c2_<n>.xlsx` (asistencia por nivel); proyecciones nacionales 2022-2040; folleto ¿Qué es el Gran Buenos Aires? |
| `indec_eph_2025/` | INDEC, EPH, bases usuarias | F, G, H, M | `EPH_usu_<1-4>_Trim_2025_txt.zip` y los diseños de registro del 1.º y 4.º trimestres |
| `indec_eph_reports/` | INDEC, Mercado de trabajo, informe de septiembre de 2026 | R | `cuadros_eph_informe_09_26.xls` (Cuadro 1.1, tasas por trimestre) |
| `indec_cno_caes/` | INDEC, clasificadores CNO-2001 y CAES-Mercosur, conversión CNO-2001 / CIUO-08, EPH 2015 codificada en CIUO-08 | F | `CONVERSION_CNO-01_CIUO-08.xls`, `EPH_CIUO_115.rar`, `EPH_CIUO_215.rar`, `EPHcontinua_CNO2001_reducido_09.pdf`, `caes_mercosur_1.0.pdf`, `EPHcontinua_CAES_Mercosur_09.pdf`, aglomerados EPH |
| `indec_eph_2015/` | INDEC, EPH 1.º y 2.º trimestres de 2015 | F (mapeo) | `t115_dta.rar`, `t215_dta.rar` y su diseño de registro |
| `indec_tic/` | INDEC, Acceso y uso de TIC, 4.º trimestre de 2024 | O | `cuadros_tic_05_25.xls` e informe |
| `educ_ra/` | Secretaría de Educación, Relevamiento Anual 2025 (bases agregadas) y 2024 | K, L | Matrícula agregada, matrícula por edad, características y diccionario (enlaces SharePoint del conjunto de datos en datos.gob.ar, con `?download=1`) |
| `educ_padron/` | Padrón Oficial de Establecimientos Educativos (16-06-2026) | K, L, P | `2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx` |
| `univ/` | SPU, Anuario Estadístico Universitario 2024 (adelanto) y Síntesis 2023-2024 | C, L | `adelanto_anuario_24_14-08.zip`, `sintesis_anuario_2023-2024.pdf` |
| `cep_xxi/` | CEP XXI, Distribución geográfica de los establecimientos productivos | D, J, N, P | `distribucion_establecimientos_productivos_sexo.csv`, diccionarios de actividades y departamentos, datos por departamento y actividad, metodología |
| `context/` | BCRA (A 3500, inclusión financiera, pagos minoristas), FMI DataMapper, Banco Mundial (Findex), DataReportal, StatCounter | I, O | Archivos y respuestas de API guardados el 18-11-2026 |
| `github_innovationgraph/` | GitHub Innovation Graph, commit `078fb62` (el mismo de Perú y México) | A | `data/developers.csv`, `organizations.csv`, `git_pushes.csv`, `repositories.csv`, `languages.csv` |
| `stackoverflow_survey/so_2025/` | Stack Overflow Developer Survey 2025 (commit `c9c23dc`, objeto LFS) | B | `results.csv` y `ai.json` |

Normas y textos citados sin archivo (Boletín Oficial, leyes de IVA, Ganancias y datos personales, AAIP, Disposición 2/2023, nota de Ámbito sobre OPSSI) se registran solo con su URL en `../sources_register.csv`.

## SHA-256 de las descargas

| sha256 | bytes | archivo |
|---|---|---|
| `0cfd2d214ae79d72ac55b9acae73aee4537a70ca89b5b674948a1ea87ce8eb3f` | 10,542,698 | `cep_xxi/cep_Datos_por_departamento_y_actividad.csv` |
| `9b7de711bbfd8f7761dd0bff163f7695cf03eac8225553d898f2ff41a1e32b54` | 488,512 | `cep_xxi/cep_Metodologia_establecimiento_productivos.pdf` |
| `c6aee4f752a5131928e8056c11c0b91015b3d3dd0dca91a179cfa869b2a89359` | 183,178 | `cep_xxi/cep_actividades_establecimientos.csv` |
| `373a29e84f37db6e2e6b66c29cce26a674cf8ee229d52edf5b4e4e1188c000f6` | 16,376 | `cep_xxi/cep_codigo_departamento_provincia.csv` |
| `d78737e744f04814f7f7c952324c4666e1cb54c81bb645236cc39106939c912c` | 96,063,842 | `cep_xxi/cep_distribucion_establecimientos_productivos_sexo.csv` |
| `7b8940ec60ab8549698b6c11022c0fd56832fd302556e4423b7334c448c38bdc` | 390,144 | `context/bcra_com3500.xls` |
| `791835603eaf4d31bf637cccc72f8d5ee1e18e8545ddf66cd248bb2ddd12d311` | 1,877,423 | `context/bcra_informe-inclusion-financiera-2026-04.pdf` |
| `a22fd8baa5a6247a402908b282f26e56f895fc320c692853a6b3ef39d30002e0` | 461,973 | `context/bcra_informe-pagos-minoristas-2025-12.pdf` |
| `d1143922c6ec0248cfc715d66c6d90f347396879a94ef464d150b7b98b75db17` | 175,565 | `context/imf_datamapper_NGDPDPC_downloaded_2026-11-18.json` |
| `7aa12d574d7920a2c9d2785dd2bf9cc90acf843106fdafbab08c782cbfbec01e` | 95 | `context/statcounter_desktop_mobile_tablet_AR_yearly_2025.csv` |
| `cd73c2c3e20c752e96c68fe86664cde52ee9bad2976d741d0cc509a7d4f09547` | 2,197 | `context/worldbank_api_findex_2026-11-18.json` |
| `b52c9f156f9535295227d93a350dd0e189138f483bfa48d2a27a4057e135e1de` | 15,660,766 | `educ_padron/2026.06.16_padron_oficial_establecimientos_educativos_die_icse.xlsx` |
| `74ffe1485fc0826a0fda458f4645748d84ed0084249541760d69e0de479db9ef` | 383,049 | `educ_ra/ra2024_usuaria2_matricula.csv` |
| `29f8758ea3966a25f54ee42ee724243de8384cb987cd1208899f1559c78eb302` | 221,727 | `educ_ra/ra2024_usuaria5_caracteristicas.csv` |
| `488a5ac9281a1ac63438bb172803620b6a2a1d758805f7c03f397857dbf5e8e2` | 224,205 | `educ_ra/ra2025_agregada_caracteristicas.csv` |
| `79ce9c3f3bb5dd27fb1e6b8effb5b10ad922f82363db9dfb8c3f2d9180fd2b73` | 378,808 | `educ_ra/ra2025_agregada_matricula.csv` |
| `052f9a4886547dca09a0e8be8468e0c694d4e226679c962b7d28bab5ca36b75c` | 2,588,733 | `educ_ra/ra2025_agregada_matricula_edad.csv` |
| `f329d6119a6a8caae050ff4400e80d255100b0fb4089bcb1d18caf50d0fe654b` | 40,573 | `educ_ra/ra_diccionario_variables.xlsx` |
| `407e2ed69f1b7a0d30badf206de8f3da27e0f9c20a17b6917cb869b86f14d607` | 62,464 | `georef/georef_departamentos.csv` |
| `31afdfe5983b6d7648eba1eafc7a5a8fe3c591abdca4b17c311c08c75d361e92` | 1,193,417 | `georef/georef_departamentos.geojson` |
| `07892ec27d23c76b8272e6be287eb1a52a4f7143483d34d74ac53dbecdebc1a8` | 2,830 | `georef/georef_provincias.csv` |
| `b086852064c26813d9f607c82c91b4e74e18ea83fd21993ddedd473cf8495af5` | 614,706 | `georef/georef_provincias.geojson` |
| `4d66d50024066cbb85fec990f75bdb9a736e89dc998af8fbca6e946c14e56fd1` | 90,282 | `github_innovationgraph/developers.csv` |
| `8d8525632080b21e1b39cfd2fbd0abdb898461ec9ee7e59da61977749a296d3a` | 72,294 | `github_innovationgraph/git_pushes.csv` |
| `795f7b9da010161544ed50359e2bce9a9c8757831c25f4cb939dbf0569215dc2` | 5,832,978 | `github_innovationgraph/languages.csv` |
| `756ca03e5b6edcc81eafffa66f6d3a95f95d80e1fdad89f2f3ae8e7e5e8a88d6` | 69,170 | `github_innovationgraph/organizations.csv` |
| `ccff96ee8774b9a3369ab552cb2b568b135b8bd5b818e2678071731ec34b8613` | 91,229 | `github_innovationgraph/repositories.csv` |
| `06f9026f4a5357f620b0d80ed3b710751e677ebe47e2785a8668600f60c0494e` | 1,632,128 | `indec_censo2022/c2022_bsas_educacion_c2_2.xlsx` |
| `f83d95b74937ac24014744bffcfa0ea0d05b19b922a324f119614c93c5331ea4` | 39,707 | `indec_censo2022/c2022_bsas_est_c1_2.xlsx` |
| `23099c51068837a3e999ce91c5f6af3fe8c006cb909675acced2f64f45f9c38d` | 213,738 | `indec_censo2022/c2022_caba_educacion_c2_1.xlsx` |
| `0aa65597e1b84ac7287b79f39ac0e3803562984917186d76c56d007ee7fb293a` | 15,928 | `indec_censo2022/c2022_caba_est_c1_1.xlsx` |
| `96b38b37fdee291639586929e00bc8584169fa8f156c45e58ca8a27a79b17f2b` | 210,927 | `indec_censo2022/c2022_catamarca_educacion_c2_3.xlsx` |
| `6c7f5c5503287b0d6895ab92202aca9c2f582a7568185f6f9324eac9b5d01202` | 22,252 | `indec_censo2022/c2022_catamarca_est_c1_3.xlsx` |
| `54b1950569fb6d9ca279457069e80254565c29080eb74c1070de014f5f88a9cb` | 322,507 | `indec_censo2022/c2022_chaco_educacion_c2_4.xlsx` |
| `8fe948f7677a7e7f8cbcf9b3dee540967d6ffe7f4646ee3360cc3242f495ea00` | 16,564 | `indec_censo2022/c2022_chaco_est_c1_4.xlsx` |
| `0430754b38825ace7649cb80deb7b1d8f38de259603352c38283d58900bf2a03` | 204,213 | `indec_censo2022/c2022_chubut_educacion_c2_5.xlsx` |
| `8a1c8a6251a6deb6f8d9681f94de0af541de4c600466ab1993aca97353df6878` | 16,092 | `indec_censo2022/c2022_chubut_est_c1_5.xlsx` |
| `9de54774f4a3e7d6a93aecffb692ed7928e8948052286c19400d46a3cd7265ea` | 340,989 | `indec_censo2022/c2022_cordoba_educacion_c2_6.xlsx` |
| `0adbbd70e0f4084685b1a7c6b7ff884f7528c90f36b0e463a88baa923c4cbf72` | 16,904 | `indec_censo2022/c2022_cordoba_est_c1_6.xlsx` |
| `5d9aeec72f8470e8a49894391bdf8fdef0bd9577c18f9552c6543a320b4f412f` | 322,090 | `indec_censo2022/c2022_corrientes_educacion_c2_7.xlsx` |
| `62ec130c9d528a6361818232909a00e00b248ce93eadaa5b0904da613809bd4a` | 16,572 | `indec_censo2022/c2022_corrientes_est_c1_7.xlsx` |
| `e087dd429367f11a4003791fe23ae08f4439a6c3942f49f1dc1eb38d3fbd1591` | 233,224 | `indec_censo2022/c2022_entrerios_educacion_c2_8.xlsx` |
| `309e956a9066bc561e7fcca37823cf00f0a36b3308ec1f28d78c797fd007010c` | 16,219 | `indec_censo2022/c2022_entrerios_est_c1_8.xlsx` |
| `6c28f46075424ba9db6779aa4bfe3e8bc74d850baf248899da0067fa440b362f` | 133,717 | `indec_censo2022/c2022_formosa_educacion_c2_9.xlsx` |
| `6834f6a0d61543179337834a9429484ef0d6e06da64f842efc1074c295ceab17` | 15,472 | `indec_censo2022/c2022_formosa_est_c1_9.xlsx` |
| `662a9da94992bf24c1881463e4e191a8a1e2aced8fa1c25989988636fdcee6e0` | 216,734 | `indec_censo2022/c2022_jujuy_educacion_c2_10.xlsx` |
| `dee8f6133a4cb591d6499f32455762fa63fe5aa19179559c3896baef4aa832da` | 15,952 | `indec_censo2022/c2022_jujuy_est_c1_10.xlsx` |
| `70ab1eb2e0eb7d8c2c37ee4124bb6c8cae14f4dcc0315fcc562fdedb1123a7ef` | 277,873 | `indec_censo2022/c2022_lapampa_educacion_c2_11.xlsx` |
| `d8ee0b4d1e4629a5822f255014d5eacc718f3fcd83bc7df7e676568334cf80ef` | 16,432 | `indec_censo2022/c2022_lapampa_est_c1_11.xlsx` |
| `900d603524be059d2c5c3936b0bcda0562acbda9835cf9d857729a402bb209e2` | 232,004 | `indec_censo2022/c2022_larioja_educacion_c2_12.xlsx` |
| `6037989b99985d30419e9d804c54f62ce177c5c1d04ef559d11836bc80f13d2f` | 15,984 | `indec_censo2022/c2022_larioja_est_c1_12.xlsx` |
| `6f475ad991a63ef8b15862f1ef80832da4ab4b348f9321067f2ee7202a1225d0` | 242,576 | `indec_censo2022/c2022_mendoza_educacion_c2_13.xlsx` |
| `f06f10444023687550f9025a6a44bf741ce3fd6a4c7254a99fb76fe0780c5651` | 15,075 | `indec_censo2022/c2022_mendoza_est_c1_13.xlsx` |
| `6217a7ea429ff3745156c02436475f11b4f8e1e4a189487e35761dca003869d8` | 229,115 | `indec_censo2022/c2022_misiones_educacion_c2_14.xlsx` |
| `a03423bd812b7a7ca49469c64b12a952d7a59d93e1e9a2b248e3f1c363e1fddd` | 16,003 | `indec_censo2022/c2022_misiones_est_c1_14.xlsx` |
| `39567fa445161f45cb71e10d94a0d6e2ba78479504bb4a27601cd3fcabc0465f` | 216,768 | `indec_censo2022/c2022_neuquen_educacion_c2_15.xlsx` |
| `986aed255dbe7a3db7266a25db4d798e8bb84b4ab7b18a88f1a1d25fc83c5717` | 16,150 | `indec_censo2022/c2022_neuquen_est_c1_15.xlsx` |
| `585fc70ec873e08cba7bfba4dcbeeaaba5c3be8278c427302e44891350c30724` | 181,741 | `indec_censo2022/c2022_rionegro_educacion_c2_16.xlsx` |
| `ec58cbd86e4148cb40464e1efe17f705972217bce0311cbf681a116f2eab40db` | 15,923 | `indec_censo2022/c2022_rionegro_est_c1_16.xlsx` |
| `47b56ed96eeca25d29ea81b0392a38363043525433d3d09d1c52d030b92b9f1b` | 295,470 | `indec_censo2022/c2022_salta_educacion_c2_17.xlsx` |
| `537881b0892f4efa90ce08b7af978b2cf71deee86d2dfc5f30f0f528492a29f5` | 16,323 | `indec_censo2022/c2022_salta_est_c1_17.xlsx` |
| `ee27341f6b6852ac55d3654a101a85dbee6645ec77296635951c856317e6eba4` | 251,508 | `indec_censo2022/c2022_sanjuan_educacion_c2_18.xlsx` |
| `18d90ebb2fdf28751d796da7772196b47f7f69234d1a18137cb69e80e3f0ef9e` | 16,097 | `indec_censo2022/c2022_sanjuan_est_c1_18.xlsx` |
| `ba3cfa2943f541f46655f1e695ee377cb5b6a0fa3af8704432de90d7efa0c7d7` | 131,541 | `indec_censo2022/c2022_sanluis_educacion_c2_19.xlsx` |
| `4cd32a98d799e9dfb8a32d39bd48abe50e4cf54a009d62150266f842978d1b07` | 14,588 | `indec_censo2022/c2022_sanluis_est_c1_19.xlsx` |
| `d3f89e949054c5b096e83c791ad2d90ae604b6f9c36e9537f76b043cad7ea793` | 113,254 | `indec_censo2022/c2022_santacruz_educacion_c2_20.xlsx` |
| `487085d03ab585084d9dd043dc9b4f6cf682b8497cf15486a9c37d476023eeb2` | 15,540 | `indec_censo2022/c2022_santacruz_est_c1_20.xlsx` |
| `50dbca8de81683c6d1f7a6290848c0b72af496bbc8d20a666a869319ba179412` | 258,196 | `indec_censo2022/c2022_santafe_educacion_c2_21.xlsx` |
| `936689b6031d25dfefd09272ac533c1498d3480c1714643cf4013eef37f0c06e` | 16,236 | `indec_censo2022/c2022_santafe_est_c1_21.xlsx` |
| `a3c421d0f4b12e4dafcc7eebae0a3c5a76d8d54c3469bd4fe389564a0e056c0c` | 341,146 | `indec_censo2022/c2022_santiago_educacion_c2_22.xlsx` |
| `f8ccf459fb7a29b6a67c0063e8c5e8ce2d822fc98cbb1ad3010b0e5e2733c143` | 16,670 | `indec_censo2022/c2022_santiago_est_c1_22.xlsx` |
| `50f36af3fcc8b42775c6cbc2e6887ce0f0724e4dc6278026f8ad7f2a810c99d0` | 67,377 | `indec_censo2022/c2022_tdf_educacion_c2_23.xlsx` |
| `d6d264233ca345a03924183c87423f2812a16b8cce23a964f373d6bea8170da7` | 16,197 | `indec_censo2022/c2022_tdf_est_c1_23.xlsx` |
| `7cdb0b44ee0370c487145b4ff383c0dc073244a09c274dd53556a75ef4c0006c` | 13,355 | `indec_censo2022/c2022_tp_c_resumen.xlsx` |
| `e6d843c759f50f80581a6b2f3fff70c4b57836946554e805f4a3a5d58ac8f0d6` | 21,254 | `indec_censo2022/c2022_tp_educacion_c2.xlsx` |
| `b900f4bfd517d228882b834bbb571a16b05b83c378724f944e26b73af2eabfed` | 17,059 | `indec_censo2022/c2022_tp_est_c1.xlsx` |
| `c7e707ff84a676cb6007c47cfdb72ddc3acb512c6206b1b8f25a2b898c412e2e` | 17,686 | `indec_censo2022/c2022_tp_est_c2.xlsx` |
| `879ad8417e73fc662e565517c897aad40d856be70752437e0006e0b2d838dc55` | 230,539 | `indec_censo2022/c2022_tucuman_educacion_c2_24.xlsx` |
| `b6bdc6a79f85749f1cb28bc172b9cb2b1fe2df7900b73e8df8d9381575d0732c` | 16,230 | `indec_censo2022/c2022_tucuman_est_c1_24.xlsx` |
| `1e97055b9c236a3b4f7c6671814a3633c1d33fbd22124318531e4b270bbfe97f` | 1,619,581 | `indec_censo2022/folleto_gba.pdf` |
| `478a9a8fd1e888ea5c9b2039f6eddee3228f191043de128c159a43c614dbb5e4` | 76,030 | `indec_censo2022/proyecciones_nacionales_2022_2040_c1_c2.xlsx` |
| `d5500ecebc12f1c8da7b09b4b98baa0e7547f41b7d51886d8c654bcf1eda5691` | 146,432 | `indec_cno_caes/CONVERSION_CNO-01_CIUO-08.xls` |
| `f08fdfc2fe1b0c9f6576e600f9940a9b190514a81f9629c6e792aa4a74fee587` | 595,090 | `indec_cno_caes/EPH_CIUO_115.rar` |
| `3432b2b8d618e8ee4713f3bfa88ea6b420c10353fcf79e83a98ed289be2e1d90` | 596,320 | `indec_cno_caes/EPH_CIUO_215.rar` |
| `7c75e3561c70b6a3d850d6100714a795e4dc3fce2c29022bfb3c5fdd886d5fdd` | 271,580 | `indec_cno_caes/EPH_Conceptos.pdf` |
| `16c1c852651a814ef161b96bd97a812a116fbaa8bc92c1bfeab633df2dc7d6d9` | 2,488,738 | `indec_cno_caes/EPHcontinua_CAES_Mercosur_09.pdf` |
| `e30e8e8ff5c1e79b5b4360b9223426c7dc0003025f6f08d8d730a92d11900c7d` | 2,194,779 | `indec_cno_caes/EPHcontinua_CNO2001_reducido_09.pdf` |
| `83506d5c4e9e63229ecf184de0005809bae01e3608f2a384db002ce479dc6be6` | 595,843 | `indec_cno_caes/aglomerados_eph_json.zip` |
| `c3185b84062aad29cb64849cde4e1491037384a3b1a3d75b15bb6c3c5e302cfc` | 260,346 | `indec_cno_caes/caes_mercosur_1.0.pdf` |
| `9ac67ae607795c48c666b3e7a1ead8644aac82f853460a87ad34daa0ce1d0be1` | 40,960 | `indec_cno_caes/localidades_aglomerados_eph.xls` |
| `ed23daf1cf7f00d6a8498c759628d8556fffb3185de2a5c8021cbb3250ad9799` | 868,603 | `indec_eph_2015/EPH_disenoreg_T1_2015.pdf` |
| `29d4ce5d9562e7058efbeb8024f2a24a7b07ecfc5f4cd89ba66d881445538e6f` | 1,917,155 | `indec_eph_2015/t115_dta.rar` |
| `7cbed7272a1e72c51e58064fe398f5e79e1f49841860fdd0763f5cb350b8aeb4` | 1,787,908 | `indec_eph_2015/t215_dta.rar` |
| `37aaf157a475638c5317c98ffdeb3a33b23cdc6d467259dedef03902b9259c3b` | 471,128 | `indec_eph_2025/EPH_registro_1T2025.pdf` |
| `ac514a7bc32de9f1c9a2423edf50767a70bb033a035e951d1070c846a3484dbb` | 697,175 | `indec_eph_2025/EPH_registro_4T2025.pdf` |
| `1c0070ba5d4d6775bc7de444f9f81bf4b300e3d09fef5635a27a7049cec31f0c` | 3,069,537 | `indec_eph_2025/EPH_usu_1_Trim_2025_txt.zip` |
| `c4f92368e2590daecd566368451a80a7935515b58059518a54152ea0897ed359` | 3,462,812 | `indec_eph_2025/EPH_usu_2_Trim_2025_txt.zip` |
| `02e16a62a8330fddd67bbdfb334d6638ae1ad02b6b4040851e1e5250246fa848` | 2,940,149 | `indec_eph_2025/EPH_usu_3_Trim_2025_txt.zip` |
| `7e523150c1da6bae28e35bfa9277d445208a6de73fc150c9f7d0d0b03c8a3473` | 2,894,565 | `indec_eph_2025/EPH_usu_4_Trim_2025_txt.zip` |
| `3fd9e9be9c5f89ef0e42e84ad3d83b29c37c61fe9a4c0b86ecd3ac8306f8f7d0` | 1,166,541 | `indec_eph_reports/EPHContinua_CIndividual.pdf` |
| `1e66ffc84c08df4d45f47889c457c2868d6ba9a39a19c5c3dc6763147a11e179` | 317,440 | `indec_eph_reports/cuadros_eph_informe_09_26.xls` |
| `28d794d8f76b0ddc1732d12ed9f9b08429a8d358a0bb9c56fd3fd1d1ef4e3685` | 344,064 | `indec_eph_reports/cuadros_tasas_indicadores_eph_09_26.xls` |
| `2fca82bd67358fa2d9449f85a018bc2141f525ad9b1ebb6e7198dbf09dec566d` | 109,056 | `indec_tic/cuadros_tic_05_25.xls` |
| `73db60f45e5b336841f855681a87f72feb5472e0ea358c1c143b6b9c853f94a0` | 1,130,276 | `indec_tic/mautic_05_25FD0D0C4A71.pdf` |
| `fb2d797e08185eba13136835ba439e43d4ba3ed33a97c47ca93b5cf7434c01c8` | 84,289 | `stackoverflow_survey/so_2025/ai.json` |
| `2d1f65308877282edfb4470520eabbc08cb499118432a3dcec6a66c086aa2baa` | 140,893,245 | `stackoverflow_survey/so_2025/results.csv` |
| `cae7f327e5c9d55ab0210b0c5a29f9ac3c233f38ac6bf81cbe83268c9b63187a` | 4,678,390 | `univ/adelanto_anuario_24_14-08.zip` |
| `e0676e9d56bd837723c43432aa91e2f74aa0eaf70d499f3abea62d3eca768306` | 8,464,271 | `univ/rv_anuario_finales_todos.zip` |
| `615c06cf7f764ed621614be3a4e7cc177ae962957c9be200464f1e70d47fecb0` | 32,829,802 | `univ/sintesis_anuario_2023-2024.pdf` |
