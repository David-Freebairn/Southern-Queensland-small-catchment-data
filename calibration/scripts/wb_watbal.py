"""Calibration wrapper around the real Watbal2026 daily engine (core/waterbalance.daily_water_balance).

Watbal2026 code is called unchanged. This wrapper only supplies:
  * observed total cover (interpolated) instead of the .vege residue schedule,
  * green cover and root depth by days-after-planting from the .vege matrix, on observed plant/harvest dates,
  * optional resets of the profile to measured PAW at the start of each fallow,
  * parameter overrides for calibration.
"""
import copy, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watbal2026"))
from core.waterbalance import daily_water_balance          # noqa: E402
from core.soil_xml import read_soil_xml                     # noqa: E402
from core.soil import SoilLayer                              # noqa: E402



def relayer(prof, bounds):
    """Re-discretise the profile onto new cumulative layer bottoms (mm).
    Each new layer takes thickness-weighted averages of the original horizons it spans,
    so total PAWC and storage are preserved; only the evaporation geometry changes."""
    old = prof.layers
    tops = [0.0] + [l.depth_mm for l in old[:-1]]
    new, prev = [], 0.0
    for b in bounds:
        w = [max(0.0, min(b, l.depth_mm) - max(prev, t)) for l, t in zip(old, tops)]
        tw = sum(w)
        avg = lambda attr: sum(wi * getattr(l, attr) for wi, l in zip(w, old)) / tw
        # drain rate: the slowest horizon spanned controls the layer
        ks = min(l.ksat for wi, l in zip(w, old) if wi > 0)
        th = b - prev
        ad, ll, dul, sat = avg("airdry"), avg("ll"), avg("dul"), avg("sat")
        new.append(SoilLayer(depth_mm=b, thickness=th, airdry=ad, ll=ll, dul=dul, sat=sat, ksat=ks,
                             ll_mm=ll * th, dul_mm=dul * th, sat_mm=sat * th, airdry_mm=ad * th,
                             pawc=(dul - ll) * th, bulk_density=avg("bulk_density")))
        prev = b
    prof.layers = new
    prof.pawc_total = sum(l.pawc for l in new)
    return prof

# .vege matrix (Scarify) re-expressed as days after planting (plant DOY 145)
DAP = np.array([0, 6, 36, 67, 98, 128, 400])
GREEN = np.array([0, 2, 15, 45, 80, 85, 85]) / 100
ROOT = np.array([0, 50, 192, 384, 816, 1400, 1500])

# "Wheat fallow slower roots" (Oct 2026): CropFactorMatrix DOY 145(plant)..300, as days after planting.
# Roots 100 mm at 36 DAP, 700 mm at 98, max 1200 mm at 135 (profile is 1500 mm).
# Green senescence (85% -> 0 over DOY 280-300) is anchored to the recorded harvest date.
# Greenwood wheat (all four .vege files share the in-crop rows; plant DOY 150): as days after planting
VEGE_GW = dict(dap=np.array([0, 12, 62, 93, 123, 155]),
               green=np.array([0, 0, 30, 85, 95, 95]) / 100,
               root=np.array([0, 0, 450, 1200, 1500, 1500]),
               senesce_days=20)

VEGE2 = dict(dap=np.array([0, 6, 36, 67, 98, 118, 135]),
             green=np.array([0, 2, 15, 45, 80, 85, 85]) / 100,
             root=np.array([0, 0, 100, 250, 700, 1000, 1200]),
             senesce_days=20)

FILE_PARAMS = dict(cn2=86.0, cn_red=10.0, U=4.0, cona=4.0, sw_prop=0.2, green_mult=1.0,
                   crop_factor=1.0, K=0.4, tue=25.0, hi=0.35, ksat_bot=0.1, fallow_green=0.0, amc_mode="howleaky", vege="scarify", cover_winter_frac=1.0, sed_winter_frac=1.0, sed_cover_coef=None,
                   kl=None, hi_stress=0.0, gf_days=35)


def build_forcing(clim, cover_obs, seasons, start, end):
    idx = pd.date_range(start, end, freq="D")
    f = pd.DataFrame(index=idx)
    f["rain"] = clim["rain"].reindex(idx).fillna(0).values
    f["epan"] = clim["evap"].reindex(idx).fillna(0).values
    dap = np.full(len(idx), -1.0); crop = np.full(len(idx), -1)
    for k, (p, h, _) in enumerate(seasons):
        m = (idx >= p) & (idx < h)
        dap[m] = (idx[m] - p).days.values; crop[m] = k
    f["dap"], f["crop"] = dap, crop
    tot = cover_obs.reindex(cover_obs.index.union(idx)).interpolate("time").reindex(idx)
    f["obs_total"] = tot.bfill().ffill().values / 100
    return f


def make_profile(soil_path, p):
    prof = read_soil_xml(soil_path)
    if p.get("bounds"):
        relayer(prof, p["bounds"])
    prof.cn2_bare = p["cn2"]; prof.cn_cover_reduction = p["cn_red"]
    prof.u = p["U"]; prof.cona = p["cona"]; prof.musle_k = p["K"]
    prof.amc_mode = p["amc_mode"]
    prof.kl = p["kl"]
    prof.cover_winter_frac = p["cover_winter_frac"]; prof.sed_winter_frac = p["sed_winter_frac"]
    prof.sed_cover_coef = p["sed_cover_coef"]
    prof.layers[-1].ksat = p["ksat_bot"] / 24.0   # bottom-layer MaxDailyDrainRate (mm/day -> mm/hr)
    return prof


def run(soil_path, forcing, seasons, params=None, resets=None, paw0=None):
    p = dict(FILE_PARAMS); p.update(params or {})
    prof = make_profile(soil_path, p)
    L = prof.layers
    pawc = np.array([l.dul_mm - l.ll_mm for l in L]); ll = np.array([l.ll_mm for l in L])
    frac0 = (paw0 / pawc.sum()) if paw0 is not None else 0.5
    sw = ll + pawc * frac0
    s1 = s2 = tw = 0.0
    resets = resets or {}
    dates = forcing.index
    rain, epan = forcing["rain"].values, forcing["epan"].values
    dap, crop, obs_tot = forcing["dap"].values, forcing["crop"].values, forcing["obs_total"].values
    n = len(dates)
    out = np.zeros((n, 10))
    T_season = np.zeros(len(seasons))
    gf_T = np.zeros(len(seasons)); gf_ep = np.zeros(len(seasons))
    slen = np.array([(h - pl).days for pl, h, _ in seasons])
    for d in range(n):
        if dates[d] in resets:
            fr = min(max(resets[dates[d]] / pawc.sum(), 0.0), 1.0)
            sw = ll + pawc * fr
            s1 = s2 = tw = 0.0
        if crop[d] >= 0:
            if p.get("vege") in ("slow_roots", "greenwood"):
                V = VEGE2 if p["vege"] == "slow_roots" else VEGE_GW
                g = np.interp(dap[d], V["dap"], V["green"])
                left = slen[crop[d]] - dap[d]                      # days to harvest
                if left < V["senesce_days"]:
                    g = min(g, V["green"][-1] * left / V["senesce_days"])
                g = min(1.0, g * p["green_mult"])
                rd = np.interp(dap[d], V["dap"], V["root"])
            else:
                g = min(1.0, np.interp(dap[d], DAP, GREEN) * p["green_mult"])
                rd = np.interp(dap[d], DAP, ROOT)
        else:   # fallow: optional weed green cover, shallow-rooted
            g, rd = p["fallow_green"], (600.0 if p["fallow_green"] > 0 else 0.0)
        tot = max(obs_tot[d], g)
        o = daily_water_balance(sw=sw, layers=L, soil=prof, rain=float(rain[d]), epan=float(epan[d]),
                                green_cover=g, total_cover=tot, root_depth_mm=rd,
                                crop_factor=p["crop_factor"], sumes1=s1, sumes2=s2, t_since_wet=tw,
                                sw_prop_no_stress=p["sw_prop"], doy=int(dates[d].dayofyear))
        sw, s1, s2, tw = o["sw"], o["sumes1"], o["sumes2"], o["t_since_wet"]
        paw = float(np.maximum(sw - ll, 0).sum())
        out[d] = [o["runoff"], o["soil_evap"], o["transp"], o["drainage"], o["sediment"], paw,
                  float(sw.sum()), g, o.get("sumh20", 0.0), o.get("S_value", 0.0)]
        if crop[d] >= 0:
            k = crop[d]
            T_season[k] += o["transp"]
            if dap[d] >= slen[k] - p["gf_days"]:          # grain-fill window before harvest
                gf_T[k] += o["transp"]; gf_ep[k] += epan[d] * g * p["crop_factor"]
    res = pd.DataFrame(out, index=dates, columns=["runoff", "soil_evap", "transp", "drainage",
                                                  "sediment", "paw", "sw_total", "green", "sumh20", "S"])
    res["rain"] = rain; res["total_cover"] = np.maximum(obs_tot, res["green"].values)
    gf_ratio = np.where(gf_ep > 0, gf_T / np.maximum(gf_ep, 1e-9), 1.0)
    hi_eff = p["hi"] * (1 - p["hi_stress"] * (1 - np.clip(gf_ratio, 0, 1)))
    yields = p["tue"] * T_season * hi_eff / 1000
    return res, yields, T_season
