"""Greenwood (1978-84): one soil, one climate, four stubble treatments. Observed cover drives each treatment."""
import numpy as np
import pandas as pd
from wb_io import read_p51, read_sim
from wb_watbal import build_forcing, run

D = "/home/claude/gw/data/"
SOIL = D + "Greenwood_Grey_clay.soil"
clim = read_p51(D + "Greenwood.p51")
cov = read_sim(D + "Cover.sim").astype(float)
swf = read_sim(D + "Soil_water_adjusted.sim").astype(float)
ph = read_sim(D + "Plant_harvest_yield.sim")
plants = list(ph.index[ph["Plant_date"] == 9]); harvs = list(ph.index[ph["Harvest_date"] == 99])
seasons = []
for p in plants:
    h = [x for x in harvs if x > p]
    if h and (h[0] - p).days < 250:
        seasons.append((p, h[0], float(ph.loc[h[0], "Wheat_Yield_kg_ha"]) / 1000))
    else:
        seasons.append((p, p + pd.Timedelta(days=150), np.nan))
START, END = pd.Timestamp("1978-12-19"), pd.Timestamp("1984-12-31")

TREAT = [("Burnt", "Stubble_Burnt_%", "Burnt_PAW_mm"), ("Incorporated", "Stubble_Incorp_%", "Incorp_PAW_mm"),
         ("Mulch", "Stubble_mulch_%", "Mulch_PAW_mm"), ("Zero till", "ZT_%", "Mintill_PAW_mm")]
CATS = []
for name, ccol, swcol in TREAT:
    cv = cov[ccol].copy()
    if name == "Zero till":                                   # 0 before Nov 1980 = not yet recorded
        cv[(cv.index < "1980-11-01") & (cv == 0)] = np.nan
        cv = cv.dropna()
    c = dict(name=name, forcing=build_forcing(clim, cv, seasons, START, END))
    sw = swf[swcol].dropna(); first = sw.iloc[0]
    rd = [d for d in sw.index if (swf.loc[d].nunique() == 1)]           # common start-of-fallow value
    c["resets"] = {d: sw[d] for d in rd}; c["sw_eval"] = sw.drop(rd); c["paw0"] = first
    CATS.append(c)
yield_obs = pd.Series([s[2] for s in seasons], index=[s[1] for s in seasons]).dropna()


def sim(c, p, resets=True):
    if c["name"] == "Zero till" and p.get("zt_cn2_offset"):
        p = dict(p); p["cn2"] = p["cn2"] + p["zt_cn2_offset"]       # untilled surface: higher CN2
    return run(SOIL, c["forcing"], seasons, p, c["resets"] if resets else None, paw0=c["paw0"])


def nse(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)


def evaluate_sw(p):
    out, O, S = {}, [], []
    for c in CATS:
        r, y, T = sim(c, p)
        rd = sorted(c["resets"])[1:]
        so = pd.concat([c["sw_eval"], pd.Series({d: c["resets"][d] for d in rd})])
        ss = pd.concat([r["paw"].reindex(c["sw_eval"].index), pd.Series({d: r["paw"].get(d - pd.Timedelta(days=1)) for d in rd})])
        yrs = r[r.index >= "1979-01-01"]; ny = yrs.index.year.nunique()
        ys = pd.Series(y, index=[s_[1] for s_ in seasons]).reindex(yield_obs.index)
        out[c["name"]] = dict(sw_rmse=float(np.sqrt(np.mean((so - ss) ** 2))), sw_bias=float((ss - so).mean()), n=len(so),
                              runoff=yrs.runoff.sum() / ny, soil_evap=yrs.soil_evap.sum() / ny, transp=yrs.transp.sum() / ny,
                              drainage=yrs.drainage.sum() / ny, sediment=yrs.sediment.sum() / ny,
                              y_sim=list(np.round(ys.values, 2)))
        O += list(so); S += list(ss)
    out["pooled"] = dict(sw_rmse=float(np.sqrt(np.mean((np.array(O) - np.array(S)) ** 2))))
    return out
