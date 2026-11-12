# Joint three-site calibration and model test: Watbal2026, November 2026

This folder follows on from the October 2026 reference calibration in `../`. That calibration fitted each site separately, driven by measured cover with soil water reset to measured profiles. This one asks a different question: **with one shared set of cover parameters, run the way a user would run it from soil and vege input files, how well does Watbal2026 reproduce long-term runoff, soil movement and suspended sediment at all three sites?**

Two analyses were kept separate:

1. **Model test (this folder's main results).** Watbal2026 driven by each site's soil file and each treatment's revised vege file, on daily climate, with no measured cover and no soil water resets. Parameters fitted jointly across all ten catchments on cumulative predicted ÷ observed (P:O). All data used; no years held out.
2. **Statistical event analysis (`event_analysis/`).** Relative impact of rain, prior rain, cover, roughness, rain since tillage, site, I30 and peak runoff rate on event runoff, soil movement and sediment concentration. No model involved.

## Revised vege files (`vege_revised/`)

The original vege files gave far more fallow residue than was measured on the high-residue treatments: Greenwood zero till 75–85% against about 55% measured, and Wallumbilla minimum tillage 55–70% against 15–50%. The fallow residue values in each file were refitted to the measured cover with one rule for all ten files:

- measured total cover on fallow days, ordered by days since harvest;
- a non-increasing (isotonic) curve fitted, since residue only breaks down or is buried during a fallow;
- each fallow residue value (`z`) set from that curve.

Green cover, root depth, planting day, the in-crop values and all other settings are unchanged. No multipliers are used (the `...BioMassTo...Factor` values stay at 1). The Greenwood burnt file is relabelled "Wheat stubble burnt" (it was labelled "incorporated" internally). `residue_changes.csv` lists every old and new value.

Points to note:
- Burnt files now carry the measured standing stubble between harvest and the burn (Greenmount 58%, Greenwood 29% just after harvest).
- Greenwood curves rest on 13–18 fallow cover observations per treatment.
- Greenwood zero till has data only from November 1980, when the treatment began. `greenwood/cover.csv` still holds 0% zero-till rows before that date; they were excluded here.
- The residue curves were fitted to cover measured on these catchments, so the vege files are calibrated inputs, not independent ones.

## Original vs new model (`results/`)

Both run from the revised vege files, vege-file planting dates and no-stress threshold (0.2), a continuous run from 50% PAWC, no fallow weeds.

- **Original:** the packaged `.soil` files as they are (CN2, CN reduction, Cona, U, K, drainage), capped AMC, no zero-till offset, PERFECT sediment curve, no suspended sediment model.
- **New:** HowLeaky AMC; shared CN reduction at full cover and zero-till offset; site CN2; site soil water parameters from the October reference calibration; exponential sediment curve with shared coefficient and site K; suspended sediment with a shared cover coefficient and site bare-soil concentration; seasonal sediment factor off.

| | Original | New |
|---|---|---|
| Runoff P:O (10 catchments) | 0.74–1.41 | 0.93–1.05 |
| Soil movement P:O (8 catchments) | 0.88–2.13 | 0.71–1.19 |
| Suspended sediment P:O (10 catchments) | not modelled | 0.78–1.28 |
| Mean PAW RMSE (mm) | 68 | 59 |

New-model parameters (`new_model_parameters.json`):

| Parameter | Greenmount | Greenwood | Wallumbilla | |
|---|---|---|---|---|
| CN2, bare tilled | 91.4 | 94.2 | 85.4 | site |
| CN reduction at full cover | 14.8 | 14.8 | 14.8 | shared |
| Zero-till CN2 offset | +5.4 | +5.4 | – | shared |
| Sediment cover coefficient (`SedCoverCoef`) | 0.057 | 0.057 | – | shared |
| K (LS 1.43 / 0.72 / 0.45) | 0.48 | 0.37 | – | site |
| Suspended cover coefficient | 0.039 | 0.039 | 0.039 | shared |
| Suspended conc. at bare soil (g/L) | 8.4 | 7.0 | 14.1 | site |

Soil movement = 16.52·e^(−b·cover%)·LS·K·P·runoff/10 and suspended = conc·runoff, both on days with more than 1 mm runoff. Total soil movement is compared only at Greenmount and Greenwood, where rills and fans were distinct; suspended sediment through the flumes and weirs is the water-quality measure common to all three sites.

Files:
- `watbal2026_original_vs_new.xlsx`: summary, parameters, fit statistics, cover curves (as formulas from the parameters) and cumulative series.
- `fit_statistics_original_vs_new.csv`: P:O, NSE and PAW RMSE by catchment.
- `cumulative_runoff.png`, `cumulative_soil_movement.png`, `cumulative_suspended_sediment.png`: cumulative observed vs predicted by catchment.
- `cover_vs_template.csv`: every measured cover observation beside the original vege-file value for that day of year.
- `joint_calibration_report.html`: interactive report (tables, cumulative curves, cover figures).

Known limitations:
- No independent evaluation: parameters were fitted and scored on the same data.
- K and the suspended bare-soil concentration are fitted per site, so site-level P:O near 1 is partly built in; the spread between treatments is the more informative test.
- Sediment and suspended sediment were calculated from the engine's daily runoff and total cover in the calibration scripts. The suspended sediment model is not yet in Watbal2026.
- Wallumbilla soil water is worse in the new model (PAW RMSE 54–56 mm against 41): with a no-stress threshold of 0.2 the profile stays too wet. Crop water use is still to do.
- Greenwood soil movement is dominated by one storm (7 February 1981), which daily-step models cannot reproduce.

## Event analysis (`event_analysis/`)

- `contour_bay_impacts.xlsx`: relative impact of event conditions on runoff, soil movement, total sediment concentration and TSS, with and without I30 and peak runoff rate (for interest; neither is available operationally).
- `cover_water_quality.xlsx`: cover–concentration relationships, PERFECT against the fitted exponential curves.

## Scripts (`scripts/`)

`joint_setup.py` (site inputs, observations, input-file mode), `joint_runoff.py` (shared runoff fit), `joint_sed.py` (sediment and suspended fits), `compare_final.py` (original vs new), `revise_vege.py` (residue refit), `make_final_xlsx.py`, and `wb_watbal.py` (the calibration wrapper from `../scripts/`, extended with a mode that reads green, residue and roots by day of year from a vege file). They import the setup scripts in `../scripts/` and contain absolute paths from the working environment; set those paths before re-running.
