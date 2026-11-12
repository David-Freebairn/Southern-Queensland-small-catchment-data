"""Joint three-site setup: forcing, resets and site parameters from the reference calibrations;
observations from the published data package CSVs (includes the Greenmount corrections)."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/joint/scripts')
import gm_setup as GM, gw_setup as GW, pooled as WB
from wb_watbal import run

PKG = '/home/claude/pkg/data/'
PF = PKG + 'calibration/parameter_files/'

# ---- site reference parameters (soil water and crop held at these) ----
P_GW = json.load(open(PF + 'greenwood_model_H_params.json'))['params']
P_GM = json.load(open(PF + 'greenmount_model_H_params.json'))['params']
P_GW.update(ksat_bot=12.0)          # reference table value (file value 12; fitted 48 changes PAW RMSE by 1 mm)
P_WB = dict(vege='slow_roots', cn2=92.2, cn_red=8.0, cona=3.33, U=4.8, ksat_bot=0.14, K=0.149, kl=0.037,
            sw_prop=0.75, tue=33.4, hi=0.35, fallow_green=0.06, amc_mode='howleaky',
            cover_winter_frac=1.0, sed_winter_frac=1.0, sed_cover_coef=None)
WB_SOIL = PF + 'Brown sodosol Wallumbilla 2026.soil'

def ls_factor(slope, length):
    sys.path.insert(0, '/home/claude/joint/Watbal2026')
    from core.waterbalance import calc_ls_factor
    return calc_ls_factor(slope, length)
GEOM = {'Greenmount': (7, 60), 'Greenwood': (5, 35), 'Wallumbilla': (2, 100)}   # soil files
LS = {s: ls_factor(*g) for s, g in GEOM.items()}

# ---- observations from package CSVs ----
gm_ev = pd.read_csv(PKG + 'greenmount/events_runoff_sediment.csv', parse_dates=['date'])
gw_ev = pd.read_csv(PKG + 'greenwood/events_runoff_sediment.csv', parse_dates=['date'])
wb_d = pd.read_csv(PKG + 'wallumbilla/daily_runoff_sediment.csv', parse_dates=['date'])

def obs_gm(name, gmcat):
    e = gm_ev[gm_ev.treatment == name].groupby('date').sum(numeric_only=True)
    idx = gmcat['obs'].index                      # measured years mask from reference setup
    return pd.DataFrame({'runoff': e.runoff_mm.reindex(idx).fillna(0.0),
                         'soil_movement': e.soil_movement_t_ha.reindex(idx).fillna(0.0),
                         'suspended': e.suspended_sediment_t_ha.reindex(idx).fillna(0.0)})

GW_START = {'Burnt': '1979-01-01', 'Incorporated': '1979-01-01', 'Mulch': '1979-01-01', 'Zero till': '1980-11-01'}
def obs_gw(name):
    e = gw_ev[gw_ev.treatment == name].groupby('date').sum(numeric_only=True)
    idx = pd.date_range(GW_START[name], '1984-04-30', freq='D')
    return pd.DataFrame({'runoff': e.runoff_mm.reindex(idx).fillna(0.0),
                         'soil_movement': e.soil_movement_t_ha.reindex(idx).fillna(0.0),
                         'suspended': e.suspended_sediment_t_ha.reindex(idx).fillna(0.0)})

WB_RO_END = {'Tilled': '1997-12-31', 'Min till': '1995-06-30'}
def obs_wb(name, wbcat):
    e = wb_d[wb_d.treatment == name].set_index('date')
    q = e.runoff_mm[(e.index >= '1983-01-01') & (e.index <= WB_RO_END[name])]
    s = e.suspended_sediment_t_ha[(e.index >= '1983-01-01') & (e.index <= '1995-02-28')]
    qq = q.reindex(s.index)
    bad = (s == 0) & (qq > 2)                     # runoff without a recorded load = not sampled
    bad = bad | bad.shift(1, fill_value=False) | bad.shift(-1, fill_value=False)
    return q, s[~bad]

CATS = []
for c in GM.CATS:
    CATS.append(dict(site='Greenmount', name=c['name'], c=c, mod=GM, obs=obs_gm(c['name'], c)))
for c in GW.CATS:
    CATS.append(dict(site='Greenwood', name=c['name'], c=c, mod=GW, obs=obs_gw(c['name'])))
for c in WB.CATS:
    q, s = obs_wb(c['name'], c)
    CATS.append(dict(site='Wallumbilla', name=c['name'], c=c, mod=WB, ro=q, ss_win=s))
for k in CATS:
    if k['site'] != 'Wallumbilla':
        k['ro'] = k['obs'].runoff
        k['ss_win'] = k['obs'].suspended
        k['sm_win'] = k['obs'].soil_movement
SITEP = {'Greenmount': P_GM, 'Greenwood': P_GW, 'Wallumbilla': P_WB}

def simulate(k, over=None):
    """Run the engine for catchment k with its site's reference parameters plus overrides."""
    p = dict(SITEP[k['site']]); p.update(over or {})
    if k['name'] == 'Zero till' and p.get('zt_cn2_offset'):
        p['cn2'] = p['cn2'] + p['zt_cn2_offset']
    p['sed_cover_coef'] = None; p['sed_winter_frac'] = 1.0     # sediment done offline
    soil = WB_SOIL if k['site'] == 'Wallumbilla' else k['mod'].SOIL
    r, y, T = run(soil, k['c']['forcing'], k['mod'].seasons, p, k['c']['resets'], paw0=k['c']['paw0'])
    return r[['runoff', 'total_cover', 'rain', 'paw']]

def nse(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)


# ---- optional: residue from each treatment's .vege file (DOY template) instead of measured total cover ----
import os, re, copy, json
VEGE_DIR = '/home/claude/vege_in/'
VEGE_FILES = {('Greenmount', 'Burnt'): 'f662d4be-Greenmount_wheat_stubble_burnt.vege',
              ('Greenmount', 'Incorporated'): '0fdec9e9-Greenmount_wheat_stubble_incorporated.vege',
              ('Greenmount', 'Mulch'): 'fddd63a9-Greenmountwheat_stubble_mulch.vege',
              ('Greenmount', 'Zero till'): '20051265-Greenmount_Wheat_zero_till.vege',
              ('Greenwood', 'Burnt'): 'e42c7419-Greenwood_wheat_stubble_burnt.vege',
              ('Greenwood', 'Incorporated'): '58981acd-Greenwood_wheat_stubble_incorporated.vege',
              ('Greenwood', 'Mulch'): '7f5f84f1-Greenwood_wheat_stubble_mulch.vege',
              ('Greenwood', 'Zero till'): '558c0aed-Greenwood_Wheat_zero_till.vege',
              ('Wallumbilla', 'Tilled'): 'ec128add-Wall_chisel.vege',
              ('Wallumbilla', 'Min till'): '5e7813dd-Wall_Minimum_tillage.vege'}
def vege_residue(fname, idx):
    s = open(VEGE_DIR + fname).read()
    d = np.array([[float(x), float(z)] for x, y, z in re.findall(r'<Data x="([\d.]+)" y="([\d.]+)" z="([\d.]+)"', s)])
    doy = idx.dayofyear.values
    return np.interp(doy, d[:, 0], d[:, 1]) / 100.0
MEASURED_TOTAL = {(k['site'], k['name']): k['c']['forcing']['obs_total'].copy() for k in CATS}
if os.environ.get('COVER') == 'vege':
    for k in CATS:
        f = k['c']['forcing'].copy()
        f['obs_total'] = vege_residue(VEGE_FILES[(k['site'], k['name'])], f.index)
        k['c'] = dict(k['c']); k['c']['forcing'] = f
    for sp in SITEP.values():
        sp['cover_mode'] = 'vege'

# ---- pure input-file mode: green, residue and roots by DOY from each treatment's .vege file; no soil water resets ----
def vege_matrix(fname):
    s = open(VEGE_DIR + fname).read()
    d = np.array([[float(x), float(y), float(z), float(a)] for x, y, z, a in
                  re.findall(r'<Data x="([\d.]+)" y="([\d.]+)" z="([\d.]+)" a="([\d.]+)"', s)])
    sw = re.search(r'<SWPropForNoStress[^>]*>([\d.]+)<', s)
    return dict(doy=d[:, 0], green=d[:, 1] / 100, resid=d[:, 2] / 100, root=d[:, 3],
                sw_prop=float(sw.group(1)) if sw else 0.2)

if os.environ.get('VEGE_REV') == '1':
    import json as _j
    VEGE_DIR = '/home/claude/vege_revised/'
    _rev = {('Greenmount','Burnt'):'Greenmount_wheat_stubble_burnt.vege',('Greenmount','Incorporated'):'Greenmount_wheat_stubble_incorporated.vege',
            ('Greenmount','Mulch'):'Greenmount_wheat_stubble_mulch.vege',('Greenmount','Zero till'):'Greenmount_Wheat_zero_till.vege',
            ('Greenwood','Burnt'):'Greenwood_wheat_stubble_burnt.vege',('Greenwood','Incorporated'):'Greenwood_wheat_stubble_incorporated.vege',
            ('Greenwood','Mulch'):'Greenwood_wheat_stubble_mulch.vege',('Greenwood','Zero till'):'Greenwood_Wheat_zero_till.vege',
            ('Wallumbilla','Tilled'):'Wallumbilla_chisel.vege',('Wallumbilla','Min till'):'Wallumbilla_Minimum_tillage.vege'}
    VEGE_FILES.update(_rev)
if os.environ.get('COVER') == 'vegefile':
    for k in CATS:
        k['vm'] = vege_matrix(VEGE_FILES[(k['site'], k['name'])])
        if os.environ.get('VEGE_MULT') == '1':
            _m = json.load(open('/home/claude/joint/residue_multipliers.json'))[f"{k['site']}|{k['name']}"]
            k['vm']['resid'] = np.minimum(1.0, k['vm']['resid'] * _m)
        k['paw_obs'] = pd.concat([pd.Series(k['c']['resets']), k['c']['sw_eval']]).sort_index()
        k['c'] = dict(k['c']); k['c']['resets'] = {}; k['c']['paw0'] = None
    for sp in SITEP.values():
        sp['cover_mode'] = 'vege'; sp['fallow_green'] = 0.0
    _sim0 = simulate
    def simulate(k, over=None):
        o = dict(over or {}); o['vege_matrix'] = k['vm']; o['sw_prop'] = k['vm']['sw_prop']
        return _sim0(k, o)
