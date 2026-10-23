"""Pooled calibration: tilled (scarify) + minimum-till catchments, one parameter set.
Objective is runoff first, with soil water as a soft constraint; sediment (K) fitted afterwards."""
import json, time
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize_scalar
from wb_io import read_p51, read_sim, crop_seasons
from wb_watbal import build_forcing, run

D = "data/"
clim = read_p51(D + "Wallumbilla_trial.p51")
ph = read_sim(D + "Plant_harvest_Yield.sim")
cov = read_sim(D + "Soil_cover.sim")
swf = read_sim(D + "Soil_water.sim")
ro = read_sim(D + "Runoff_sediment.sim").astype(float)
seasons = crop_seasons(ph)
START, END = pd.Timestamp("1982-11-11"), pd.Timestamp("1999-12-31")
SOIL = D + "Brown_sodosol.soil"


def catchment(name, cov_col, sw_col, ro_col, sed_col, ro_end):
    c = dict(name=name)
    c["forcing"] = build_forcing(clim, cov[cov_col].astype(float), seasons, START, END)
    sw = swf[sw_col].dropna(); site = swf["Site_mean_PAW_mm"]
    rd = [d for d in sw.index if abs(sw[d] - site[d]) < 0.5]
    c["resets"] = {d: sw[d] for d in rd}; c["sw_eval"] = sw.drop(rd); c["paw0"] = sw.iloc[0]
    q = ro[ro_col]; q = q[(q.index >= "1983-01-01") & (q.index <= ro_end)]
    c["ro"] = q
    s = ro[sed_col]; s = s[(q.reindex(s.index).fillna(0) > 0) & (s.index <= "1995-02-28")]
    c["sed"] = s[~((s == 0) & (q.reindex(s.index) > 2))]
    return c


CATS = [catchment("Tilled", "Tilled_%", "Scarify_PAW_mm_adjusted", "Till_runoff_mm", "Tilled_suspend_loss_t/ha", "1997-12-31"),
        catchment("Min till", "Min_Till_%", "Mintill_PAW_mm_adjusted", "ConTill_runoff_mm", "ConTilled_suspend_loss_t/ha", "1995-06-30")]


def nse(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)


def sim(c, p):
    return run(SOIL, c["forcing"], seasons, p, c["resets"], paw0=c["paw0"])[0]


def evaluate(p):
    out, O3, S3, SWo, SWs, SEo, SEs = {}, [], [], [], [], [], []
    for c in CATS:
        r = sim(c, p)
        o = c["ro"]; s = r["runoff"].reindex(o.index)
        o3 = o.rolling(3, center=True, min_periods=1).sum(); s3 = s.rolling(3, center=True, min_periods=1).sum()
        so, ss = c["sw_eval"], r["paw"].reindex(c["sw_eval"].index)
        eo, es = c["sed"], r["sediment"].reindex(c["sed"].index)
        out[c["name"]] = dict(ro_nse3=nse(o3, s3), ro_bias=100 * (s.sum() / o.sum() - 1), ro_obs=o.sum(), ro_sim=s.sum(),
                              sw_rmse=float(np.sqrt(np.mean((so - ss) ** 2))), sw_n=len(so),
                              sed_nse=nse(eo, es), sed_obs=eo.sum(), sed_sim=es.sum())
        O3 += list(o3); S3 += list(s3); SWo += list(so); SWs += list(ss); SEo += list(eo); SEs += list(es)
    out["pooled"] = dict(ro_nse3=nse(O3, S3), ro_bias=100 * (sum(S3) / sum(O3) - 1),
                         sw_rmse=float(np.sqrt(np.mean((np.array(SWo) - np.array(SWs)) ** 2))),
                         sed_nse=nse(SEo, SEs), sed_bias=100 * (sum(SEs) / sum(SEo) - 1))
    return out


BASE = json.load(open("calibrated2.json"))["params"]
NAMES = ["cn2", "cn_red", "cona", "U", "log_ksat_bot", "fallow_green"]
BOUNDS = [(72, 92), (0, 30), (2, 7), (0, 6), (-0.5, 1.0), (0.0, 0.08)]
SW_W = 0.3       # weight on soil-water RMSE (scaled by 30 mm) in the runoff objective


def to_p(x, base):
    p = dict(base); d = dict(zip(NAMES, x)); d["ksat_bot"] = 10 ** d.pop("log_ksat_bot"); p.update(d); return p


def objective(x, base):
    e = evaluate(to_p(x, base))["pooled"]
    return (1 - e["ro_nse3"]) + abs(e["ro_bias"]) / 100 + SW_W * e["sw_rmse"] / 30


if __name__ == "__main__":
    t0 = time.time()
    start = dict(BASE)
    before = evaluate(start)
    r = differential_evolution(objective, BOUNDS, args=(start,), seed=4, popsize=6, maxiter=18, tol=1e-4,
                               polish=False, workers=2, updating="deferred")
    P = to_p(r.x, start)
    print("runoff stage", round(time.time() - t0), {k: round(v, 3) for k, v in P.items()}, round(r.fun, 3), flush=True)

    # sediment: K on pooled events, with simulated runoff
    def sed_obj(k):
        p = dict(P); p["K"] = k; e = evaluate(p)
        return -e["pooled"]["sed_nse"] + abs(e["pooled"]["sed_bias"]) / 100
    P["K"] = float(minimize_scalar(sed_obj, bounds=(0.05, 1.0), method="bounded", options={"xatol": 1e-3}).x)
    after = evaluate(P)
    json.dump({"params": P, "before": before, "after": after}, open("pooled.json", "w"), default=float, indent=1)
    for lab, e in [("before", before), ("after", after)]:
        print(lab, {k: {m: round(v, 2) for m, v in d.items()} for k, d in e.items()})
    print(P, round(time.time() - t0))
