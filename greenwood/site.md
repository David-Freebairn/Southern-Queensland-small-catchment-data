# Greenwood (Acland) contour bay catchment study, 1978–1984

Project code SMPA. Full description, photographs and methods: `docs/Greenwood_background.docx`.

## Site
| | |
|---|---|
| Location | Greenwood via Acland, 25 km north-west of Toowoomba, Queensland. 27°18′53.97″S, 151°44′06.96″E (−27.3150, 151.7353) |
| Soil | Grey clay (brigalow grey clay, Ug 5.16; Udic Chromustert; Moola clay association), from Walloon sandstone. Linear gilgai at 10–30 cm, salt bulge near 45 cm |
| Catchments | Five contour bay catchments, 0.72–1.00 ha |
| Slope / slope length | 4–5 % / 35–40 m (LS ≈ 0.6) |
| Channel | 220 m at 0.3 % to a grassed waterway |
| Runoff measurement | Five 90° V-notch weirs, 5-minute stage, summed to daily (9am–9am) |
| Sediment | Rising-stage samplers (some timed pump samples) for suspended concentration; total soil movement from rill and fan volumes after each major event |
| Co-operator | Mr Bill Bosse |

## Treatments
Four bays in winter wheat with a summer fallow, one bay in summer crop. Fallow treatments were rotated between bays to avoid bay effects. The design aimed to create a range of surface conditions, not to compare replicated treatments.

| Treatment (this package) | Description |
|---|---|
| Burnt | Wheat, stubble burnt, bare summer fallow |
| Incorporated | Wheat, disc tillage, stubble incorporated |
| Mulch | Wheat, blade or chisel tillage, stubble mulch |
| Zero till | Wheat, herbicide weed control, no tillage |
| Summer crop | Summer crop, chisel tillage, winter fallow (cover only) |

## Files
| File | Content | Period |
|---|---|---|
| `daily_climate.csv` | Site rainfall (pluviograph, 1978–84) with SILO Oakey Aero (−27.33, 151.62) for other variables and outside the study period | 1977–1984 |
| `events_runoff_sediment.csv` | Event rain, runoff, soil movement, sediment concentration, suspended load | Mar 1979 – Apr 1984 (Zero till from Nov 1980) |
| `cover.csv` | Total cover, 27 dates | Sep 1978 – Apr 1984 |
| `soil_water.csv` | Adjusted PAW 0–150 cm, 18 dates | Dec 1978 – Mar 1984 |
| `crops.csv` | Wheat plant, harvest, yield (one site value per season) | 1979–1984 |
| `soil_layers.csv` | Six-layer soil description used in modelling (PAWC 258 mm) | |
| `model_files/` | Original PERFECT/HowLeaky/Watbal2026 input files | |

## Conventions and known issues
- Days not listed in `events_runoff_sediment.csv` within the measured period had no runoff.
- Zero till was measured only from 1 November 1980; earlier rows are omitted.
- A sediment concentration of 0 alongside runoff usually means the event was not sampled.
- Soil water is the adjusted series: every bay is set to the site mean at the start of each fallow, then follows its own measured change.
- PAWC differs by source: 186 mm (background document, mean wettest − driest 1978–84), 240 mm (soil file comment), 258 mm (soil file layer sum). The 258 mm soil file was used in the 2026 calibration.

## Key references
- Freebairn DM, Wockner GH (1986) A study of soil erosion on vertisols of the eastern Darling Downs, Queensland. I. Effect of surface conditions on soil movement within contour bay catchments. Aust J Soil Res 24, 135–158.
- Freebairn DM, Wockner GH (1986) II. The effect of soil, rainfall and flow conditions on suspended sediment losses. Aust J Soil Res 24, 159–172.
- Freebairn DM, Boughton WC (1981) Surface runoff experiments in the eastern Darling Downs. Aust J Soil Res 19, 133–146.
- Ciesiolka CC, Freebairn DM (1982) The influence of scale on runoff and erosion. Agric Eng Conf, Inst Eng Aust, Nat Conf Publ 82/8, 203–206.

## Custodian
Principal investigator DM Freebairn; data managers DM Freebairn, GH Wockner. Queensland Department of Natural Resources / Department of Primary Industries. Data custodian: Queensland Department of Natural Resources (now the relevant Queensland Government department). Stated access policy: open access.
