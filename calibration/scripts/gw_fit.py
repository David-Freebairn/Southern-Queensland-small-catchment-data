"""Greenwood pooled calibration: one soil, four treatments, observed cover.
Stage A soil water (Cona, U, bottom drain) -> Stage B runoff (CN2, CN reduction [, winter fraction]) x2
-> Stage C soil movement (K [, sediment winter fraction]). Suspended sediment = fitted fraction of soil movement.
Usage: python gw_fit.py linear|seasonal"""
import json, sys, time
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
import gw_setup as G
import gw_events as E

MODE = sys.argv[1] if len(sys.argv) > 1 else "seasonal"
OBS = {c["name"]: E.daily(c["name"]) for c in G.CATS}


def evaluate(p):
    out = {}; O3 = []; S3 = []; SMo = []; SMs = []; SWo = []; SWs = []
    for c in G.CATS:
        r, y, _ = G.sim(c, p)
        d = OBS[c["name"]]
        o = d["runoff"]; s = r["runoff"].reindex(o.index)
        o3 = o.rolling(3, center=True, min_periods=1).sum(); s3 = s.rolling(3, center=True, min_periods=1).sum()
        sm_o = d["soil_movement"]; sm_s = r["sediment"].reindex(o.index)
        # event totals for sediment (events grouped on observed or simulated runoff)
        evs = E.events(o, s, r["rain"])
        eo = np.array([sm_o.reindex(e["days"]).sum() for e in evs]); es = np.array([sm_s.reindex(e["days"]).sum() for e in evs])
        qo = np.array([o.reindex(e["days"]).sum() for e in evs]); qs = np.array([s.reindex(e["days"]).sum() for e in evs])
        rd = sorted(c["resets"])[1:]
        swo = pd.concat([c["sw_eval"], pd.Series({x: c["resets"][x] for x in rd})])
        sws = pd.concat([r["paw"].reindex(c["sw_eval"].index), pd.Series({x: r["paw"].get(x - pd.Timedelta(days=1)) for x in rd})])
        out[c["name"]] = dict(ro_po=float(s.sum() / o.sum()), ro_nse3=G.nse(o3, s3), ro_obs=float(o.sum()), ro_sim=float(s.sum()),
                              ev_ro_nse=G.nse(qo, qs), sm_po=float(sm_s.sum() / sm_o.sum()), sm_obs=float(sm_o.sum()), sm_sim=float(sm_s.sum()),
                              ev_sm_nse=G.nse(eo, es), sw_rmse=float(np.sqrt(np.mean((swo - sws) ** 2))),
                              events=[dict(start=str(e["start"].date()), q_obs=float(a), q_sim=float(b), sm_obs=float(x), sm_sim=float(z))
                                      for e, a, b, x, z in zip(evs, qo, qs, eo, es)])
        O3 += list(o3); S3 += list(s3); SMo += list(eo); SMs += list(es); SWo += list(swo); SWs += list(sws)
    out["pooled"] = dict(ro_nse3=G.nse(O3, S3), sm_nse=G.nse(SMo, SMs),
                         sw_rmse=float(np.sqrt(np.mean((np.array(SWo) - np.array(SWs)) ** 2))),
                         ro_po_dev=float(sum(abs(out[c["name"]]["ro_po"] - 1) for c in G.CATS)),
                         sm_po_dev=float(sum(abs(out[c["name"]]["sm_po"] - 1) for c in G.CATS)))
    return out


SW_N, SW_B = ["cona", "U", "log_ksat_bot"], [(1.5, 7), (0, 6), (-1, 1.7)]
RO_N = ["cn2", "cn_red"] + (["cover_winter_frac"] if MODE == "seasonal" else [])
RO_B = [(70, 97), (0, 40)] + ([(0, 1)] if MODE == "seasonal" else [])
SED_N = ["K"] + (["sed_winter_frac"] if MODE == "seasonal" else [])
SED_B = [(0.02, 2.0)] + ([(0, 1)] if MODE == "seasonal" else [])


def to_p(names, x, base):
    p = dict(base); d = dict(zip(names, x))
    for k in list(d):
        if k.startswith("log_"): d[k[4:]] = 10 ** d.pop(k)
    p.update(d); return p


def x_of(names, p): return [np.log10(p[n[4:]]) if n.startswith("log_") else p[n] for n in names]
def inb(x, B): return all(lo <= v <= hi for v, (lo, hi) in zip(x, B))


def f_sw(x, base):
    if not inb(x, SW_B): return 1e3
    return G.evaluate_sw(to_p(SW_N, x, base))["pooled"]["sw_rmse"]


def f_ro(x, base):
    if not inb(x, RO_B): return 1e3
    e = evaluate(to_p(RO_N, x, base))["pooled"]
    return (1 - e["ro_nse3"]) + e["ro_po_dev"] / 2


def f_sed(x, base):
    if not inb(x, SED_B): return 1e3
    e = evaluate(to_p(SED_N, x, base))["pooled"]
    return (1 - e["sm_nse"]) + e["sm_po_dev"] / 2


def fit(f, names, bounds, P, pop, iters=12, nm=50):
    x0 = [min(max(v, lo), hi) for v, (lo, hi) in zip(x_of(names, P), bounds)]
    r = differential_evolution(f, bounds, args=(P,), x0=x0, seed=11, popsize=pop, maxiter=iters, tol=1e-4,
                               polish=False, workers=2, updating="deferred")
    m = minimize(f, r.x, args=(P,), method="Nelder-Mead", options={"maxfev": nm})
    return to_p(names, m.x if m.fun < r.fun else r.x, P), float(min(m.fun, r.fun))


if __name__ == "__main__":
    t0 = time.time()
    P = json.load(open("/home/claude/gw/swfit.json"))["params"]
    P.update(cover_winter_frac=1.0, sed_winter_frac=1.0)
    start = evaluate(P)
    print(MODE, "start", {k: round(v, 3) for k, v in start["pooled"].items()}, flush=True)
    for it in range(2):
        P, v = fit(f_ro, RO_N, RO_B, P, 10)
        print(it, "RO", round(time.time() - t0), {k: round(P[k], 3) for k in RO_N}, round(v, 3), flush=True)
        P, v = fit(f_sw, SW_N, SW_B, P, 7)
        print(it, "SW", round(time.time() - t0), {k: round(P[k], 3) for k in ["cona", "U", "ksat_bot"]}, round(v, 2), flush=True)
    P, v = fit(f_ro, RO_N, RO_B, P, 10, iters=8)
    print("RO final", {k: round(P[k], 3) for k in RO_N}, round(v, 3), flush=True)
    P, v = fit(f_sed, SED_N, SED_B, P, 10, iters=10)
    print("SED", {k: round(P[k], 3) for k in SED_N}, round(v, 3), flush=True)
    e = evaluate(P)
    sdr = {c["name"]: float(OBS[c["name"]]["suspended"].sum() / OBS[c["name"]]["soil_movement"].sum()) for c in G.CATS}
    P = {k: (v if isinstance(v, str) or v is None else float(v)) for k, v in P.items()}
    json.dump({"params": P, "start": start, "after": e, "sdr_obs": sdr}, open(f"/home/claude/gw/fit_{MODE}.json", "w"), default=float, indent=1)
    for k in [c["name"] for c in G.CATS] + ["pooled"]:
        print(k, {m: round(v, 2) for m, v in e[k].items() if m != "events"})
    print(P, round(time.time() - t0), flush=True)
