"""Original vs revised Watbal2026 at the ten contour bay catchments, run through the app engine.

Original : packaged HowLeaky-era .soil files as they are (CN, CN reduction, Cona, U, K, drainage), capped AMC,
           PERFECT sediment curve, no-stress PAW fraction 0.2. Suspended sediment = soil movement x the soil
           file's sediment delivery ratio (PERFECT/HowLeaky practice).
Revised  : final 2026 soil files (uncapped AMC, CN at average wetness, exponential sediment curve, U 0) and the
           2026 contour bay vege files (no-stress 0.75). Suspended sediment = A * exp(-0.0388 cover%) * Q / 100
           for Q > 1 mm, A per site (Nov 2026 refit).
Both     : the same revised vege files for green cover, residue and roots (so the comparison isolates the model
           and parameter changes), climate files of each site, continuous run from 50 % PAWC, no resets.
Observations and measured windows: joint_2026 setup (package CSVs).
Run with COVER=vegefile VEGE_REV=1 (needed by joint_setup) from /home/claude/joint/scripts.
"""
import sys, io, contextlib, copy, json, pickle
sys.path.insert(0, '/home/claude/joint/scripts'); sys.path.insert(0, '/home/claude/Watbal2026')
import numpy as np, pandas as pd
import joint_setup as J
from core.soil_xml import read_soil_xml
from core.vege import read_vege
from core.read_p51 import read_p51
from core.run_simulation import _run_daily, _make_vege_fn

W = '/home/claude/Watbal2026/'
D = '/home/claude/southern-queensland-small-catchment-data/'
CLIM = {'Greenmount': 'Greenmount catchment.P51', 'Greenwood': 'Greenwood catchmenr.p51', 'Wallumbilla': 'Wallumbilla catchment.p51'}
OLD_SOIL = {'Greenmount': D + 'greenmount/model_files/Black_earth.soil', 'Greenwood': D + 'greenwood/model_files/Greenwood_Grey_clay.soil',
            'Wallumbilla': D + 'wallumbilla/model_files/Brown_sodosol.soil'}
NEW_SOIL = {('Greenmount', False): 'Greenmount_Black_earth_2026.soil', ('Greenmount', True): 'Greenmount_Black_earth_2026_zero_till.soil',
            ('Greenwood', False): 'Greenwood_Grey_clay_2026.soil', ('Greenwood', True): 'Greenwood_Grey_clay_2026_zero_till.soil',
            ('Wallumbilla', False): 'Wallumbilla_Brown_sodosol_2026.soil'}
VEGE = {('Greenmount', 'Burnt'): 'Greenmount_wheat_stubble_burnt', ('Greenmount', 'Incorporated'): 'Greenmount_wheat_stubble_incorporated',
        ('Greenmount', 'Mulch'): 'Greenmount_wheat_stubble_mulch', ('Greenmount', 'Zero till'): 'Greenmount_Wheat_zero_till',
        ('Greenwood', 'Burnt'): 'Greenwood_wheat_stubble_burnt', ('Greenwood', 'Incorporated'): 'Greenwood_wheat_stubble_incorporated',
        ('Greenwood', 'Mulch'): 'Greenwood_wheat_stubble_mulch', ('Greenwood', 'Zero till'): 'Greenwood_Wheat_zero_till',
        ('Wallumbilla', 'Tilled'): 'Wallumbilla_chisel', ('Wallumbilla', 'Min till'): 'Wallumbilla_Minimum_tillage'}
NK = json.load(open('/home/claude/joint/nokl_params.json'))
B_SS = 0.0388
SDR_OLD = {}

def sdr_from_file(path):
    import xml.etree.ElementTree as ET
    e = ET.parse(path).getroot().find('SoilType').find('SedDelivRatio')
    return float(e.text) if e is not None and e.text else 1.0

met = {}
for s, f in CLIM.items():
    with contextlib.redirect_stdout(io.StringIO()):
        lat, m = read_p51(W + 'Climate files/' + f)
    met[s] = m

out = {}
for k in J.CATS:
    s, t = k['site'], k['name']; zt = (t == 'Zero till')
    vf = W + 'Vegetation descriptions/Contour bay catchments 2026/' + VEGE[(s, t)] + '.vege'
    # revised
    pn = read_soil_xml(W + 'Soils/' + NEW_SOIL[(s, zt and s != 'Wallumbilla')])
    fn_new = _make_vege_fn(read_vege(vf))
    rn = _run_daily(met[s], pn, fn_new)[0]
    q = rn.runoff.values; cov = np.minimum(100, rn['total_cover'].values * 100) if 'total_cover' in rn else None
    # original
    po = read_soil_xml(OLD_SOIL[s])
    po.amc_mode = 'capped'
    if getattr(po, 'cn_input', None) is not None:
        po.cn2_bare = po.cn_input
    po.sed_cover_coef = None
    fn_old = _make_vege_fn(read_vege(vf)); fn_old._sw_prop_no_stress = 0.2
    ro = _run_daily(met[s], po, fn_old)[0]
    sdr = sdr_from_file(OLD_SOIL[s]); SDR_OLD[s] = sdr
    out[(s, t)] = dict(new=rn, old=ro, sdr_old=sdr, A_new=NK[s]['A'],
                       new_soil=dict(cn_input=pn.cn_input, cn_internal=pn.cn2_bare, cona=pn.cona, u=pn.u, K=pn.musle_k, amc=pn.amc_mode, b=pn.sed_cover_coef),
                       old_soil=dict(cn=po.cn2_bare, cn_red=po.cn_cover_reduction, cona=po.cona, u=po.u, K=po.musle_k, amc=po.amc_mode, sdr=sdr),
                       obs=dict(ro=k['ro'], sm=k.get('sm_win'), ss=k['ss_win'], paw=k['paw_obs']))
    print(s, t, 'new runoff', round(rn.runoff.sum()), 'old', round(ro.runoff.sum()), flush=True)
pickle.dump(out, open('/home/claude/paper/runs.pkl', 'wb'))
print(list(rn.columns))
