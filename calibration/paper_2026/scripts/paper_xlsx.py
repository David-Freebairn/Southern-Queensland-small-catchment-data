import pickle, pandas as pd, numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

R = pickle.load(open('/home/claude/paper/runs.pkl', 'rb'))
S = pd.read_csv('/home/claude/paper/stats_by_catchment.csv')
P = pd.read_csv('/home/claude/paper/stats_pooled.csv')
F = Font(name='Arial', size=10); B = Font(name='Arial', size=10, bold=True); T = Font(name='Arial', size=12, bold=True)
I = Font(name='Arial', size=9, italic=True, color='555555'); H = PatternFill('solid', fgColor='DDE5EE')
thin = Border(bottom=Side(style='thin', color='999999'))
wb = Workbook()

def head(ws, r, cols, row2=None):
    for j, h in enumerate(cols, 1):
        c = ws.cell(r, j, h); c.font = B; c.fill = H; c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    if row2:
        for j, h in enumerate(row2, 1):
            c = ws.cell(r + 1, j, h); c.font = B; c.fill = H; c.alignment = Alignment(horizontal='center'); c.border = thin

def widths(ws, w):
    for j, x in enumerate(w, 1): ws.column_dimensions[get_column_letter(j)].width = x

# ── Table 1: model configurations ─────────────────────────────────────────
ws = wb.active; ws.title = 'T1 Configuration'
ws['A1'] = 'Table 1. Original and revised model configurations'; ws['A1'].font = T
rows = [('Runoff AMC', 'Capped (PERFECT)', 'Uncapped (HowLeaky); CN entered at average wetness (0.25), converted internally'),
        ('Zero till', 'Same soil as other treatments', 'Separate soil file, CN higher'),
        ('Soil evaporation', 'Stage 1 (U) and stage 2 (Cona) from soil file', 'U = 0; Cona fitted per site'),
        ('Crop water use', 'No-stress PAW fraction 0.2', 'No-stress PAW fraction 0.75; no kl'),
        ('Soil movement', 'PERFECT concentration-cover curve x LS x K x Q', 'conc = 16.52 exp(-0.057 cover%) x LS x K x Q'),
        ('Suspended sediment', 'Soil movement x delivery ratio in soil file', 'A exp(-0.0388 cover%) x Q / 100 (Q > 1 mm), A per site'),
        ('Cover, roots, crop dates', 'Revised vege files (same in both)', 'Revised vege files (same in both)'),
        ('Run', 'App engine, from climate start, 50 % PAWC, no resets', 'Same')]
head(ws, 3, ['Component', 'Original', 'Revised'])
for i, r in enumerate(rows, 4):
    for j, v in enumerate(r, 1):
        c = ws.cell(i, j, v); c.font = F; c.alignment = Alignment(wrap_text=True, vertical='top')
r0 = 4 + len(rows) + 1
ws.cell(r0, 1, 'Parameters by site').font = B
head(ws, r0 + 1, ['Site', 'CN (orig.)', 'CN tilled / zero till (rev., entered)', 'CN internal tilled / zero till (rev.)', 'CN cover reduction (orig. / rev.)',
                  'Cona (orig. / rev.)', 'U (orig. / rev.)', 'K (orig. / rev.)', 'Delivery ratio (orig.)', 'Suspended A, g/L (rev.)'])
for i, s in enumerate(['Greenmount', 'Greenwood', 'Wallumbilla'], r0 + 2):
    t = [k for k in R if k[0] == s]; d0 = R[t[0]]; o, n = d0['old_soil'], d0['new_soil']
    zt = [R[k]['new_soil'] for k in t if k[1] == 'Zero till']
    vals = [s, o['cn'], f"{n['cn_input']:.1f}" + (f" / {zt[0]['cn_input']:.1f}" if zt else ''),
            f"{n['cn_internal']:.1f}" + (f" / {zt[0]['cn_internal']:.1f}" if zt else ''), f"{o['cn_red']:g} / 14.8",
            f"{o['cona']:g} / {n['cona']:.2f}", f"{o['u']:g} / {n['u']:g}", f"{o['K']:g} / {n['K']:.3f}", o['sdr'], round(d0['A_new'], 2)]
    for j, v in enumerate(vals, 1): ws.cell(i, j, v).font = F
ws.cell(r0 + 6, 1, 'Wallumbilla K applies to the soil movement equation but soil movement was not measured there. Greenwood original U = 0 runs with the Nov 2026 evaporation reset fix.').font = I
widths(ws, [24, 34, 52, 18, 18, 14, 10, 14, 12, 14])

# ── Table 2: statistics by catchment ─────────────────────────────────────
ws = wb.create_sheet('T2 By catchment')
ws['A1'] = 'Table 2. Fit statistics by catchment, original (O) and revised (R)'; ws['A1'].font = T
groups = [('Runoff P:O', 'runoff_PO', '0.00'), ('Runoff NSE (3-day)', 'runoff_NSE_3day', '0.00'), ('Runoff R² (monthly)', 'runoff_R2_monthly', '0.00'),
          ('Soil movement P:O', 'sm_PO', '0.00'), ('Soil movement NSE (3-day)', 'sm_NSE_3day', '0.00'),
          ('Suspended P:O', 'ss_PO', '0.00'), ('Suspended NSE (3-day)', 'ss_NSE_3day', '0.00'),
          ('PAW RMSE (mm)', 'paw_RMSE_mm', '0'), ('PAW bias (mm)', 'paw_bias_mm', '0'), ('PAW R²', 'paw_R2', '0.00')]
top = ['Site', 'Treatment', 'Runoff obs (mm)', 'Soil movement obs (t/ha)', 'Suspended obs (t/ha)', 'PAW n']
row1, row2 = list(top), [''] * len(top)
for g, _, _ in groups: row1 += [g, '']; row2 += ['O', 'R']
head(ws, 3, row1, row2)
for j in range(len(top) + 1, len(row1) + 1, 2): ws.merge_cells(start_row=3, start_column=j, end_row=3, end_column=j + 1)
r = 5
for (site, trt), g in S.groupby(['site', 'treatment'], sort=False):
    o = g[g.model == 'Original'].iloc[0]; n = g[g.model == 'Revised'].iloc[0]
    base = [site, trt, round(o.runoff_obs_mm), None if pd.isna(o.get('sm_obs_t_ha')) else round(o.sm_obs_t_ha, 1), round(o.ss_obs_t_ha, 1), int(o.paw_n)]
    for j, v in enumerate(base, 1): ws.cell(r, j, v).font = F
    col = len(base) + 1
    for _, key, fmt in groups:
        for rr in (o, n):
            v = rr.get(key); c = ws.cell(r, col, None if pd.isna(v) else float(v)); c.font = F; c.number_format = fmt; col += 1
    r += 1
ws.cell(r + 1, 1, 'P:O = predicted / observed total over measured days. NSE on 3-day centred sums (timing errors of ±1 day). R² on monthly totals. PAW 0-150 cm at sampling dates.').font = I
ws.freeze_panes = 'C5'
widths(ws, [12, 13, 9, 10, 10, 6] + [6.5] * 20)

# ── Table 3: pooled ───────────────────────────────────────────────────────
ws = wb.create_sheet('T3 By site')
ws['A1'] = 'Table 3. Fit statistics by site and overall (catchments pooled)'; ws['A1'].font = T
cols = [('Runoff P:O', 'runoff_PO', '0.00'), ('Runoff NSE 3-day', 'runoff_NSE_3day', '0.00'), ('Runoff R² monthly', 'runoff_R2_monthly', '0.00'),
        ('Soil mov. P:O', 'sm_PO', '0.00'), ('Soil mov. NSE 3-day', 'sm_NSE_3day', '0.00'), ('Soil mov. R² monthly', 'sm_R2_monthly', '0.00'),
        ('Suspended P:O', 'ss_PO', '0.00'), ('Suspended NSE 3-day', 'ss_NSE_3day', '0.00'), ('Suspended R² monthly', 'ss_R2_monthly', '0.00'),
        ('PAW RMSE (mm)', 'paw_RMSE_mm', '0'), ('PAW bias (mm)', 'paw_bias_mm', '0'), ('PAW R²', 'paw_R2', '0.00'), ('PAW n', 'paw_n', '0')]
head(ws, 3, ['Site', 'Model'] + [c[0] for c in cols])
for i, rr in enumerate(P.itertuples(), 4):
    ws.cell(i, 1, rr.site).font = F; ws.cell(i, 2, rr.model).font = F
    for j, (_, key, fmt) in enumerate(cols, 3):
        v = getattr(rr, key); c = ws.cell(i, j, None if pd.isna(v) else float(v)); c.font = F; c.number_format = fmt
widths(ws, [12, 10] + [10] * len(cols))

# ── Figure list ───────────────────────────────────────────────────────────
ws = wb.create_sheet('Figures')
ws['A1'] = 'Figures (PNG 300 dpi and PDF)'; ws['A1'].font = T
figs = [('Fig1_cumulative_runoff', 'Cumulative runoff, observed vs original vs revised, 10 catchments, measured periods; P:O in each panel'),
        ('Fig2_cumulative_soil_movement', 'Cumulative soil movement, Greenmount and Greenwood (8 catchments)'),
        ('Fig3_cumulative_suspended_sediment', 'Cumulative suspended sediment, 10 catchments'),
        ('Fig4_monthly_obs_vs_pred', 'Observed vs predicted monthly runoff, soil movement and suspended sediment, original and revised, same months'),
        ('Fig5_PAW_obs_vs_pred', 'Observed vs predicted PAW (0-150 cm), original and revised')]
for i, (a, b) in enumerate(figs, 3): ws.cell(i, 1, a).font = B; ws.cell(i, 2, b).font = F
widths(ws, [36, 110])
wb.save('/home/claude/paper/Watbal2026_paper_tables.xlsx')
print('ok')
