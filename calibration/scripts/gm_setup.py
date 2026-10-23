"""Greenmount (1976-89): Black earth, four stubble treatments, observed cover drives each treatment."""
import numpy as np, pandas as pd
from wb_io import read_p51, read_sim
from wb_watbal import build_forcing, run
from gm_load import load, FILES

D = "/home/claude/gm/data/"
SOIL = D + "Black_earth.soil"
clim = read_p51(D + "Greenmount_trial.P51")
covsim = read_sim(D + "Greenmount_cover.sim").apply(pd.to_numeric, errors="coerce")
ph = read_sim(D + "Plant_harvest_yield.sim").apply(pd.to_numeric, errors="coerce")
plants = list(ph.index[ph.iloc[:, 0] == 9]); harvs = list(ph.index[ph.iloc[:, 0] == 99])
YCOL = {"Burnt": "Burnt_yield_kg_ha", "Incorporated": "Incorp_yield_kg_ha", "Mulch": "Mulch_yield_kg_ha", "Zero till": "ZT_yield_kg_ha"}
seasons = []
for p in plants:
    h = [x for x in harvs if x > p][0]
    seasons.append((p, h, np.nan))
START, END = pd.Timestamp("1976-04-25"), pd.Timestamp("1989-04-30")     # last recorded harvest Nov 1988
COVCOL = {"Burnt": "Burnt_%", "Incorporated": "Incorp_%", "Mulch": "Mulch_%", "Zero till": "ZT_%"}

CATS = []
for name in FILES:
    o = load(name)
    cv = pd.concat([o["cover"].dropna(), covsim[COVCOL[name]].dropna()]).groupby(level=0).mean().sort_index()
    c = dict(name=name, forcing=build_forcing(clim, cv, seasons, START, END))
    # measured years: years with any runoff row; unlisted days in those years are zero
    yrs = sorted(set(o["runoff"].dropna().index.year))
    idx = pd.date_range(START, END, freq="D"); m = idx.year.isin(yrs)
    first = o["runoff"].dropna().index.min(); m &= idx >= first
    c["obs"] = pd.DataFrame({"runoff": o["runoff"].reindex(idx).fillna(0.0), "soil_movement": o["erosion"].reindex(idx).fillna(0.0),
                             "suspended": o["suspended"].reindex(idx).fillna(0.0)})[m]
    # soil water: reset at the first sample after each harvest (fallow start); score the rest
    sw = o["paw"].dropna(); sw = sw[(sw.index >= START) & (sw.index <= END)]
    rd = []
    for h in harvs:
        after = sw[(sw.index > h) & (sw.index <= h + pd.Timedelta(days=75))]
        if len(after): rd.append(after.index[0])
    if sw.index[0] not in rd: rd = [sw.index[0]] + rd
    c["resets"] = {d: sw[d] for d in rd}; c["sw_eval"] = sw.drop(rd); c["paw0"] = sw.iloc[0]
    ys = ph[YCOL[name]].dropna(); ys = ys[ys > 0] / 1000
    c["yield_obs"] = ys
    CATS.append(c)


def sim(c, p, resets=True):
    if c["name"] == "Zero till" and p.get("zt_cn2_offset"):
        p = dict(p); p["cn2"] = p["cn2"] + p["zt_cn2_offset"]
    return run(SOIL, c["forcing"], seasons, p, c["resets"] if resets else None, paw0=c["paw0"])


def nse(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
