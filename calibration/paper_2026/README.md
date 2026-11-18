# Original vs revised Watbal2026: statistics and figures for the paper (18 Nov 2026)

Both models run through the Watbal2026 app engine (`core.run_simulation._run_daily`) for the ten contour bay catchments. Each run uses the site climate file, starts at the start of the climate record at 50 % PAWC, and has no soil water resets. Observations and measured periods come from the joint_2026 setup (package CSVs, with the Greenmount corrections applied).

| | Original | Revised |
|---|---|---|
| Soil files | packaged HowLeaky-era files (`<site>/model_files/*.soil`) | final 2026 site soils in Watbal2026 (`Soils/*2026*.soil`), with a zero-till file |
| Runoff AMC | capped (PERFECT); CN as entered | uncapped (HowLeaky); CN entered at average wetness 0.25 and converted internally |
| Soil evaporation | U and Cona from the soil file | U = 0; Cona fitted per site |
| Crop water use | no-stress PAW fraction 0.2 | 0.75; no kl |
| Soil movement | PERFECT concentration-cover curve × LS × K × Q | 16.52·exp(−0.057·cover%) × LS × K × Q |
| Suspended sediment | soil movement × the soil file's delivery ratio | A·exp(−0.0388·cover%) × Q/100 for Q > 1 mm, A per site |
| Cover, roots, crop dates | revised contour bay vege files | same files |

Using the same vege files in both isolates the model and parameter changes. The original treatment vege files are not in this repository.

## Files
- `Watbal2026_paper_tables.xlsx`: T1 configuration and parameters; T2 statistics by catchment; T3 by site and overall; figure list.
- `stats_by_catchment.csv`, `stats_pooled.csv`: the same statistics, unrounded.
- `figures/`: Fig1 cumulative runoff; Fig2 cumulative soil movement; Fig3 cumulative suspended sediment; Fig4 monthly observed vs predicted; Fig5 PAW observed vs predicted. Each as PNG (300 dpi) and PDF.
- `scripts/`: `paper_runs.py` (model runs; needs the joint_2026 setup and Watbal2026), `paper_stats.py`, `paper_figs.py`, `paper_xlsx.py`.

## Definitions
- **P:O** = predicted ÷ observed total over the measured days.
- **NSE** on 3-day centred sums of daily values, to allow ±1 day timing errors.
- **R²** on monthly totals.
- **PAW** = 0–150 cm plant available water at the sampling dates (RMSE, bias = predicted − observed, R²).
- **Pooled statistics** concatenate the catchments.

## Caveats
- There is no independent test: the revised parameters were fitted to these data (CN2, Cona per site, K and A rescaled to site P:O = 1). Site-level P:O near 1 is therefore partly built in. Differences between treatments, timing (NSE, R²) and PAW are the more informative comparison.
- Greenwood original U = 0 runs with the November 2026 evaporation reset fix. The pre-fix code evaporated much more after each rain.
- These runs start at the beginning of each climate record. The calibration-script runs started at the observation start, so PAW statistics differ slightly from the no_kl_nov2026 notes (most at Greenwood).
