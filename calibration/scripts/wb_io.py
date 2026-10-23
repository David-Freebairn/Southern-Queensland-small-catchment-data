"""Readers for the Wallumbilla calibration inputs (P51, HowLeaky .soil/.vege, .sim observations)."""
import re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd


def read_p51(path):
    rows = []
    with open(path) as f:
        for line in f:
            parts = re.split(r"[\s,]+", line.strip())
            if len(parts) >= 8 and re.fullmatch(r"\d{8}", parts[0]):
                rows.append([parts[0]] + [float(x) for x in parts[2:8]])
    df = pd.DataFrame(rows, columns=["date", "tmax", "tmin", "rain", "evap", "rad", "vp"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.set_index("date")


def _vals(el):
    n = int(el.get("Count"))
    return np.array([float(el.get(f"value{i}")) for i in range(1, n + 1)])


def read_soil(path):
    st = ET.parse(path).getroot().find("SoilType")
    g = lambda tag: float(st.find(tag).text)
    return dict(
        depth=_vals(st.find("LayerDepth")),                 # cumulative mm
        airdry=_vals(st.find("InSituAirDryMoist")) / 100,
        wp=_vals(st.find("WiltingPoint")) / 100,
        fc=_vals(st.find("FieldCapacity")) / 100,
        sat=_vals(st.find("SatWaterCont")) / 100,
        maxdrain=_vals(st.find("MaxDailyDrainRate")),
        U=g("Stage1SoilEvap_U"), cona=g("Stage2SoilEvap_Cona"),
        cn2=g("RunoffCurveNumber"), cn_red=g("RedInCNAtFullCover"),
        K=g("USLE_K"), P=g("USLE_P"), slope=g("FieldSlope"), slope_len=g("SlopeLength"),
        sdr=g("SedDelivRatio"),
    )


def read_vege(path):
    vt = ET.parse(path).getroot().find("VegetationType")
    g = lambda tag: float(vt.find(tag).text)
    m = np.array([[float(d.get(k)) for k in "xyza"] for d in vt.find("CropFactorMatrix")])
    return dict(plant_doy=g("PanPlantDay"), sw_nostress=g("SWPropForNoStress"),
                days_to_harvest=g("DaysPlantingToHarvest"), tue=g("WaterUseEffic"),
                hi=g("PanHarvestIndex"), matrix=m)


def read_sim(path):
    with open(path) as f:
        lines = [l for l in f if not l.startswith("//")]
    hdr_i = next(i for i, l in enumerate(lines) if l.lower().startswith("date"))
    from io import StringIO
    df = pd.read_csv(StringIO("".join(lines[hdr_i:])))
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed")
    return df.set_index("Date")


def crop_seasons(plant_harvest, end_default=150):
    """Pair each planting with the next harvest (last planting wins if replanted)."""
    ph = plant_harvest.sort_index()
    seasons, last_plant = [], None
    for d, row in ph.iterrows():
        if row.iloc[0] == 1:
            if last_plant is not None and (d - last_plant).days > 200:
                seasons.append((last_plant, last_plant + pd.Timedelta(days=end_default), np.nan))
            last_plant = d
        elif row.iloc[0] == 2 and last_plant is not None:
            seasons.append((last_plant, d, row.iloc[1]))
            last_plant = None
    if last_plant is not None:
        seasons.append((last_plant, last_plant + pd.Timedelta(days=end_default), np.nan))
    return seasons
