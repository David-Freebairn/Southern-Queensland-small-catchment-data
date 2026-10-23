"""Variants to separate the gains: sediment curve shape vs storm season, and a zero-till CN2 offset."""
import json, sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
import gw_fit as F

def fit(f, B, P, pop=10, iters=12, nm=60, x0=None):
    r = differential_evolution(f, B, args=(P,), x0=x0, seed=5, popsize=pop, maxiter=iters, tol=1e-4, polish=False, workers=2, updating="deferred")
    m = minimize(f, r.x, args=(P,), method="Nelder-Mead", options={"maxfev": nm})
    return (m.x if m.fun < r.fun else r.x), float(min(m.fun, r.fun))

class _Obj:
    """Picklable objective for parallel DE."""
    def __init__(self, names, B, kind): self.names, self.B, self.kind = names, B, kind
    def __call__(self, x, base):
        if not all(lo <= v <= hi for v, (lo, hi) in zip(x, self.B)): return 1e3
        p = dict(base); p.update(dict(zip(self.names, x))); e = F.evaluate(p)["pooled"]
        if self.kind == "sed":
            return (1 - e["sm_nse"]) + e["sm_po_dev"] / 2
        return (1 - e["ro_nse3"]) + e["ro_po_dev"] / 2

def sed_fit(P, names, B):
    x, v = fit(_Obj(names, B, "sed"), B, P); P = dict(P); P.update(dict(zip(names, map(float, x)))); return P

def ro_fit(P, names, B):
    x0 = [min(max(P.get(n, (lo + hi) / 2), lo), hi) for n, (lo, hi) in zip(names, B)]
    x, v = fit(_Obj(names, B, "ro"), B, P, x0=x0); P = dict(P); P.update(dict(zip(names, map(float, x)))); return P

def summ(lab, P):
    e = F.evaluate(P); T = ["Burnt", "Incorporated", "Mulch", "Zero till"]
    row = dict(label=lab, params={k: P[k] for k in ["cn2", "cn_red", "cover_winter_frac", "zt_cn2_offset", "K", "sed_cover_coef", "sed_winter_frac", "cona", "U", "ksat_bot"] if k in P},
               ro_nse3=e["pooled"]["ro_nse3"], sm_nse=e["pooled"]["sm_nse"], sw_rmse=e["pooled"]["sw_rmse"],
               ro_po=[e[t]["ro_po"] for t in T], sm_po=[e[t]["sm_po"] for t in T],
               ev_ro_nse=[e[t]["ev_ro_nse"] for t in T], ev_sm_nse=[e[t]["ev_sm_nse"] for t in T])
    print(lab, {k: (np.round(v, 2).tolist() if isinstance(v, list) else round(v, 3)) for k, v in row.items() if k not in ("label", "params")}, flush=True)
    print("   ", {k: round(v, 3) for k, v in row["params"].items() if v is not None}, flush=True)
    return row, e

if __name__ == "__main__":
    t0 = time.time(); out = {}
    L = json.load(open("/home/claude/gw/fit_linear.json"))["params"]
    S = json.load(open("/home/claude/gw/fit_seasonal.json"))["params"]
    SE = json.load(open("/home/claude/gw/fit_seasonal_exp.json"))["params"]
    out["A"] = summ("A linear CN, PERFECT sediment", L)[0]
    LE = sed_fit(dict(L, sed_cover_coef=0.05), ["K", "sed_cover_coef"], [(0.05, 5), (0.0, 0.2)])
    out["B"] = summ("B linear CN, exponential sediment", LE)[0]
    out["C"] = summ("C seasonal CN, PERFECT sediment + season", S)[0]
    SEn = sed_fit(dict(S, sed_cover_coef=0.05, sed_winter_frac=1.0), ["K", "sed_cover_coef"], [(0.05, 5), (0.0, 0.2)])
    out["D"] = summ("D seasonal CN, exponential sediment, no sed season", SEn)[0]
    out["E"] = summ("E seasonal CN, exponential sediment + season", SE)[0]
    # F: E plus zero-till CN2 offset (untilled, less roughness), refit runoff then sediment
    Z = ro_fit(dict(SE, zt_cn2_offset=4.0), ["cn2", "cn_red", "cover_winter_frac", "zt_cn2_offset"], [(80, 98), (0, 40), (0, 1), (0, 8)])
    Z = sed_fit(Z, ["K", "sed_cover_coef", "sed_winter_frac"], [(0.05, 5), (0.0, 0.2), (0.0, 0.5)])
    out["F"], eF = summ("F = E + zero-till CN2 offset", Z)
    # G: linear CN + zero-till offset + exponential sediment (no seasons anywhere)
    G_ = ro_fit(dict(L, zt_cn2_offset=4.0, sed_cover_coef=LE["sed_cover_coef"], K=LE["K"]), ["cn2", "cn_red", "zt_cn2_offset"], [(80, 98), (0, 40), (0, 8)])
    G_ = sed_fit(G_, ["K", "sed_cover_coef"], [(0.05, 5), (0.0, 0.2)])
    out["G"] = summ("G linear CN + zero-till offset, exponential sediment (no season)", G_)[0]
    json.dump(out, open("/home/claude/gw/variants.json", "w"), default=float, indent=1)
    json.dump({"params": Z, "after": eF}, open("/home/claude/gw/fit_final.json", "w"), default=float, indent=1)
    json.dump({"params": G_}, open("/home/claude/gw/fit_noseason.json", "w"), default=float, indent=1)
    print("done", round(time.time() - t0))
