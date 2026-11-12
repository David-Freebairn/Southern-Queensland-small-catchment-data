"""Revise fallow residue in each treatment's .vege file from measured cover, with one rule for all treatments.

Rule: measured total cover on fallow days (template green = 0) is ordered by days since harvest
(first DOY after the crop where green returns to 0 ... harvest knot); a non-increasing (isotonic) curve is fitted
(residue only breaks down or is buried during a fallow); each fallow knot's residue (z) becomes that curve's value
at the knot. Green (y), roots (a), planting day, crop knots and all other settings are unchanged."""
import re, os, json
import numpy as np, pandas as pd
from sklearn.isotonic import IsotonicRegression

SRC = '/home/claude/vege_in/'
OUT = '/home/claude/vege_revised/'
os.makedirs(OUT, exist_ok=True)
PKG = '/home/claude/pkg/data/'
FILES = {('Greenmount', 'Burnt'): ('f662d4be-Greenmount_wheat_stubble_burnt.vege', 'Greenmount_wheat_stubble_burnt.vege'),
         ('Greenmount', 'Incorporated'): ('0fdec9e9-Greenmount_wheat_stubble_incorporated.vege', 'Greenmount_wheat_stubble_incorporated.vege'),
         ('Greenmount', 'Mulch'): ('fddd63a9-Greenmountwheat_stubble_mulch.vege', 'Greenmount_wheat_stubble_mulch.vege'),
         ('Greenmount', 'Zero till'): ('20051265-Greenmount_Wheat_zero_till.vege', 'Greenmount_Wheat_zero_till.vege'),
         ('Greenwood', 'Burnt'): ('e42c7419-Greenwood_wheat_stubble_burnt.vege', 'Greenwood_wheat_stubble_burnt.vege'),
         ('Greenwood', 'Incorporated'): ('58981acd-Greenwood_wheat_stubble_incorporated.vege', 'Greenwood_wheat_stubble_incorporated.vege'),
         ('Greenwood', 'Mulch'): ('7f5f84f1-Greenwood_wheat_stubble_mulch.vege', 'Greenwood_wheat_stubble_mulch.vege'),
         ('Greenwood', 'Zero till'): ('558c0aed-Greenwood_Wheat_zero_till.vege', 'Greenwood_Wheat_zero_till.vege'),
         ('Wallumbilla', 'Tilled'): ('ec128add-Wall_chisel.vege', 'Wallumbilla_chisel.vege'),
         ('Wallumbilla', 'Min till'): ('5e7813dd-Wall_Minimum_tillage.vege', 'Wallumbilla_Minimum_tillage.vege')}
DATA_RE = r'<Data x="([\d.]+)" y="([\d.]+)" z="([\d.]+)" a="([\d.]+)"/>'

summary = []
for (site, trt), (src, dst) in FILES.items():
    s = open(SRC + src).read()
    knots = [(float(x), float(y), float(z), float(a)) for x, y, z, a in re.findall(DATA_RE, s)]
    doy = np.array([k[0] for k in knots]); green = np.array([k[1] for k in knots])
    # harvest = first knot after the in-crop period where green returns to 0
    incrop = np.where(green > 0)[0]
    h_idx = incrop[-1] + 1
    harvest = doy[h_idx]
    since = lambda d: (d - harvest) % 365                      # days since harvest
    c = pd.read_csv(PKG + site.lower() + '/cover.csv', parse_dates=['date'])
    c = c[c.treatment == trt].groupby('date').total_cover_pct.mean().dropna()
    if site == 'Greenwood' and trt == 'Zero till':
        c = c[c.index >= '1980-11-01']                         # treatment started Nov 1980
    cd = c.index.dayofyear.values
    gd = np.interp(cd, doy, green)
    fallow = gd == 0
    t, v = since(cd[fallow]), c.values[fallow]
    iso = IsotonicRegression(increasing=False, out_of_bounds='clip').fit(t, v)
    new = []
    for (x, y, z, a) in knots:
        if y == 0 and (x == harvest or since(x) > 0):          # fallow knot
            z2 = float(np.clip(np.round(iso.predict([since(x)])[0]), 0, 100))
        else:
            z2 = z
        new.append((x, y, z, z2, a))
    # rewrite z values in place (keep each element's exact formatting otherwise)
    it = iter(new)
    def rep(m):
        x, y, z, z2, a = next(it)
        zs = m.group(3) if z2 == z else f'{z2:g}'
        return f'<Data x="{m.group(1)}" y="{m.group(2)}" z="{zs}" a="{m.group(4)}"/>'
    s2 = re.sub(DATA_RE, rep, s)
    label = s2.split('text="')[1].split('"')[0]
    name = 'Wheat stubble burnt' if (site, trt) == ('Greenwood', 'Burnt') else label
    s2 = re.sub(r'text="[^"]*" Description="[^"]*"', f'text="{name} (residue revised Nov 2026)" Description="{name}: fallow residue fitted to measured cover, {site} {trt}"', s2, count=1)
    open(OUT + dst, 'w').write(s2)
    for x, y, z, z2, a in new:
        summary.append(dict(site=site, treatment=trt, file=dst, doy=int(x), green=y, residue_old=z, residue_new=z2,
                            fallow_knot=bool(y == 0 and (x == harvest or since(x) > 0))))
    print(f'{site:11s} {trt:13s} harvest DOY {int(harvest)}  n fallow obs {fallow.sum():3d}  ' +
          ' '.join(f'{int(x)}:{z:g}->{z2:g}' for x, y, z, z2, a in new if y == 0 and (x == harvest or since(x) > 0)))
pd.DataFrame(summary).to_csv(OUT + 'residue_changes.csv', index=False)
