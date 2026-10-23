"""Build the three-site catchment benchmark package (tidy CSVs + model files + docs)."""
import io, json, re, shutil, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pandas as pd
import openpyxl

sys.path.insert(0, "/home/claude/calib")
from wb_io import read_sim, read_p51

OUT = Path("/home/claude/pkg/catchment-benchmarks")
UP = Path("/mnt/user-data/uploads")
GW = Path("/home/claude/gw/data")
GM = Path("/home/claude/gm/data")
ATT = Path("/mnt/user-data/attachments/b0a28d46-f32a-5471-99a8-8c34ab09c0d2")
if False:
    shutil.rmtree(OUT)

def w(df, site, name):
    p = OUT / site / name
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, float_format="%.6g", date_format="%Y-%m-%d")
    return df

def climate(path, site, rain_source):
    c = read_p51(str(path)).reset_index()
    c.columns = ["date", "tmax_c", "tmin_c", "rain_mm", "pan_evap_mm", "radiation_mj_m2", "vapour_pressure_hpa"]
    c["date"] = pd.to_datetime(c["date"]).dt.date
    return w(c, site, "daily_climate.csv")

def plant_harvest(df, flagcol, plant, harvest, yields):
    """Pair each planting with the next harvest before the following planting."""
    rows, cur = [], None
    for d, r in df.iterrows():
        f = r[flagcol]
        if f == plant:
            if cur is not None:
                rows.append(cur)
            cur = {"plant_date": d.date(), "harvest_date": None, **{k: np.nan for k in yields}}
        elif f == harvest and cur is not None:
            cur["harvest_date"] = d.date()
            for k, col in yields.items():
                cur[k] = r[col]
            rows.append(cur); cur = None
    if cur is not None:
        rows.append(cur)
    return pd.DataFrame(rows)

def soil_props(path, site):
    st = ET.parse(path).getroot().find("SoilType")
    keys = {"LayerDepth": "depth_bottom_mm", "InSituAirDryMoist": "air_dry_pct_vol", "WiltingPoint": "ll_pct_vol",
            "FieldCapacity": "dul_pct_vol", "SatWaterCont": "sat_pct_vol", "BulkDensity": "bulk_density_g_cm3",
            "PAWC": "pawc_mm", "MaxDailyDrainRate": "max_drain_rate_mm_day"}
    n = int(st.find("LayerDepth").get("Count"))
    d = {"layer": list(range(1, n + 1))}
    for k, col in keys.items():
        e = st.find(k)
        if e is not None:
            d[col] = [float(e.get(f"value{i}")) for i in range(1, n + 1)]
    df = pd.DataFrame(d)
    df.insert(1, "depth_top_mm", [0] + df["depth_bottom_mm"].tolist()[:-1])
    return w(df, site, "soil_layers.csv")

def model_files(site, files):
    m = OUT / site / "model_files"
    m.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy(f, m / Path(f).name)

def docs(site, docx):
    d = OUT / site / "docs"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(next(ATT.glob(f"*{docx}")), d / docx)

summary = {}

# ---------------- Wallumbilla ----------------
S = "wallumbilla"
cl = climate(UP / "Wallumbilla_trial.p51", S, "site")
ro = read_sim(str(UP / "Runoff_sediment.sim"))
T = {"Tilled": ("Till_runoff_mm", "Tilled_suspend_loss_t/ha"),
     "Min till": ("ConTill_runoff_mm", "ConTilled_suspend_loss_t/ha"),
     "Pasture": ("Pasture_runoff_mm", "Pasture_suspend_loss_t/ha")}
L = []
for t, (q, s) in T.items():
    L.append(pd.DataFrame({"date": ro.index.date, "treatment": t, "rain_mm": ro["Rain"].values,
                           "runoff_mm": ro[q].values, "suspended_sediment_t_ha": ro[s].values}))
rs = w(pd.concat(L), S, "daily_runoff_sediment.csv")
cv = read_sim(str(UP / "Soil_cover.sim"))
cvl = cv.rename(columns={"Tilled_%": "Tilled", "Min_Till_%": "Min till", "Pasture_%": "Pasture"}).stack().rename("total_cover_pct").reset_index()
cvl.columns = ["date", "treatment", "total_cover_pct"]
cvl["date"] = cvl["date"].dt.date
w(cvl.sort_values(["date", "treatment"]), S, "cover.csv")
sw = read_sim(str(UP / "Soil_water.sim"))
SWT = {"Site mean": ("Site_mean_PAW_mm", None), "Scarify": ("Scarify_PAW_mm", "Scarify_PAW_mm_adjusted"),
       "Chisel": ("Chisel_PAW_mm", "Chisel_PAW_mm_adjusted"), "Min till": ("Mintill_PAW_mm", "Mintill_PAW_mm_adjusted")}
L = []
for t, (a, b) in SWT.items():
    L.append(pd.DataFrame({"date": sw.index.date, "treatment": t, "paw_mm": sw[a].values,
                           "paw_adjusted_mm": sw[b].values if b else np.nan}))
swl = pd.concat(L).dropna(subset=["paw_mm", "paw_adjusted_mm"], how="all")
# Scarify and Chisel bays are both the Tilled treatment (D. Freebairn, 23 Oct 2026)
swl.insert(2, "implement", swl["treatment"].map({"Scarify": "Scarify", "Chisel": "Chisel"}))
swl["treatment"] = swl["treatment"].replace({"Scarify": "Tilled", "Chisel": "Tilled"})
swl = swl.sort_values(["date", "treatment", "implement"])
w(swl, S, "soil_water.csv")
ph = read_sim(str(UP / "Plant_harvest_Yield.sim"))
cr = plant_harvest(ph, "Plant_1_Harvest_2", 1, 2, {"yield_t_ha": "Wheat Yield (t/ha)"})
cr.insert(0, "treatment", "Crop catchments (all)"); cr.insert(1, "crop", "wheat")
w(cr, S, "crops.csv")
soil_props(UP / "Brown_sodosol.soil", S)
model_files(S, [UP / f for f in ["Wallumbilla_trial.p51", "Brown_sodosol.soil", "Tilled_winterr_crop.vege",
                                 "Soil_cover.sim", "Soil_water.sim", "Runoff_sediment.sim", "Plant_harvest_Yield.sim"]])
docs(S, "Wallumbilla_background.docx")
summary[S] = dict(climate=(cl.date.min(), cl.date.max()), runoff=rs.groupby("treatment").runoff_mm.sum().round(1).to_dict(),
                  cover=len(cvl), sw=len(swl), crops=len(cr))

# ---------------- Greenwood ----------------
S = "greenwood"
cl = climate(GW / "Greenwood.p51", S, "site + SILO Oakey")
ws = openpyxl.load_workbook(GW / "Greenwood_runoff_sediment_data.xlsx", data_only=True).worksheets[0]
rows = [r for r in ws.iter_rows(values_only=True)]
hi = next(i for i, r in enumerate(rows) if r[0] == "Date")
ev = pd.DataFrame(rows[hi + 1:], columns=rows[hi]).dropna(subset=["Date"])
ev["Date"] = pd.to_datetime(ev["Date"])
P = {"Burnt": "Burnt", "Incorporated": "Incorp", "Mulch": "Mulch", "Zero till": "Zero_till"}
L = []
for t, p in P.items():
    conc = "Zero-till_Sedconc_gm_L" if t == "Zero till" else f"{p}_Sedconc_gm_L"
    L.append(pd.DataFrame({"date": ev["Date"].dt.date, "treatment": t, "rain_mm": ev["Rainfall_mm"],
                           "runoff_mm": ev[f"{p}_Runoff_mm"], "soil_movement_t_ha": ev[f"{p}_Soil_movement_t_ha"],
                           "sediment_conc_g_l": ev[conc], "suspended_sediment_t_ha": ev[f"{p}_Suspended_sediment_t_ha"]}))
evl = pd.concat(L)
for c in ["rain_mm", "runoff_mm", "soil_movement_t_ha", "sediment_conc_g_l", "suspended_sediment_t_ha"]:
    evl[c] = pd.to_numeric(evl[c], errors="coerce")
evl = evl[~((evl.treatment == "Zero till") & (pd.to_datetime(evl.date) < "1980-11-01"))]
w(evl, S, "events_runoff_sediment.csv")
cv = read_sim(str(GW / "Cover.sim"))
cvl = cv.rename(columns={"Stubble_Burnt_%": "Burnt", "Stubble_Incorp_%": "Incorporated", "Stubble_mulch_%": "Mulch",
                         "ZT_%": "Zero till", "Summer_crop_%": "Summer crop"}).stack().rename("total_cover_pct").reset_index()
cvl.columns = ["date", "treatment", "total_cover_pct"]; cvl["date"] = cvl["date"].dt.date
w(cvl.sort_values(["date", "treatment"]), S, "cover.csv")
sw = read_sim(str(GW / "Soil_water_adjusted.sim"))
swl = sw.rename(columns={"Burnt_PAW_mm": "Burnt", "Incorp_PAW_mm": "Incorporated", "Mulch_PAW_mm": "Mulch",
                         "Mintill_PAW_mm": "Zero till"}).stack().rename("paw_adjusted_mm").reset_index()
swl.columns = ["date", "treatment", "paw_adjusted_mm"]; swl["date"] = swl["date"].dt.date
w(swl.sort_values(["date", "treatment"]), S, "soil_water.csv")
ph = read_sim(str(GW / "Plant_harvest_yield.sim"))
ph["flag"] = np.where(ph["Plant_date"] == 9, 9, np.where(ph["Harvest_date"] == 99, 99, 0))
cr = plant_harvest(ph, "flag", 9, 99, {"yield_kg_ha": "Wheat_Yield_kg_ha"})
cr["yield_t_ha"] = cr.pop("yield_kg_ha") / 1000
cr.insert(0, "treatment", "Crop catchments (all)"); cr.insert(1, "crop", "wheat")
w(cr, S, "crops.csv")
soil_props(GW / "Greenwood_Grey_clay.soil", S)
model_files(S, sorted(GW.iterdir()))
docs(S, "Greenwood_background.docx")
summary[S] = dict(climate=(cl.date.min(), cl.date.max()), runoff=evl.groupby("treatment").runoff_mm.sum().round(1).to_dict(),
                  sm=evl.groupby("treatment").soil_movement_t_ha.sum().round(1).to_dict(), cover=len(cvl), sw=len(swl), crops=len(cr))

# ---------------- Greenmount ----------------
S = "greenmount"
cl = climate(GM / "Greenmount_trial.P51", S, "site + SILO")
import gm_load
rain = cl.set_index(pd.to_datetime(cl.date))["rain_mm"]
L, C, W = [], [], []
for t in gm_load.FILES:
    d = gm_load.load(t)
    e = d[["runoff", "erosion", "suspended"]].dropna(how="all")
    L.append(pd.DataFrame({"date": e.index.date, "treatment": t, "rain_mm": rain.reindex(e.index).values,
                           "runoff_mm": e["runoff"].values, "soil_movement_t_ha": e["erosion"].values,
                           "suspended_sediment_t_ha": e["suspended"].values}))
    c = d[["cover", "rough"]].dropna(how="all")
    C.append(pd.DataFrame({"date": c.index.date, "treatment": t, "total_cover_pct": c["cover"].values,
                           "roughness_1to5": c["rough"].values, "source": f"Greenmount_{t}.sim"}))
    p = d["paw"].dropna()
    W.append(pd.DataFrame({"date": p.index.date, "treatment": t, "paw_mm": p.values}))
evl = pd.concat(L).reset_index(drop=True)
# Corrections confirmed by D. Freebairn, 23 Oct 2026 (logged in greenmount/corrections.csv)
dd = pd.to_datetime(evl["date"])
drop = (evl.treatment == "Burnt") & (dd == "1985-12-24")          # no runoff events in 1985
evl = evl[~drop]; dd = pd.to_datetime(evl["date"])
m = (evl.treatment == "Mulch") & dd.isin(pd.to_datetime(["1988-04-04", "1988-04-06", "1988-04-07"])) & (evl.soil_movement_t_ha == 9.999)
evl.loc[m, "soil_movement_t_ha"] = 0.0                            # 3 Apr value is the total for 3, 4, 6, 7 Apr 1988
evl = w(evl, S, "events_runoff_sediment.csv")
w(pd.DataFrame([
    {"date": "1985-12-24", "treatment": "Burnt", "column": "all", "original": "runoff 2.4 mm; soil movement 0.5 t/ha", "corrected": "row removed",
     "reason": "No runoff events occurred in 1985 (D. Freebairn, 2026)"},
    {"date": "1988-04-04; 1988-04-06; 1988-04-07", "treatment": "Mulch", "column": "soil_movement_t_ha", "original": "9.999", "corrected": "0",
     "reason": "Field sheet: total soil movement for events G70-G73 (3, 4, 6, 7 Apr 1988) was measured once and is recorded on 3 Apr; 9.999 was a placeholder"},
]), S, "corrections.csv")
gc = read_sim(str(GM / "Greenmount_cover.sim")).rename(columns={"Burnt_%": "Burnt", "Incorp_%": "Incorporated",
       "Mulch_%": "Mulch", "ZT_%": "Zero till", "Pasture_%": "Pasture"}).stack().rename("total_cover_pct").reset_index()
gc.columns = ["date", "treatment", "total_cover_pct"]; gc["date"] = gc["date"].dt.date
gc["roughness_1to5"] = np.nan; gc["source"] = "Greenmount_cover.sim"
cvl = pd.concat([gc] + C)
w(cvl.sort_values(["date", "treatment", "source"]), S, "cover.csv")
swl = w(pd.concat(W).sort_values(["date", "treatment"]), S, "soil_water.csv")
ph = read_sim(str(GM / "Plant_harvest_yield.sim"))
cr = plant_harvest(ph, "Plant_9_Harvest_99", 9, 99, {t: c for t, c in zip(gm_load.FILES, ["Burnt_yield_kg_ha", "Incorp_yield_kg_ha", "Mulch_yield_kg_ha", "ZT_yield_kg_ha"])})
crl = cr.melt(id_vars=["plant_date", "harvest_date"], var_name="treatment", value_name="yield_kg_ha")
crl["yield_t_ha"] = crl.pop("yield_kg_ha") / 1000; crl.insert(1, "crop", "wheat")
crl = crl[["treatment", "crop", "plant_date", "harvest_date", "yield_t_ha"]].sort_values(["plant_date", "treatment"])
w(crl, S, "crops.csv")
soil_props(GM / "Black_earth.soil", S)
model_files(S, sorted(GM.iterdir()))
docs(S, "Greenmount_background.docx")
summary[S] = dict(climate=(cl.date.min(), cl.date.max()), runoff=evl.groupby("treatment").runoff_mm.sum().round(1).to_dict(),
                  sm=evl.groupby("treatment").soil_movement_t_ha.sum().round(1).to_dict(), cover=len(cvl), sw=len(swl), crops=len(crl))
for k, v in summary.items():
    print(k, v)
