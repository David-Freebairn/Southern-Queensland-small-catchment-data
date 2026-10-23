# Greenmount contour bay catchment study, 1976–1993

Project code SMPG. Full description, photographs and methods: `docs/Greenmount_background.docx`.

## Site
| | |
|---|---|
| Location | "Marylands", 1.3 km north-east of Greenmount, Queensland. 27°46′S, 151°55′E (−27.7667, 151.9167). 500 m elevation, northerly aspect |
| Soil | Black earth (Ug 5.15), Irving clay association, from basalt. Strongly self-mulching, gross cracking when dry |
| Catchments | Five contour bay catchments, 0.71–1.44 ha (gauging stations AB42204–AB42208) |
| Slope / slope length | 6–7 % / 60–65 m (LS ≈ 1) |
| Channel | 250 m at 0.3 % to a grassed waterway |
| Runoff measurement | Four 0.61 m (2′) H-flumes and one 90° V-notch weir (Bay 0); 5-minute stage, summed to daily (9am–9am) |
| Sediment | Rising-stage samplers for suspended concentration; total soil movement from rill and fan volumes after each major event |
| Co-operator | Mr Terry Cuskelly |

| Bay | Station | Area (ha) | Structure |
|---|---|---|---|
| 0 | AB42204 | 0.711 | 90° V-notch weir |
| 1 | AB42205 | 1.320 | 2′ H-flume |
| 2 | AB42206 | 1.218 | 2′ H-flume |
| 3 | AB42207 | 1.157 | 2′ H-flume |
| 4 | AB42208 | 1.436 | 2′ H-flume |

## Treatments
Four bays in winter wheat with a summer fallow, one bay in summer crop (later pasture). Treatments were rotated between bays (1976–80) to avoid bay effects.

| Treatment (this package) | Description | Runoff record with events |
|---|---|---|
| Burnt | Wheat, stubble burnt, bare summer fallow | Oct 1976 – May 1990 |
| Incorporated | Wheat, disc tillage, stubble incorporated | Oct 1976 – Feb 1991 |
| Mulch | Wheat, blade tillage, stubble mulch | Sep 1978 – May 1990 |
| Zero till | Wheat, herbicide weed control (labelled minimum tillage in some tables) | Feb 1980 – Feb 1991 |
| Pasture | Perennial pasture, 1987–90 (cover only in this package) | |

## Files
| File | Content | Period |
|---|---|---|
| `daily_climate.csv` | Site rainfall (pluviograph) added to SILO base data | 1976–1993 |
| `events_runoff_sediment.csv` | Event rain, runoff, total soil movement, suspended load, by treatment | 1976–1993 |
| `cover.csv` | Total cover and roughness class; values from the site cover file and from each treatment file (`source` column) | 1976–1993 |
| `soil_water.csv` | PAW 0–150 cm, recalculated 2012 using each bay's lower limit | Dec 1978 – May 1993 |
| `crops.csv` | Wheat plant, harvest and yield by treatment | 1976–1988 |
| `soil_layers.csv` | Four-layer soil description (PAWC 288 mm) | |
| `corrections.csv` | Changes made to the original records, with reasons | |
| `model_files/` | Original input files, including per-treatment `.sim` files and vege descriptions | |

## Conventions and known issues
- Days not listed in `events_runoff_sediment.csv` within a treatment's measured period had no runoff.
- 1985 had no runoff events on any catchment: treat as zero. A stray Burnt row on 24 Dec 1985 in the original file has been removed.
- There was no Burnt treatment in 1989: treat Burnt as not measured from the 1988 harvest to the 1989 harvest, not as zero runoff.
- There was no Zero till treatment in 1988: treat it as not measured that year.
- Soil movement for the four events of 3, 4, 6 and 7 April 1988 (G70–G73) was measured once, after the last event, and is recorded on 3 April. Values on the following days are 0.
- Corrections made to the original files are listed in `corrections.csv`. The files in `model_files/` are unchanged originals.
- Rain on event days is taken from `daily_climate.csv`.
- Suspended sediment of 0 with positive soil movement usually means the event was not sampled ("some smaller events not sampled").
- Roughness 0 means not recorded (scale is 1–5).
- Runoff allocation between consecutive days may vary (event summary sheets vs Hydstra input).
- The original treatment files also carry `EMC_ppm_DR_0_14`, a derived value (14 % of soil movement) used for model comparison. It is not measured and is not in the tidy CSVs.
- The soil-water sample on 17 Nov 1987 falls before the recorded harvest and is better treated as an in-crop sample.
- PAWC: 250 mm (text), 201 mm (April 1977 table), 288 mm (soil file used in modelling).

## Key references
- Freebairn DM, Boughton WC (1981) Surface runoff experiments in the eastern Darling Downs. Aust J Soil Res 19, 133–146.
- Freebairn DM, Wockner GH (1986) A study of soil erosion on vertisols of the eastern Darling Downs, Queensland. I and II. Aust J Soil Res 24, 135–158 and 159–172.
- Ciesiolka CC, Freebairn DM (1982) The influence of scale on runoff and erosion. Agric Eng Conf, Inst Eng Aust, Nat Conf Publ 82/8, 203–206.

## Custodian and funding
Principal investigator DM Freebairn; data managers DM Freebairn, GH Wockner. Queensland Department of Natural Resources / Department of Primary Industries (DPI base funding). Data custodian: Queensland Department of Natural Resources. The 2012 re-evaluation was supported by the Reef Rescue Water Quality R&D Program (RRRD011) and GRDC (RPS00002); those files state a CC BY-NC 3.0 AU licence and © State of Queensland 2012.
