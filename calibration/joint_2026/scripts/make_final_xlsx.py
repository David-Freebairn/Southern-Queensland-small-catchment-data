import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import ScatterChart, Reference, Series

D = json.load(open('/home/claude/joint/final_compare.json'))
C = D['curves']; S = D['stats']
F = 'Arial'
f = lambda **k: Font(name=F, **k)
BLUE, BOLD, NORM, H1, NOTE = f(color='0000FF'), f(bold=True), f(), f(bold=True, size=14), f(italic=True, size=9, color='555555')
YEL, HDR = PatternFill('solid', fgColor='FFFF00'), PatternFill('solid', fgColor='E8E6DE')
def hdr(ws, r, vals, c0=1):
    for j, v in enumerate(vals):
        c = ws.cell(r, c0 + j, v); c.font = BOLD; c.fill = HDR; c.alignment = Alignment(wrap_text=True, vertical='center')
SITES = ['Greenmount', 'Greenwood', 'Wallumbilla']
wb = Workbook()

# ---------------- Fit statistics (data the summary draws on)
st = wb.active; st.title = 'Fit statistics'
st['A1'] = 'Table 2. Fit statistics by catchment, original vs new model'; st['A1'].font = H1
st['A2'] = 'Both models run from the revised vege files, no soil water resets. P:O = cumulative predicted / observed over the measured period.'; st['A2'].font = NOTE
cols = [('Site', 'site'), ('Treatment', 'name'), ('Runoff observed (mm)', 'ro_obs'), ('Runoff P:O original', 'ro_po_old'), ('Runoff P:O new', 'ro_po_new'),
        ('Runoff NSE 3-day original', 'ro_nse_old'), ('Runoff NSE 3-day new', 'ro_nse_new'), ('Soil movement observed (t/ha)', 'sm_obs'),
        ('Soil movement P:O original', 'sm_po_old'), ('Soil movement P:O new', 'sm_po_new'), ('Suspended observed (t/ha)', 'ss_obs'),
        ('Suspended P:O new', 'ss_po_new'), ('PAW RMSE original (mm)', 'paw_rmse_old'), ('PAW RMSE new (mm)', 'paw_rmse_new')]
hdr(st, 4, [c[0] for c in cols])
for i, r in enumerate(S):
    for j, (_, k) in enumerate(cols):
        v = r.get(k)
        c = st.cell(5 + i, 1 + j, v if v is not None else None); c.font = NORM
        if isinstance(v, float):
            c.number_format = '0.0' if ('obs' in k or 'rmse' in k) else '0.00'
last = 4 + len(S)
st.cell(last + 1, 1, 'Blank = not applicable: Wallumbilla has no comparable total soil movement; the original model has no suspended sediment. Greenwood Zero till has data from November 1980 only.').font = NOTE
st.column_dimensions['A'].width = 13; st.column_dimensions['B'].width = 14
for j in range(3, 15): st.column_dimensions[L(j)].width = 13
st.freeze_panes = 'C5'

# ---------------- Summary (formulas over Fit statistics)
sm = wb.create_sheet('Summary', 0)
sm['A1'] = 'Watbal2026 joint calibration: original vs new model'; sm['A1'].font = H1
sm['A2'] = 'Ranges are formulas over the Fit statistics sheet.'; sm['A2'].font = NOTE
hdr(sm, 4, ['Measure', 'Original min', 'Original max', 'New min', 'New max'])
rng = lambda col: f"'Fit statistics'!{col}5:{col}{last}"
rows = [('Runoff P:O (10 catchments)', 'D', 'E', '0.00'), ('Runoff NSE, 3-day', 'F', 'G', '0.00'),
        ('Soil movement P:O (8 catchments)', 'I', 'J', '0.00'), ('Suspended sediment P:O (10 catchments)', None, 'L', '0.00'),
        ('PAW RMSE (mm)', 'M', 'N', '0')]
for i, (lab, co, cn, fmt) in enumerate(rows):
    r = 5 + i; sm.cell(r, 1, lab).font = NORM
    if co:
        sm.cell(r, 2, f'=MIN({rng(co)})').number_format = fmt; sm.cell(r, 3, f'=MAX({rng(co)})').number_format = fmt
    else:
        sm.cell(r, 2, 'not modelled').font = NOTE
    sm.cell(r, 4, f'=MIN({rng(cn)})').number_format = fmt; sm.cell(r, 5, f'=MAX({rng(cn)})').number_format = fmt
sm['A11'] = 'Mean PAW RMSE (mm)'; sm['B11'] = f"=AVERAGE({rng('M')})"; sm['D11'] = f"=AVERAGE({rng('N')})"
sm['B11'].number_format = sm['D11'].number_format = '0'
notes = ['Original model: original .soil files as packaged (CN2, CN reduction, U, Cona, K, drainage), capped AMC, no zero-till offset, PERFECT sediment curve, no suspended sediment.',
         'New model: HowLeaky AMC, shared CN-cover reduction and zero-till offset, site CN2, site soil water parameters from reference calibrations, exponential sediment curve (shared b, site K), suspended sediment (shared b, site bare-soil concentration), seasonal factor off.',
         'Both: revised vege files (fallow residue fitted to measured cover; green, roots, planting day unchanged; no multipliers), no-stress threshold 0.2, continuous run from 50% PAWC, no fallow weeds.',
         'Wallumbilla PAW is worse in the new model (54-56 vs 41 mm): the vege no-stress threshold of 0.2 leaves the profile too wet. Crop water use still to do.']
for i, t in enumerate(notes):
    c = sm.cell(13 + i, 1, t); c.font = NORM; c.alignment = Alignment(wrap_text=True, vertical='top')
    sm.merge_cells(start_row=13 + i, start_column=1, end_row=13 + i, end_column=5); sm.row_dimensions[13 + i].height = 42
sm.column_dimensions['A'].width = 40
for col in 'BCDE': sm.column_dimensions[col].width = 14

# ---------------- Parameters
pa = wb.create_sheet('Parameters', 1)
pa['A1'] = 'Table 1. Parameters, original vs new'; pa['A1'].font = H1
pa['A2'] = 'Blue/yellow = model parameter values (inputs for the Cover sheets). Original values are from the packaged .soil files; new values from the joint fit.'; pa['A2'].font = NOTE
hdr(pa, 4, ['Parameter', 'Original Greenmount', 'Original Greenwood', 'Original Wallumbilla', 'New Greenmount', 'New Greenwood', 'New Wallumbilla', 'In the new model'])
O, N = C['orig'], C['new']
P = [('CN2, bare tilled', [O[s]['cn2'] for s in SITES], [N['cn2'][s] for s in SITES], 'Site (soil)', '0.0'),
     ('CN reduction at full cover', [O[s]['cn_red'] for s in SITES], [N['cn_red']] * 3, 'Shared', '0.0'),
     ('Zero-till CN2 offset', [0, 0, 0], [N['zt']] * 3, 'Shared', '0.0'),
     ('AMC mode', ['capped'] * 3, ['HowLeaky'] * 3, 'All sites', None),
     ('Cona', [O[s]['cona'] for s in SITES], [6.96, 5.10, 3.33], 'Site', '0.00'),
     ('U', [O[s]['U'] for s in SITES], [0.01, 4.68, 4.80], 'Site', '0.00'),
     ('Bottom-layer drainage (mm/day)', [O[s]['ksat_bot'] for s in SITES], [12, 12, 0.14], 'Site', '0.00'),
     ('LS (from soil file slope and length)', [C['LS'][s] for s in SITES], [C['LS'][s] for s in SITES], 'Site', '0.000'),
     ('K', [O[s]['K'] for s in SITES], [N['K']['Greenmount'], N['K']['Greenwood'], None], 'Site', '0.000'),
     ('Sediment cover coefficient b (per % cover)', ['PERFECT'] * 3, [N['b_sm']] * 3, 'Shared (SedCoverCoef)', '0.0000'),
     ('Bare-soil sediment concentration (g/L)', [16.52] * 3, [16.52] * 3, 'Fixed', '0.00'),
     ('Suspended cover coefficient (per % cover)', [None] * 3, [N['b_ss']] * 3, 'Shared', '0.0000'),
     ('Suspended conc. at bare soil (g/L)', [None] * 3, [N['A'][s] / 1000 for s in SITES], 'Site', '0.00'),
     ('Seasonal sediment factor', ['off'] * 3, ['off'] * 3, '', None)]
PROW = {}
for i, (n, ov, nv, sh, fmt) in enumerate(P):
    r = 5 + i; PROW[n] = r; pa.cell(r, 1, n).font = NORM
    for j, v in enumerate(ov + nv):
        c = pa.cell(r, 2 + j, v)
        c.font = BLUE if isinstance(v, (int, float)) else NORM
        if isinstance(v, (int, float)):
            c.fill = YEL
            if fmt: c.number_format = fmt
    pa.cell(r, 8, sh).font = NORM
pa.cell(20, 1, 'Wallumbilla: no K, as total soil movement was not comparably measured. PERFECT curve: 16.52 - 0.46C + 0.0031C^2 below 50% cover, 2.54 - 0.0254C above.').font = NOTE
pa.column_dimensions['A'].width = 42
for j in range(2, 8): pa.column_dimensions[L(j)].width = 13
pa.column_dimensions['H'].width = 22

# ---------------- Cover vs soil movement (formulas from Parameters)
def ref(name, site, new=True):
    col = {('Greenmount', False): 'B', ('Greenwood', False): 'C', ('Wallumbilla', False): 'D',
           ('Greenmount', True): 'E', ('Greenwood', True): 'F', ('Wallumbilla', True): 'G'}[(site, new)]
    return f"Parameters!${col}${PROW[name]}"
cs = wb.create_sheet('Cover vs soil movement')
cs['A1'] = 'Figure 2. Cover and soil movement per mm of runoff (g/L), Greenmount and Greenwood'; cs['A1'].font = H1
cs['A2'] = 'Model concentration = conc(cover) x LS x K x 10. Curves are formulas from the Parameters sheet.'; cs['A2'].font = NOTE
hdr(cs, 4, ['Cover (%)', 'Greenmount new', 'Greenmount original', 'Greenwood new', 'Greenwood original'])
b = ref('Sediment cover coefficient b (per % cover)', 'Greenmount')
for i, cv in enumerate(range(0, 81, 5)):
    r = 5 + i; cs.cell(r, 1, cv)
    perf = f'MAX(0,IF(A{r}<50,16.52-0.46*A{r}+0.0031*A{r}^2,2.54-0.0254*A{r}))'
    for j, s in enumerate(['Greenmount', 'Greenwood']):
        LSr = ref('LS (from soil file slope and length)', s); Kn = ref('K', s); Ko = ref('K', s, False)
        cs.cell(r, 2 + 2 * j, f'=16.52*EXP(-{b}*A{r})*{LSr}*{Kn}*10').number_format = '0.00'
        cs.cell(r, 3 + 2 * j, f'={perf}*{LSr}*{Ko}*10').number_format = '0.00'
cend = 5 + 16
hdr(cs, 24, ['Site', 'Treatment', 'Runoff-weighted cover (%)', 'Observed (g/L)', 'New model (g/L)', 'Observed / new'])
pts = [p for p in D['pts'] if p['kind'] == 'sm']
for i, p in enumerate(pts):
    r = 25 + i
    cs.cell(r, 1, p['site']); cs.cell(r, 2, p['name'])
    cs.cell(r, 3, round(p['cover'], 1)).number_format = '0.0'; cs.cell(r, 4, round(p['conc'], 2)).number_format = '0.00'
    s = p['site']
    cs.cell(r, 5, f"=16.52*EXP(-{b}*C{r})*{ref('LS (from soil file slope and length)', s)}*{ref('K', s)}*10").number_format = '0.00'
    cs.cell(r, 6, f'=D{r}/E{r}').number_format = '0.00'
cs.cell(25 + len(pts), 1, 'Observed = treatment total soil movement / total runoff x 100; cover from the revised vege file, weighted by observed runoff.').font = NOTE
ch = ScatterChart(); ch.title = 'Soil movement per mm runoff vs cover'; ch.style = 13
ch.x_axis.title = 'Cover (%)'; ch.y_axis.title = 'g/L'; ch.y_axis.scaling.logBase = 10
xs = Reference(cs, min_col=1, min_row=5, max_row=cend - 1)
for col, name in [(2, 'Greenmount new'), (3, 'Greenmount original'), (4, 'Greenwood new'), (5, 'Greenwood original')]:
    se = Series(Reference(cs, min_col=col, min_row=5, max_row=cend - 1), xs, title=name); se.marker.symbol = 'none'; ch.series.append(se)
for site in ['Greenmount', 'Greenwood']:
    rows_ = [25 + i for i, p in enumerate(pts) if p['site'] == site]
    se = Series(Reference(cs, min_col=4, min_row=rows_[0], max_row=rows_[-1]), Reference(cs, min_col=3, min_row=rows_[0], max_row=rows_[-1]), title=f'{site} observed')
    se.marker.symbol = 'circle'; se.graphicalProperties.line.noFill = True; ch.series.append(se)
ch.x_axis.delete = False; ch.y_axis.delete = False; ch.height = 9; ch.width = 16
cs.add_chart(ch, 'H4')
for j, w in enumerate([14, 16, 18, 16, 18, 14]): cs.column_dimensions[L(1 + j)].width = w

# ---------------- Cover vs TSS
ct = wb.create_sheet('Cover vs TSS')
ct['A1'] = 'Figure 3. Cover and suspended sediment (flow-weighted TSS, g/L), three sites'; ct['A1'].font = H1
ct['A2'] = 'New model only: TSS = bare-soil concentration x EXP(-b x cover). Curves are formulas from the Parameters sheet.'; ct['A2'].font = NOTE
hdr(ct, 4, ['Cover (%)'] + [f'{s} new' for s in SITES])
bt = ref('Suspended cover coefficient (per % cover)', 'Greenmount')
for i, cv in enumerate(range(0, 81, 5)):
    r = 5 + i; ct.cell(r, 1, cv)
    for j, s in enumerate(SITES):
        ct.cell(r, 2 + j, f"={ref('Suspended conc. at bare soil (g/L)', s)}*EXP(-{bt}*A{r})").number_format = '0.00'
hdr(ct, 24, ['Site', 'Treatment', 'Runoff-weighted cover (%)', 'Observed (g/L)', 'New model (g/L)', 'Observed / new'])
tp = [p for p in D['pts'] if p['kind'] == 'ss']
for i, p in enumerate(tp):
    r = 25 + i
    ct.cell(r, 1, p['site']); ct.cell(r, 2, p['name'])
    ct.cell(r, 3, round(p['cover'], 1)).number_format = '0.0'; ct.cell(r, 4, round(p['conc'], 2)).number_format = '0.00'
    ct.cell(r, 5, f"={ref('Suspended conc. at bare soil (g/L)', p['site'])}*EXP(-{bt}*C{r})").number_format = '0.00'
    ct.cell(r, 6, f'=D{r}/E{r}').number_format = '0.00'
ct.cell(25 + len(tp), 1, 'Observed = treatment total suspended sediment / total runoff x 100. The original model has no suspended sediment.').font = NOTE
ch = ScatterChart(); ch.title = 'Flow-weighted TSS vs cover'; ch.style = 13
ch.x_axis.title = 'Cover (%)'; ch.y_axis.title = 'g/L'; ch.y_axis.scaling.logBase = 10
xs = Reference(ct, min_col=1, min_row=5, max_row=21)
for j, s in enumerate(SITES):
    se = Series(Reference(ct, min_col=2 + j, min_row=5, max_row=21), xs, title=f'{s} new'); se.marker.symbol = 'none'; ch.series.append(se)
for s in SITES:
    rows_ = [25 + i for i, p in enumerate(tp) if p['site'] == s]
    se = Series(Reference(ct, min_col=4, min_row=rows_[0], max_row=rows_[-1]), Reference(ct, min_col=3, min_row=rows_[0], max_row=rows_[-1]), title=f'{s} observed')
    se.marker.symbol = 'circle'; se.graphicalProperties.line.noFill = True; ch.series.append(se)
ch.x_axis.delete = False; ch.y_axis.delete = False; ch.height = 9; ch.width = 16
ct.add_chart(ch, 'H4')
for j, w in enumerate([14, 16, 18, 16, 18, 14]): ct.column_dimensions[L(1 + j)].width = w

# ---------------- Cumulative series (long format)
cu = wb.create_sheet('Cumulative')
cu['A1'] = 'Figure 1 data. Cumulative observed and predicted, month-end values'; cu['A1'].font = H1
hdr(cu, 3, ['Site', 'Treatment', 'Variable', 'Month', 'Observed', 'Original', 'New', 'Unit'])
r = 4
for c in D['cum']:
    for v, lab, unit in [('ro', 'Runoff', 'mm'), ('sm', 'Soil movement', 't/ha'), ('ss', 'Suspended sediment', 't/ha')]:
        s = c.get(v)
        if not s: continue
        for i, d in enumerate(s['d']):
            cu.cell(r, 1, c['site']); cu.cell(r, 2, c['name']); cu.cell(r, 3, lab); cu.cell(r, 4, d)
            cu.cell(r, 5, s['o'][i]); cu.cell(r, 6, s['old'][i] if 'old' in s else None); cu.cell(r, 7, s['new'][i]); cu.cell(r, 8, unit)
            r += 1
for j, w in enumerate([13, 13, 18, 12, 12, 12, 12, 7]): cu.column_dimensions[L(1 + j)].width = w
cu.freeze_panes = 'A4'; cu.auto_filter.ref = f'A3:H{r - 1}'

wb.save('/home/claude/joint/watbal2026_original_vs_new.xlsx')
print('rows cumulative', r - 4)
