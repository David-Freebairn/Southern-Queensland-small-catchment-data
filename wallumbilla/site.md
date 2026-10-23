# Wallumbilla contour bay catchment study, 1982–2000

Full description, photographs, methods and related documents: `docs/Wallumbilla_background.docx`.

## Site
| | |
|---|---|
| Location | "Fairlands", Wallumbilla, 45 km east-north-east of Roma, Maranoa region, Queensland. 26°28′S, 149°06′E (−26.4667, 149.1000). The climate file header gives −26.28, 149.06, which is degrees.minutes, not decimal degrees |
| Soil | Brown clay (brigalow brown clay; brown sodosol in the model files), from glauconitic lithic sandstone. Hard-setting surface that seals quickly |
| Catchments | Four contour bay catchments, 2.4–5.9 ha |
| Slope / slope length | 1–3 % / 60–140 m |
| Channel | 290–660 m at 0.22 % to a grassed waterway |
| Runoff measurement | Four trapezoidal weirs |
| Sediment | Rising-stage samplers for suspended sediment. Total soil movement was not measured (rills and fans too indistinct on these slopes) |
| Climate | Mean annual rainfall 577 mm (1983–2000), 70 % Oct–Mar; pan evaporation ~2000 mm |
| Co-operators | Viv and Barbara Taylor, Rowan and Michael Taylor, "Fairlands"; Roma DPI (Gus Hamilton, Phil Rowland) |

| Bay | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Area (ha) | 3.7 | 4.0 | 5.9 | 2.4 |
| Slope (%) | 1–3 | 1–3 | 1–2 | 1–3 |
| Slope length (m) | 80–140 | 80–140 | 100–130 | 60–130 |
| Channel length (m) | 460 | 355 | 660 | 290 |
| Established | 14/12/1982 | 14/12/1982 | 14/12/1982 | 13/8/1985 |
| Reliable record | 1982–95 | 1982–95 | 1982–95 | 1985–95 |

## Treatments
Wheat sown annually (median 1 June), harvested early November; crop failures in 1987 and 1994. Treatments were applied by the farmer. Stubble was usually too light to burn and zero till was rarely practical, so differences between the two cropped treatments were subtle. Pasture (buffel grass and snail medic) was established in Bay 2 in 1990 and Bay 1 in 1996, and grazed Dec–Mar.

| Treatment (this package) | Original labels | Description |
|---|---|---|
| Tilled | Till, Tilled, Scarify, Chisel | Conventional tillage after wheat (scarifier or chisel) |
| Min till | ConTill, Min till, Mintill | Conservation/minimum tillage after wheat |
| Pasture | Pasture | Buffel grass pasture, from 1990 |

## Files
| File | Content | Period |
|---|---|---|
| `daily_climate.csv` | Site rainfall with SILO data for other variables | 1982–2000 |
| `daily_runoff_sediment.csv` | Continuous daily rain, runoff and suspended sediment load by treatment | 1982–1997 |
| `cover.csv` | Total cover, 74 dates | 1983–2000 |
| `soil_water.csv` | PAW and adjusted PAW 0–150 cm for Tilled (scarify and chisel bays), Min till and the site mean | 1982–1999 |
| `crops.csv` | Wheat plant, harvest, yield (one site value per season) | 1983–1999 |
| `soil_layers.csv` | Brown sodosol layers used in modelling | |
| `model_files/` | Original input files | |

## Conventions and known issues
- The runoff record is continuous and infilled: 0 means no runoff observed, not missing. Outside each bay's reliable period (above) zeros are infill. The 2026 calibration used Tilled to Dec 1997 and Min till to Jun 1995.
- Possible timing errors of ±1 day between rain and runoff.
- Soil water: when bays changed treatment, the site mean PAW for that day appears on the next day. The adjusted series sets all bays to the site mean at the start of each fallow (about November). The lower limit for 0–10 cm is fixed at 20.9 % g/g for all bays.
- Soil water for the Tilled treatment has two series, one for the scarified bay and one for the chisel bay (`implement` column). Both belong to the Tilled runoff record. The 2026 calibration used the Scarify series.
- 1985 has two sowing dates (re-sown 16 June).

## Key references
- Freebairn DM, Wockner GH, Hamilton NA, Rowland P (2009) Impact of soil conditions on hydrology and water quality for a brown clay in the north-eastern cereal zone of Australia. Aust J Soil Res 47, 389–402.
- Freebairn DM, Cutajar J (2011) Howleaky assessment – Wallumbilla ROSL study. Report for RRRD011.
- Ghahramani A, Freebairn DM, Sena DR, Cutajar JL, Silburn DM (2020) A pragmatic parameterisation and calibration approach to model hydrology and water quality of agricultural landscapes and catchments. Environ Model Softw 130, 104733.

## Custodian
Principal investigator DM Freebairn; data managers GH Wockner, DM Freebairn. Queensland Department of Natural Resources / Department of Primary Industries. Data custodian: Queensland Department of Natural Resources. Stated access policy: open access (base data in HYDSTRA, Qld Govt only, and DARTS, open via Qld Globe). Files carry © State of Queensland (DERM) 2012.
