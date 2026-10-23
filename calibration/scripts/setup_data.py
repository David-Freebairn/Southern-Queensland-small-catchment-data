"""Load Wallumbilla data, build forcing for the Tilled (Scarify) catchment, and define scoring."""
import numpy as np
import pandas as pd
from wb_io import read_p51, read_soil, read_vege, read_sim
from wb_model import crop_seasons
from wb_watbal import build_forcing, run

D = "data/"
clim = read_p51(D + "Wallumbilla_trial.p51")
soil = read_soil(D + "Brown_sodosol.soil")
vege = read_vege(D + "Tilled_winterr_crop.vege")
cover = read_sim(D + "Soil_cover.sim")["Tilled_%"].astype(float)
ph = read_sim(D + "Plant_harvest_Yield.sim")
swobs_all = read_sim(D + "Soil_water.sim")
ro = read_sim(D + "Runoff_sediment.sim")

START, END = pd.Timestamp("1982-11-11"), pd.Timestamp("1999-12-31")
seasons = crop_seasons(ph)
forcing = build_forcing(clim, cover, seasons, START, END)

sw_obs = swobs_all["Scarify_PAW_mm_adjusted"].dropna()
site = swobs_all["Site_mean_PAW_mm"]
# Reset dates: start-of-fallow rows where the adjusted value equals the site mean
reset_dates = [d for d in sw_obs.index if abs(sw_obs[d] - site[d]) < 0.5]
resets = {d: sw_obs[d] for d in reset_dates}
sw_eval = sw_obs.drop(reset_dates)            # dates actually used to score soil water

ro_obs = ro["Till_runoff_mm"].astype(float)
ro_obs = ro_obs[(ro_obs.index >= pd.Timestamp("1983-01-01")) & (ro_obs.index <= pd.Timestamp("1997-12-31"))]
sed_obs = ro["Tilled_suspend_loss_t/ha"].astype(float)
# sediment counted only for runoff events with a recorded load, up to the last recorded load
last_sed = sed_obs[sed_obs > 0].index.max()
sed_ev = sed_obs[(ro_obs.reindex(sed_obs.index).fillna(0) > 0) & (sed_obs.index <= last_sed)]
sed_ev = sed_ev[~((sed_ev == 0) & (ro_obs.reindex(sed_ev.index) > 2))]   # zero load with real runoff = not sampled

yield_obs = np.array([s[2] for s in seasons])

SPLIT = pd.Timestamp("1991-01-01")   # calibrate before, validate after


def nse(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)


def scores(res, yields, period=None):
    def win(x):
        if period == "cal":
            return x[x.index < SPLIT]
        if period == "val":
            return x[x.index >= SPLIT]
        return x
    out = {}
    o = win(sw_eval); s = res["paw"].reindex(o.index)
    out["sw_rmse"] = float(np.sqrt(np.mean((o - s) ** 2))); out["sw_bias"] = float((s - o).mean())
    out["sw_nse"] = float(nse(o, s)); out["sw_n"] = len(o)
    o = win(ro_obs); s = res["runoff"].reindex(o.index)
    o3, s3 = o.rolling(3, center=True, min_periods=1).sum(), s.rolling(3, center=True, min_periods=1).sum()
    out["ro_nse3"] = float(nse(o3, s3)); out["ro_obs_tot"] = float(o.sum()); out["ro_sim_tot"] = float(s.sum())
    out["ro_bias_pct"] = 100 * (out["ro_sim_tot"] / out["ro_obs_tot"] - 1)
    o = win(sed_ev); s = res["sediment"].reindex(o.index)
    if len(o) > 2:
        out["sed_nse"] = float(nse(o, s)); out["sed_obs_tot"] = float(o.sum()); out["sed_sim_tot"] = float(s.sum())
    yi = pd.Series(yields, index=[s_[1] for s_ in seasons]); yo = pd.Series(yield_obs, index=yi.index)
    m = yo.notna()
    yo, yi = win(yo[m]), win(yi[m])
    out["y_rmse"] = float(np.sqrt(np.mean((yo - yi) ** 2))); out["y_bias"] = float((yi - yo).mean())
    out["y_r"] = float(np.corrcoef(yo, yi)[0, 1]) if len(yo) > 2 else np.nan
    return out


def simulate(p, use_resets=True):
    return run(D + "Brown_sodosol.soil", forcing, seasons, p, resets if use_resets else None, paw0=sw_obs.iloc[0])
