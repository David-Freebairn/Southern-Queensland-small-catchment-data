"""Round 6: soil cracking removed; total cover -> CN + soil evaporation, green -> transpiration;
runoff objective = 3-day NSE + |P:O-1| per catchment; K set for pooled sediment P:O = 1. Based on round 4: fixed engine (green-cover ET partition, kl extraction limit, AMC switch), pooled tilled + min till.
Soil water is scored at every measured profile, including the end-of-crop profiles at the fallow-start
reset dates (model value on the day before the reset). Deep drainage above 25 mm/yr is penalised.
Stages (all on all years): A soil water -> B runoff (x2), C yield (TUE + grain-fill stress on HI), D sediment K."""
import json, sys, time
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize, minimize_scalar
from pooled import CATS, seasons, SOIL, nse, ro
SED_END = pd.Timestamp("1995-02-28")
for _c, _col, _q in [(CATS[0], "Tilled_suspend_loss_t/ha", "Till_runoff_mm"), (CATS[1], "ConTilled_suspend_loss_t/ha", "ConTill_runoff_mm")]:
    _s = ro[_col][(ro.index >= "1983-01-01") & (ro.index <= SED_END)]
    _qq = ro[_q].reindex(_s.index)
    _bad = (_s == 0) & (_qq > 2)                       # runoff without a recorded load = not sampled
    _bad = _bad | _bad.shift(1, fill_value=False) | _bad.shift(-1, fill_value=False)
    _c["sed_window"] = _s[~_bad]
from wb_watbal import run

MODE = sys.argv[1] if len(sys.argv) > 1 else "howleaky"
DR_TARGET, DR_W = 25.0, 0.5          # mm/yr allowed before penalty; RMSE-mm per mm/yr over
yield_obs = pd.Series([s[2] for s in seasons], index=[s[1] for s in seasons]).dropna()


def evaluate(p):
    out, pooled = {}, {"O3": [], "S3": [], "swo": [], "sws": [], "eo": [], "es": [], "dr": [], "ys": []}
    for c in CATS:
        r, y, T = run(SOIL, c["forcing"], seasons, p, c["resets"], paw0=c["paw0"])
        o = c["ro"]; s = r["runoff"].reindex(o.index)
        o3 = o.rolling(3, center=True, min_periods=1).sum(); s3 = s.rolling(3, center=True, min_periods=1).sum()
        rd = sorted(c["resets"])[1:]
        swo = pd.concat([c["sw_eval"], pd.Series({d: c["resets"][d] for d in rd})])
        sws = pd.concat([r["paw"].reindex(c["sw_eval"].index),
                         pd.Series({d: r["paw"].get(d - pd.Timedelta(days=1)) for d in rd})])
        hv = pd.Series({d: c["resets"][d] for d in rd}); hs = pd.Series({d: r["paw"].get(d - pd.Timedelta(days=1)) for d in rd})
        eo, es = c["sed"], r["sediment"].reindex(c["sed"].index)
        sw_o = c["sed_window"]; sw_s = r["sediment"].reindex(sw_o.index)
        yrs = r[r.index >= "1983-01-01"]; dr = yrs["drainage"].sum() / yrs.index.year.nunique()
        ys = pd.Series(y, index=[s_[1] for s_ in seasons]).reindex(yield_obs.index)
        out[c["name"]] = dict(ro_nse3=nse(o3, s3), ro_bias=100 * (s.sum() / o.sum() - 1),
                              sw_rmse=float(np.sqrt(np.mean((swo - sws) ** 2))), sw_n=len(swo),
                              harvest_rmse=float(np.sqrt(np.mean((hv - hs) ** 2))), harvest_bias=float((hs - hv).mean()),
                              sed_nse=nse(eo, es), sed_po=float(sw_s.sum() / sw_o.sum()), sed_obs=float(sw_o.sum()), sed_sim=float(sw_s.sum()),
                              ro_po=float(s.sum() / o.sum()), drainage=dr,
                              soil_evap=yrs["soil_evap"].sum() / yrs.index.year.nunique(),
                              transp=yrs["transp"].sum() / yrs.index.year.nunique(),
                              runoff=yrs["runoff"].sum() / yrs.index.year.nunique())
        pooled["O3"] += list(o3); pooled["S3"] += list(s3); pooled["swo"] += list(swo); pooled["sws"] += list(sws)
        pooled["eo"] += list(sw_o); pooled["es"] += list(sw_s); pooled["dr"].append(dr); pooled["ys"].append(ys.values)
    ys = np.mean(pooled["ys"], axis=0)
    out["pooled"] = dict(ro_nse3=nse(pooled["O3"], pooled["S3"]), ro_bias=100 * (sum(pooled["S3"]) / sum(pooled["O3"]) - 1),
                         sw_rmse=float(np.sqrt(np.mean((np.array(pooled["swo"]) - np.array(pooled["sws"])) ** 2))),
                         sed_po=sum(pooled["es"]) / sum(pooled["eo"]),
                         drainage=float(np.mean(pooled["dr"])),
                         y_rmse=float(np.sqrt(np.mean((yield_obs.values - ys) ** 2))), y_r=float(np.corrcoef(yield_obs.values, ys)[0, 1]),
                         y_bias=float((ys - yield_obs.values).mean()))
    out["yields"] = {"obs": list(yield_obs.values), "sim": list(ys), "harvest": [str(d.date()) for d in yield_obs.index]}
    return out


SW_N, SW_B = ["cona", "U", "log_ksat_bot", "fallow_green", "log_kl", "sw_prop"], [(1.5, 7), (0, 6), (-1.0, 1.0), (0.0, 0.06), (-1.7, 0.0), (0.1, 0.8)]
RO_N, RO_B = ["cn2", "cn_red"], [(70, 97), (0, 30)]
Y_N, Y_B = ["tue"], [(10, 35)]


def to_p(names, x, base):
    p = dict(base); d = dict(zip(names, x))
    for k in list(d):
        if k.startswith("log_"): d[k[4:]] = 10 ** d.pop(k)
    p.update(d); return p


def x_of(names, p):
    return [np.log10(p[n[4:]]) if n.startswith("log_") else p[n] for n in names]


def inb(x, B): return all(lo <= v <= hi for v, (lo, hi) in zip(x, B))


def f_sw(x, base):
    if not inb(x, SW_B): return 1e3
    e = evaluate(to_p(SW_N, x, base))["pooled"]
    return e["sw_rmse"] + DR_W * max(0.0, e["drainage"] - DR_TARGET)


def f_ro(x, base):
    if not inb(x, RO_B): return 1e3
    E = evaluate(to_p(RO_N, x, base))
    return (1 - E["pooled"]["ro_nse3"]) + abs(E["Tilled"]["ro_po"] - 1) + abs(E["Min till"]["ro_po"] - 1)


def f_y(x, base):
    if not inb(x, Y_B): return 1e3
    return evaluate(to_p(Y_N, x, base))["pooled"]["y_rmse"]


def fit(f, names, bounds, P, pop, iters=14, nm=80):
    r = differential_evolution(f, bounds, args=(P,), x0=x_of(names, P), seed=9, popsize=pop, maxiter=iters,
                               tol=1e-4, polish=False, workers=2, updating="deferred")
    m = minimize(f, r.x, args=(P,), method="Nelder-Mead", options={"maxfev": nm, "xatol": 1e-3, "fatol": 1e-3})
    return to_p(names, m.x if m.fun < r.fun else r.x, P), float(min(m.fun, r.fun))


if __name__ == "__main__":
    t0 = time.time()
    P = json.load(open("pooled6_howleaky.json"))["params"]
    P.update(amc_mode=MODE, hi_stress=0.0, vege="slow_roots")
    start = evaluate(P)
    print(MODE, "start", {k: round(v, 2) for k, v in start["pooled"].items()}, flush=True)
    for it in range(2):
        P, v = fit(f_sw, SW_N, SW_B, P, 7)
        print(it, "SW", round(time.time() - t0), {k: round(P[k], 3) for k in ["cona", "U", "ksat_bot", "fallow_green", "kl", "sw_prop"]}, round(v, 2), flush=True)
        P, v = fit(f_ro, RO_N, RO_B, P, 10, iters=12, nm=50)
        print(it, "RO", round(time.time() - t0), {k: round(P[k], 3) for k in RO_N}, round(v, 3), flush=True)
    P, v = fit(f_y, Y_N, Y_B, P, 8, iters=10, nm=40)
    print("Y", round(time.time() - t0), {k: round(P[k], 3) for k in Y_N}, round(v, 3), flush=True)

    e0 = evaluate(P)["pooled"]["sed_po"]
    P["K"] = P["K"] / e0                     # sediment is linear in K: pooled P:O = 1
    P = {k: (v if isinstance(v, str) or v is None else float(v)) for k, v in P.items()}
    e = evaluate(P)
    json.dump({"params": P, "start": start, "after": e}, open(f"pooled7_{MODE}.json", "w"), default=float, indent=1)
    for k in ["Tilled", "Min till", "pooled"]:
        print(k, {m: round(v, 2) for m, v in e[k].items()})
    print(P, round(time.time() - t0), flush=True)
