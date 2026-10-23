# Reference calibration: Watbal2026, October 2026

These are reference results for the three sites, for others to compare against. The model is Watbal2026 (https://github.com/David-Freebairn/Watbal2026), a Python daily soil water balance descended from PERFECT and HowLeaky.

## Method
- **All data used.** No years were held out. At each site one parameter set covers all treatments, and the observed cover drives the differences between treatments.
- **Model structure:**
  - Runoff: SCS curve number with uncapped HowLeaky antecedent moisture (S = Smax(CN1)·(1 − wetness)).
  - Total cover = residue + (1 − residue)·green. Total cover reduces CN, erosion and soil evaporation; green cover alone drives transpiration.
  - Soil cracking is off.
- **Erosion:**
  - Wallumbilla uses the PERFECT sediment concentration–cover curve.
  - Greenwood and Greenmount use an exponential curve, conc ∝ exp(−b·cover%), with a seasonal (cosine) scaling of sediment.
- **Zero till:** its CN2 is raised by a fitted offset. Untilled surfaces have less roughness.
- **Soil water:** PAW is reset to the measured value at each fallow start and scored at every other measured profile, including the end-of-crop profile.
- **Optimisation:** scipy differential evolution, followed by a Nelder–Mead polish. It runs in stages: soil water → runoff → sediment.
- **Fit statistics:**
  - P:O is predicted ÷ observed total over the measured period.
  - Runoff NSE uses 3-day centred sums, because timing errors of ±1 day are real.
  - Event NSE uses grouped events.
  - PAW RMSE is in mm.

## Optimised parameters
| Parameter | Wallumbilla | Greenwood | Greenmount |
|---|---|---|---|
| CN2 (bare, tilled) | 92.2 | 93.6 | 90.2 |
| CN reduction at full cover | 8.0 | 15.1 | 14.2 |
| Zero-till CN2 offset | – | +5.0 | +5.4 |
| Sediment–cover curve | PERFECT | exp, b 0.095 | exp, b 0.057 |
| K (lumped erosion scale) | 0.149 | 0.80 | 0.62 |
| Sediment winter fraction | – | 0.015 | 0.31 |
| Cona / U | 3.33 / 4.8 | 5.1 / 4.7 | 6.96* / 0.01* |
| Bottom-layer drainage (mm/day) | 0.14 | 12 | 12 |
| No-stress PAW fraction | 0.75 | 0.2 | 0.2 |
| TUE / HI | 33.4 / 0.35 | 30 / 0.4 | 30 / 0.4 |
| Root extraction limit kl | 0.037 | – | – |
| Fallow weed green cover | 6 % (calibration code only) | – | – |

\* These values are not physical. At Greenmount the optimiser used soil evaporation to offset the crop over-using water.

K values can't be compared between sites, because the sediment–cover curves differ.

## Fit statistics
| Site / treatment | Runoff P:O | Runoff NSE (3-day) | Sediment P:O | Sediment event NSE | PAW RMSE (mm) |
|---|---|---|---|---|---|
| Wallumbilla Tilled | 1.00 | 0.73 | 1.04 | – | 40 (pooled) |
| Wallumbilla Min till | 1.00 | 0.68 | 0.95 | – | 40 (pooled) |
| Greenwood Burnt | 1.00 | 0.80 | 1.00 | 0.88 | 28 |
| Greenwood Incorporated | 1.02 | 0.74 | 1.23 | 0.81 | 24 |
| Greenwood Mulch | 0.99 | 0.73 | 0.91 | 0.82 | 29 |
| Greenwood Zero till | 1.00 | 0.82 | 1.00 | 0.74 | 29 |
| Greenmount Burnt | 1.00 | 0.79 | 1.17 | 0.82 | 51 |
| Greenmount Incorporated | 1.00 | 0.76 | 0.98 | 0.69 | 63 |
| Greenmount Mulch | 0.97 | 0.72 | 0.79 | 0.54 | 62 |
| Greenmount Zero till | 1.00 | 0.76 | 1.00 | 0.48 | 55 |

"Sediment" means suspended sediment loss at Wallumbilla, and total soil movement at Greenwood and Greenmount. Greenmount statistics cover April 1976 to April 1989.

The Greenmount fit was run before two corrections to the observed data (see `greenmount/corrections.csv`). Mulch observed soil movement included three 9.999 placeholders, so observed soil movement was 110.0 t/ha; corrected, it is 80.0 t/ha. Mulch soil movement P:O is therefore about 1.08, not 0.79. Removing the 24 Dec 1985 Burnt row changes Burnt runoff by 2.4 mm.

## Findings
- **CN–cover relationship.** The CN reduction with cover and the zero-till offset are almost identical at Greenwood and Greenmount. Base CN2 and the sediment–cover coefficient b are specific to each site and soil.
- **Event curve numbers at Greenwood** (summer events): CN = 54 − 19·cover + 95·wetness, R² 0.78. Wetness is the depth-weighted fraction between the lower limit and saturation. Winter events showed no cover effect.
- **Delivery ratio** (observed suspended sediment ÷ soil movement) is highest under zero till:
  - Greenwood: 0.14 / 0.20 / 0.21 / 0.46 (Burnt / Incorporated / Mulch / Zero till);
  - Greenmount: 0.11 / 0.11 / 0.08 / 0.21.
- **Crop water use.** End-of-crop PAW is unbiased only at Wallumbilla, which used the slower-root vege and the kl limit. At Greenwood and Greenmount the simulated crop dries the profile too much, and yields come out low.
- **No intensity data.** Event-level sediment is not expected to match closely without rainfall-intensity inputs. The target was P:O near 1.

## Files
- `Watbal2026_three_site_calibration_summary.xlsx`: parameters, fit statistics, crop and soil water.
- `parameter_files/`:
  - Wallumbilla 2026 soil and vege files;
  - Greenwood and Greenmount fitted parameter sets in JSON. Greenmount includes its fit statistics.
- `scripts/`: the calibration code as used. File paths are hard-coded for the original workspace and must be edited before use.
  - `wb_*`: shared input/output and model wrapper.
  - `setup_data.py`, `pooled*.py`: Wallumbilla.
  - `gw_*`: Greenwood.
  - `gm_*`: Greenmount.
