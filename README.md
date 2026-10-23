# Queensland contour bay catchment benchmark data: Greenmount, Greenwood and Wallumbilla

These are long-term records from small contour bay catchments on cracking clay soils in southern Queensland, Australia. Each record has daily climate; runoff, soil movement and suspended sediment; and episodic soil water, surface cover and wheat yield, all under contrasting stubble and tillage management. The data were collected to relate soil surface condition to runoff, erosion and fallow water storage, and they form a benchmark for testing water-balance and water-quality models.

| Site | Lat, Long (decimal °) | Years | Soil | Catchments | Slope | Treatments | Rain (mm/yr) |
|---|---|---|---|---|---|---|---|
| Greenmount | −27.7667, 151.9167 | 1976–1993 | Black earth (Irving clay), basalt | 5 × 0.7–1.4 ha | 6–7 % | Stubble burnt, incorporated, mulch, zero till; pasture | ~730 |
| Greenwood (Acland) | −27.3150, 151.7353 | 1978–1984 | Grey clay (Moola clay) | 5 × 0.7–1.0 ha | 4–5 % | Stubble burnt, incorporated, mulch, zero till; summer crop | ~680 |
| Wallumbilla | −26.4667, 149.1000 | 1982–2000 | Brown clay (brown sodosol) | 4 × 2.4–5.9 ha | 1–3 % | Tilled, minimum till; pasture | ~580 |

## Layout
```
README.md               this file
data_dictionary.csv     every column: units, meaning, missing/zero conventions
datapackage.json        machine-readable description (Frictionless Data)
CITATION.cff            how to cite
LICENCE.md              CC BY 4.0 and attribution
<site>/
  site.md               location, catchments, treatments, methods, known issues, references
  daily_climate.csv
  daily_runoff_sediment.csv   (Wallumbilla: continuous daily)
  events_runoff_sediment.csv  (Greenmount, Greenwood: event days)
  cover.csv
  soil_water.csv
  crops.csv
  soil_layers.csv
  model_files/          original PERFECT / HowLeaky / Watbal2026 input files
  docs/                 full site background document (Word)
calibration/            reference Watbal2026 calibration (parameters, statistics, code)
```

## Using the data
- **Tables.** The CSVs are tidy: one row per date and treatment, dates in ISO format, units in the column names. They are the reference copy. The files in `model_files/` hold the same data in model input format.
- **Treatments.** Treatments were rotated between unreplicated bays. The aim was a range of surface conditions, not a replicated treatment comparison.
- **Runoff and sediment records.**
  - Wallumbilla is a continuous daily record, where 0 means no runoff.
  - Greenmount and Greenwood list event days only. Unlisted days within a treatment's measured period had no runoff.
  - Check each `site.md` for the measured periods and gaps.
  - A suspended sediment value of 0 when runoff occurred often means the event was not sampled.
- **Soil water** is PAW (0–150 cm) from nine cores per bay. Greenwood and Wallumbilla also have an "adjusted" series: all bays are set to the site mean at the start of each fallow. Use it to test fallow water accumulation, resetting simulated PAW at each fallow start.
- **Known limitation.** There are no rainfall-intensity data in this package. The original pluviograph records are held by the custodian.

## Provenance
- **Investigators and organisations.** Principal investigator DM Freebairn; data managers DM Freebairn and GH Wockner. Queensland Department of Natural Resources and Department of Primary Industries.
- **Original sources.** The data were compiled from field notes and the RRUMS and Hydstra databases (2007), and revised in 2012 and 2021.
- **Funding.** The 2012 re-evaluation was supported by the Reef Rescue Water Quality R&D Program (RRRD011) and GRDC (RPS00002).
- **Co-operating farmers.** Terry Cuskelly (Greenmount), Bill Bosse (Greenwood), and the Taylor family of "Fairlands" (Wallumbilla).

## Key publications
- Freebairn DM, Boughton WC (1981) Surface runoff experiments in the eastern Darling Downs. Aust J Soil Res 19, 133–146.
- Freebairn DM, Wockner GH (1986) A study of soil erosion on vertisols of the eastern Darling Downs, Queensland. I. Effect of surface conditions on soil movement within contour bay catchments. Aust J Soil Res 24, 135–158.
- Freebairn DM, Wockner GH (1986) II. The effect of soil, rainfall and flow conditions on suspended sediment losses. Aust J Soil Res 24, 159–172.
- Freebairn DM, Wockner GH, Hamilton NA, Rowland P (2009) Impact of soil conditions on hydrology and water quality for a brown clay in the north-eastern cereal zone of Australia. Aust J Soil Res 47, 389–402.
- Ghahramani A, Freebairn DM, Sena DR, Cutajar JL, Silburn DM (2020) A pragmatic parameterisation and calibration approach to model hydrology and water quality of agricultural landscapes and catchments. Environ Model Softw 130, 104733.

## Version
Version 1.0, October 2026. Compiled by David Freebairn.
