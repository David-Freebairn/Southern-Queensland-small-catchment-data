# kl removed, U = 0, no-stress fraction 0.75: refit of Cona and CN2 (15 Nov 2026)

David's decision (15 Nov 2026) was to drop two arbitrary tuning parameters and handle profile drying through the crop description:
- remove the root extraction limit (kl) everywhere;
- use the revised vege file for each treatment and site;
- set the no-stress PAW fraction to 0.75 in every simulation;
- set U (stage I soil evaporation) to 0 everywhere;
- refit Cona and CN2 at each site.

Everything else is unchanged from the adopted November joint model (A2): input-file mode, no soil water resets, a 50 % PAWC start, CN reduction at full cover 14.77, zero-till CN2 offset +5.41, HowLeaky AMC, and bottom drainage as before.

## Method
For each site, a trial Cona fixes CN2 by root-finding so that the site's cumulative runoff P:O = 1. Cona is then chosen to minimise the site's PAW RMSE, pooled over its catchments (bounded scalar search). Afterwards, K (soil movement) and the suspended bare-soil concentration are rescaled so that site P:O = 1; their cover coefficients are unchanged. Scripts: `scripts/nokl_fit.py` and `scripts/nokl_eval.py`, which need the joint_2026 setup scripts. The search traces are in `fit_trace_*.log`.

## Engine fix needed for U = 0
With U = 0 the old code never reset days since wetting after rain, because the reset happens only in the stage I branch. Soil evaporation then ran at the potential rate after each rain until the stage II total caught up with Cona·√t, adding about 140–180 mm/yr of evaporation at these sites. Watbal2026 now resets days since wetting from the stage II total after rain: t = (sse2/Cona)². With U > 0, results are unchanged (checked on all ten catchments). This is in Watbal2026 pull request #4.

## Parameters
| | Greenmount | Greenwood | Wallumbilla |
|---|---|---|---|
| CN2 (A2 → new) | 91.4 → 90.6 | 94.2 → 94.9 | 85.4 → 95.6 |
| Cona (A2 → new) | 6.96 → 6.82 | 5.10 → 8.33 | 3.33 → 7.86 |
| U (A2 → new) | 0.01 → 0 | 4.68 → 0 | 4.8 → 0 |
| kl | – | – | 0.037 → removed |
| No-stress PAW fraction | 0.2 → 0.75 | 0.2 → 0.75 | 0.2 → 0.75 |
| K (soil movement) | 0.483 → 0.450 | 0.374 → 0.451 | – |
| Suspended bare-soil conc. (g/L) | 8.41 → 9.18 | 7.00 → 7.39 | 14.06 → 13.87 |

## Results, A2 → new (`fit_statistics_A2_vs_no_kl.csv`)
| | Greenmount | Greenwood | Wallumbilla |
|---|---|---|---|
| Runoff P:O | 0.98–1.02 → 0.97–1.02 | 0.93–1.04 → 0.95–1.05 | 0.98–1.05 → 0.97–1.02 |
| Runoff 3-day NSE | 0.71–0.79 → 0.71–0.78 | 0.72–0.85 → 0.71–0.84 | 0.42–0.61 → 0.65–0.72 |
| PAW RMSE (mm) | 59–69 → 28–50 | 51–62 → 40–52 | 54–56 → 33–38 |
| PAW bias (mm) | −45 to −22 → −5 to +11 | −1 to +13 → +7 to +20 | +35 → −9 |
| End-of-crop PAW, pred (obs) | 37–43 → 97–108 (104–113) | 13–14 → 48–49 (41) | 70–78 → 57–62 (58–64) |
| Yield, pred (obs) t/ha | 3.4–3.6 → 2.7–2.8 (2.8–3.1) | 2.3–2.6 → 1.4–1.7 (2.8) | 1.6–1.7 → 0.8–0.9 (1.3) |
| Soil movement P:O | 0.88–1.14 → 0.79–1.06 | 0.71–1.19 → 0.84–1.41 | – |
| Suspended P:O | 0.84–1.28 → 0.92–1.36 | 0.78–1.26 → 0.81–1.31 | 0.94–1.04 → 0.84–1.13 |
| Soil evaporation (mm/yr) | 371–405 → 415–448 | 403–420 → 469–483 | 318–323 → 403–408 |
| Transpiration (mm/yr) | 277–299 → 219–235 | 184–205 → 116–139 | 132–135 → 65–66 |

## Reading the results
- Soil water is much better at all three sites, and end-of-crop PAW is now about right at Greenmount and Wallumbilla. That is the main gain from the 0.75 no-stress fraction.
- Runoff is unchanged in quality. Wallumbilla runoff timing improves.
- Cona rises to 6.8–8.3 because, with U = 0, it now carries all of the soil evaporation after wetting.
- Wallumbilla CN2 rises by 10 units because the profile is now drier at the start of fallows.
- Greenwood zero-till CN2 is 100.3. That is valid under the HowLeaky AMC, which works from CN1, but it looks odd to users.
- **Yields are too low at Greenwood and Wallumbilla.** Transpiration halves and soil evaporation rises, so the soil water is right but too much of it leaves as evaporation rather than through the crop. This matches the earlier finding (cereal water-use curves, Oct 2026) that in-crop soil evaporation under a canopy is too high. That is the next thing to address.
