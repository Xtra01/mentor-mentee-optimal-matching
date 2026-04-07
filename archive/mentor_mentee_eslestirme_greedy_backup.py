import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Load data ──────────────────────────────────────────────────────────────────
import os, glob
_script_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_script_dir, '..', 'data')
_xlsx_files = glob.glob(os.path.join(_data_dir, 'Mentor*2026*.xlsx'))
if not _xlsx_files:
    raise FileNotFoundError(f"No matching Excel file found in {_data_dir}")
xf = pd.read_excel(_xlsx_files[0], sheet_name=None)

mentee_raw = xf['Mentee']
mcols = [c for c in mentee_raw.columns if c is not None and str(c) != 'None']
mentee = mentee_raw[mcols].copy()
mentee = mentee[mentee.iloc[:, 0].notna()].reset_index(drop=True)

mentor_raw = xf['Mentor']
trcols = [c for c in mentor_raw.columns if c is not None]
mentor = mentor_raw[trcols].copy()
mentor = mentor[mentor.iloc[:, 0].notna()].reset_index(drop=True)

history = xf['Son 3 yıl eşleşme'].copy()
history.columns = ['ID', 'MenteeName', 'Mentor', 'Year']

# ── Column shortcuts ───────────────────────────────────────────────────────────
# Mentee columns (by index)
M_NAME      = 1   # name
M_ID        = 2   # student id
M_CITY      = 6   # city
M_MAJOR     = 7   # major
M_CAREER    = 10  # career goals
M_PREF_TEXT = 12  # preferred mentor description
M_SUPPORT   = 14  # support topics wanted
M_SCR_DEPT  = 15  # importance: department (1-5)
M_SCR_SEC   = 16  # importance: sector
M_SCR_ORG   = 17  # importance: organization
M_SCR_CITY  = 19  # importance: city
M_SCR_INT   = 21  # importance: interests
M_FLEX      = 22  # flexible if not ideal
M_OLD_MENTOR= 23  # old mentor name
M_MATCHED   = 24  # already matched this round

# Mentor columns (by index)
T_NAME      = 1   # name
T_CITY      = 6   # standardized city
T_HOBBIES   = 7   # hobbies
T_GRAD_YEAR = 8   # graduation year
T_MAJOR     = 9   # major at KU
T_SECTOR    = 12  # current sector
T_POSITION  = 13  # position
T_EXPERTISE = 15  # expertise areas
T_SUPPORT   = 21  # support areas
T_CAPACITY  = 22  # max mentees

# ── Helper functions ───────────────────────────────────────────────────────────

def clean(s):
    return str(s).lower().strip() if pd.notna(s) else ''

def parse_score(val):
    """Convert '3 - Orta düzeyde önemli' -> 3"""
    s = str(val)
    if s[0].isdigit():
        return int(s[0])
    return 3  # default

def parse_capacity(val):
    try:
        return int(val)
    except:
        s = str(val).lower()
        if 'tüm' in s or 'limit' in s or 'ne kadar' in s or 'sayı' in s:
            return 5
        return 2  # default

def text_overlap(a, b):
    """Simple token overlap score 0-1"""
    if not a or not b:
        return 0.0
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))

# ── Parse mentor capacity & build availability ─────────────────────────────────
mentor['_capacity'] = mentor.iloc[:, T_CAPACITY].apply(parse_capacity)

# Existing matches in this round (already assigned in spreadsheet)
assigned_mentor_names = set()
for col_idx in [24, 26, 28]:  # Mentee Adı1, Mentee Adı2, Mentee Adı3
    assigned_mentor_names.update(
        mentor.iloc[:, col_idx].dropna().unique()
    )

def mentor_current_load(mentor_name):
    """Count how many mentees already assigned to this mentor in the sheet."""
    count = 0
    for col_idx in [25, 27, 29]:  # Mentee ID1, ID2, ID3
        vals = mentor[mentor.iloc[:, T_NAME] == mentor_name].iloc[:, col_idx]
        count += vals.notna().sum()
    return count

# Build mentor remaining capacity dict
mentor_remaining = {}
for _, row in mentor.iterrows():
    mname = row.iloc[T_NAME]
    cap = parse_capacity(row.iloc[T_CAPACITY])
    # Count already filled slots
    filled = sum(1 for ci in [24, 26, 28] if pd.notna(row.iloc[ci]))
    mentor_remaining[mname] = max(0, cap - filled)

# ── Build historical pairs to avoid repeats ───────────────────────────────────
historical_pairs = set()
for _, row in history.iterrows():
    if pd.notna(row['MenteeName']) and pd.notna(row['Mentor']):
        historical_pairs.add((clean(row['MenteeName']), clean(row['Mentor'])))

# ── Identify mentees that need matching ───────────────────────────────────────
need_match = mentee[mentee.iloc[:, M_MATCHED].isna()].reset_index(drop=True)
print(f"Mentees needing match: {len(need_match)}")
print(f"Available mentors: {len(mentor)}")
print(f"Total remaining mentor capacity: {sum(mentor_remaining.values())}")

# ── Scoring function ───────────────────────────────────────────────────────────
def score_pair(me_row, mr_row):
    """
    Returns a score 0-100 for a mentee-mentor pair.
    Higher = better match.
    """
    score = 0.0

    # Hard block: old mentor or historical repeat
    me_name = clean(me_row.iloc[M_NAME])
    mr_name = clean(mr_row.iloc[T_NAME])
    old_mentor = clean(me_row.iloc[M_OLD_MENTOR])
    
    if old_mentor and old_mentor == mr_name:
        return -999
    if (me_name, mr_name) in historical_pairs:
        return -999

    # Get mentee importance weights (1-5)
    w_dept  = parse_score(me_row.iloc[M_SCR_DEPT])
    w_sec   = parse_score(me_row.iloc[M_SCR_SEC])
    w_city  = parse_score(me_row.iloc[M_SCR_CITY])
    w_int   = parse_score(me_row.iloc[M_SCR_INT])

    total_w = w_dept + w_sec + w_city + w_int
    if total_w == 0:
        total_w = 1

    # 1. Sector match (mentee career goal vs mentor sector+expertise)
    me_career = clean(me_row.iloc[M_CAREER])
    mr_sector = clean(mr_row.iloc[T_SECTOR])
    mr_expertise = clean(mr_row.iloc[T_EXPERTISE])
    sec_score = max(
        text_overlap(me_career, mr_sector),
        text_overlap(me_career, mr_expertise),
        text_overlap(clean(me_row.iloc[M_PREF_TEXT]), mr_sector)
    )
    score += (w_sec / total_w) * 35 * sec_score

    # 2. Department / academic match
    me_major = clean(me_row.iloc[M_MAJOR])
    mr_major = clean(mr_row.iloc[T_MAJOR])
    dept_score = text_overlap(me_major, mr_major)
    # Also check mentee preference text
    dept_score = max(dept_score, text_overlap(clean(me_row.iloc[M_PREF_TEXT]), mr_major))
    score += (w_dept / total_w) * 30 * dept_score

    # 3. City match
    me_city = clean(me_row.iloc[M_CITY])
    mr_city = clean(mr_row.iloc[T_CITY])
    city_score = 0.0
    if me_city and mr_city:
        if me_city == mr_city:
            city_score = 1.0
        elif me_city.split(',')[0].strip() == mr_city.split(',')[0].strip():
            city_score = 0.8
        elif 'istanbul' in me_city and 'istanbul' in mr_city:
            city_score = 1.0
    score += (w_city / total_w) * 15 * city_score

    # 4. Interests match
    me_interests = clean(me_row.iloc[M_PREF_TEXT]) + ' ' + clean(me_row.iloc[M_SUPPORT])
    mr_interests = clean(mr_row.iloc[T_HOBBIES]) + ' ' + clean(mr_row.iloc[T_SUPPORT])
    int_score = text_overlap(me_interests, mr_interests)
    score += (w_int / total_w) * 10 * int_score

    # 5. Support topic match
    sup_score = text_overlap(clean(me_row.iloc[M_SUPPORT]), clean(mr_row.iloc[T_SUPPORT]))
    score += 10 * sup_score

    return round(score, 2)

# ── Greedy matching with capacity constraints ──────────────────────────────────
print("Computing scores...")

results = []
remaining = dict(mentor_remaining)  # copy

# Sort mentees: those with stricter preferences first (higher avg weight = more picky)
def pickiness(row):
    weights = [parse_score(row.iloc[c]) for c in [M_SCR_DEPT, M_SCR_SEC, M_SCR_CITY, M_SCR_INT]]
    return sum(weights)

need_match = need_match.copy()
need_match['_pickiness'] = need_match.apply(pickiness, axis=1)
need_match = need_match.sort_values('_pickiness', ascending=False).reset_index(drop=True)

matched_count = 0
unmatched = []

for _, me_row in need_match.iterrows():
    me_name = me_row.iloc[M_NAME]
    me_id   = me_row.iloc[M_ID]
    
    # Score all mentors
    candidates = []
    for _, mr_row in mentor.iterrows():
        mr_name = mr_row.iloc[T_NAME]
        if remaining.get(mr_name, 0) <= 0:
            continue
        s = score_pair(me_row, mr_row)
        if s > -900:
            candidates.append((s, mr_name, mr_row))
    
    if not candidates:
        unmatched.append({'Mentee_Adı': me_name, 'Mentee_ID': me_id, 'Sebep': 'Tüm mentorler dolu veya bloke'})
        continue
    
    # Pick best
    candidates.sort(reverse=True)
    best_score, best_mentor, best_mr_row = candidates[0]
    
    # Collect top-3 alternatives for transparency
    alts = [f"{c[1]} ({c[0]:.1f})" for c in candidates[1:4]]
    
    results.append({
        'Mentee_Adı': me_name,
        'Mentee_ID': int(me_id) if pd.notna(me_id) else '',
        'Mentee_Bölüm': me_row.iloc[M_MAJOR],
        'Mentee_Kariyer_Hedefi': str(me_row.iloc[M_CAREER])[:120],
        'Mentee_Şehir': me_row.iloc[M_CITY],
        'Mentor_Adı': best_mentor,
        'Mentor_Sektör': best_mr_row.iloc[T_SECTOR],
        'Mentor_Pozisyon': best_mr_row.iloc[T_POSITION],
        'Mentor_Şehir': best_mr_row.iloc[T_CITY],
        'Eşleşme_Puanı': best_score,
        'Alternatif_Mentorler': ' | '.join(alts),
        'Eski_Mentor': me_row.iloc[M_OLD_MENTOR],
    })
    
    remaining[best_mentor] = remaining.get(best_mentor, 0) - 1
    matched_count += 1

print(f"Matched: {matched_count}")
print(f"Unmatched: {len(unmatched)}")

# Also carry over already-matched mentees
already_df_rows = []
already = mentee[mentee.iloc[:, M_MATCHED].notna()].reset_index(drop=True)
for _, row in already.iterrows():
    already_df_rows.append({
        'Mentee_Adı': row.iloc[M_NAME],
        'Mentee_ID': row.iloc[M_ID],
        'Mentee_Bölüm': row.iloc[M_MAJOR],
        'Mentee_Kariyer_Hedefi': str(row.iloc[M_CAREER])[:120],
        'Mentee_Şehir': row.iloc[M_CITY],
        'Mentor_Adı': row.iloc[M_MATCHED],
        'Mentor_Sektör': '',
        'Mentor_Pozisyon': '',
        'Mentor_Şehir': '',
        'Eşleşme_Puanı': 'Mevcut',
        'Alternatif_Mentorler': '',
        'Eski_Mentor': row.iloc[M_OLD_MENTOR],
    })

results_df = pd.DataFrame(results)
already_df = pd.DataFrame(already_df_rows)
unmatched_df = pd.DataFrame(unmatched) if unmatched else pd.DataFrame(columns=['Mentee_Adı','Mentee_ID','Sebep'])

# Mentor load summary
mentor_load = []
for _, mr_row in mentor.iterrows():
    mname = mr_row.iloc[T_NAME]
    cap = parse_capacity(mr_row.iloc[T_CAPACITY])
    filled_existing = sum(1 for ci in [24,26,28] if pd.notna(mr_row.iloc[ci]))
    newly_assigned = cap - filled_existing - remaining.get(mname, 0)
    total_assigned = filled_existing + max(0, newly_assigned)
    mentor_load.append({
        'Mentor_Adı': mname,
        'Sektör': mr_row.iloc[T_SECTOR],
        'Kapasite': cap,
        'Mevcut_Eşleşme': filled_existing,
        'Yeni_Eşleşme': max(0, newly_assigned),
        'Toplam_Eşleşme': total_assigned,
        'Kalan_Kapasite': remaining.get(mname, cap),
    })
mentor_load_df = pd.DataFrame(mentor_load)

# ── Export to Excel ────────────────────────────────────────────────────────────
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()

# Color palette
BLUE_H   = 'FF1E3A5F'  # header bg dark blue
WHITE_H  = 'FFFFFFFF'
GREEN_BG = 'FFE8F5E9'
AMBER_BG = 'FFFFF8E1'
RED_BG   = 'FFFFEBEE'
GRAY_BG  = 'FFF5F5F5'
GREEN_H  = 'FF2E7D32'
AMBER_H  = 'FFF57F17'

thin = Border(
    left=Side(style='thin', color='FFD0D0D0'),
    right=Side(style='thin', color='FFD0D0D0'),
    top=Side(style='thin', color='FFD0D0D0'),
    bottom=Side(style='thin', color='FFD0D0D0')
)

def style_header_row(ws, row_num, bg='FF1E3A5F', fg='FFFFFFFF'):
    for cell in ws[row_num]:
        if cell.value is None:
            continue
        cell.font = Font(bold=True, color=fg, name='Arial', size=10)
        cell.fill = PatternFill('solid', start_color=bg)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin

def style_data_row(ws, row_num, bg=None):
    for cell in ws[row_num]:
        cell.font = Font(name='Arial', size=9)
        cell.alignment = Alignment(vertical='center', wrap_text=True)
        cell.border = thin
        if bg:
            cell.fill = PatternFill('solid', start_color=bg)

def set_col_widths(ws, widths):
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

# ── Sheet 1: Yeni Eşleşmeler ──────────────────────────────────────────────────
ws1 = wb.active
ws1.title = '🔗 Yeni Eşleşmeler'

ws1.row_dimensions[1].height = 18
ws1.row_dimensions[2].height = 35

ws1['A1'] = f'Mentor-Mentee Eşleştirme Sonuçları 2026  |  Yeni Eşleşmeler: {len(results_df)}  |  Eşleştirilemeyen: {len(unmatched_df)}'
ws1['A1'].font = Font(bold=True, name='Arial', size=12, color='FF1E3A5F')
ws1.merge_cells('A1:L1')

headers = ['Mentee Adı', 'Mentee ID', 'Bölüm', 'Kariyer Hedefi', 'Mentee Şehir',
           'Mentor Adı', 'Mentor Sektör', 'Mentor Pozisyon', 'Mentor Şehir',
           'Eşleşme Puanı', 'Alternatif Mentorler', 'Eski Mentor']
ws1.append(headers)
style_header_row(ws1, 2)

for i, row in results_df.iterrows():
    ws1.append(list(row))
    bg = GREEN_BG if (i % 2 == 0) else 'FFFFFFFF'
    style_data_row(ws1, i + 3, bg)
    # Color score cell
    score_cell = ws1.cell(row=i+3, column=10)
    try:
        s = float(score_cell.value)
        if s >= 15:
            score_cell.fill = PatternFill('solid', start_color='FFB9F6CA')
            score_cell.font = Font(bold=True, name='Arial', size=9, color='FF1B5E20')
        elif s >= 8:
            score_cell.fill = PatternFill('solid', start_color='FFFFF9C4')
            score_cell.font = Font(bold=True, name='Arial', size=9, color='FFF57F17')
        else:
            score_cell.fill = PatternFill('solid', start_color='FFFFCDD2')
            score_cell.font = Font(bold=True, name='Arial', size=9, color='FFB71C1C')
    except:
        pass

ws1.freeze_panes = 'A3'
ws1.auto_filter.ref = f'A2:L{len(results_df)+2}'
set_col_widths(ws1, {
    'A': 22, 'B': 10, 'C': 18, 'D': 35, 'E': 18,
    'F': 22, 'G': 22, 'H': 22, 'I': 18, 'J': 14, 'K': 40, 'L': 20
})

# ── Sheet 2: Mevcut Eşleşmeler ─────────────────────────────────────────────────
ws2 = wb.create_sheet('✅ Mevcut Eşleşmeler')
ws2['A1'] = f'Mevcut Eşleşmeler (Spreadsheethe Girilmiş)  |  Toplam: {len(already_df)}'
ws2['A1'].font = Font(bold=True, name='Arial', size=12, color=GREEN_H)
ws2.merge_cells('A1:L1')
ws2.row_dimensions[1].height = 18
ws2.row_dimensions[2].height = 35

ws2.append(headers)
style_header_row(ws2, 2, bg='FF2E7D32')

for i, row in already_df.iterrows():
    ws2.append(list(row))
    bg = GREEN_BG if (i % 2 == 0) else 'FFFFFFFF'
    style_data_row(ws2, i + 3, bg)

ws2.freeze_panes = 'A3'
set_col_widths(ws2, {
    'A': 22, 'B': 10, 'C': 18, 'D': 35, 'E': 18,
    'F': 22, 'G': 22, 'H': 22, 'I': 18, 'J': 14, 'K': 40, 'L': 20
})

# ── Sheet 3: Eşleştirilemeyen ─────────────────────────────────────────────────
ws3 = wb.create_sheet('⚠️ Eşleştirilemeyen')
ws3['A1'] = f'Eşleştirilemeyen Menteeler  |  Toplam: {len(unmatched_df)}'
ws3['A1'].font = Font(bold=True, name='Arial', size=12, color='FFB71C1C')
ws3.merge_cells('A1:C1')
ws3.row_dimensions[1].height = 18

if not unmatched_df.empty:
    ws3.append(['Mentee Adı', 'Mentee ID', 'Sebep'])
    style_header_row(ws3, 2, bg='FFB71C1C')
    for i, row in unmatched_df.iterrows():
        ws3.append(list(row))
        style_data_row(ws3, i + 3, RED_BG)
else:
    ws3['A2'] = '✅ Tüm menteeler eşleştirildi!'
    ws3['A2'].font = Font(bold=True, name='Arial', size=11, color=GREEN_H)

set_col_widths(ws3, {'A': 25, 'B': 12, 'C': 50})

# ── Sheet 4: Mentor Yük Özeti ──────────────────────────────────────────────────
ws4 = wb.create_sheet('📊 Mentor Yük Özeti')
ws4['A1'] = 'Mentor Kapasite ve Yük Özeti'
ws4['A1'].font = Font(bold=True, name='Arial', size=12, color='FF1E3A5F')
ws4.merge_cells('A1:G1')
ws4.row_dimensions[1].height = 18
ws4.row_dimensions[2].height = 35

ml_headers = ['Mentor Adı', 'Sektör', 'Kapasite', 'Mevcut Eşleşme', 'Yeni Eşleşme', 'Toplam Eşleşme', 'Kalan Kapasite']
ws4.append(ml_headers)
style_header_row(ws4, 2)

mentor_load_df_sorted = mentor_load_df.sort_values('Toplam_Eşleşme', ascending=False)
for i, row in mentor_load_df_sorted.iterrows():
    ws4.append(list(row))
    bg = GREEN_BG if row['Kalan_Kapasite'] > 0 else AMBER_BG
    style_data_row(ws4, mentor_load_df_sorted.index.get_loc(i) + 3, bg)

ws4.freeze_panes = 'A3'
ws4.auto_filter.ref = f'A2:G{len(mentor_load_df)+2}'
set_col_widths(ws4, {'A': 25, 'B': 28, 'C': 10, 'D': 16, 'E': 14, 'F': 16, 'G': 16})

# ── Sheet 5: Özet İstatistik ──────────────────────────────────────────────────
ws5 = wb.create_sheet('📈 Özet')
ws5.column_dimensions['A'].width = 35
ws5.column_dimensions['B'].width = 18

stats = [
    ('EŞLEŞTIRME ÖZETI 2026', ''),
    ('', ''),
    ('Toplam Başvuran Mentee', len(mentee)),
    ('Önceden Eşleşmiş (Spreadsheet)', len(already_df)),
    ('Bu Turda Eşleştirilen', len(results_df)),
    ('Eşleştirilemeyen', len(unmatched_df)),
    ('', ''),
    ('Toplam Mentor', len(mentor)),
    ('Toplam Mentor Kapasitesi', sum(parse_capacity(v) for v in mentor.iloc[:,T_CAPACITY])),
    ('Doldurulan Kapasite', len(results_df) + len(already_df)),
    ('', ''),
    ('Puan Dağılımı', ''),
    ('Yüksek Puan (≥15)', len(results_df[results_df['Eşleşme_Puanı'] >= 15]) if not results_df.empty else 0),
    ('Orta Puan (8-14)', len(results_df[(results_df['Eşleşme_Puanı'] >= 8) & (results_df['Eşleşme_Puanı'] < 15)]) if not results_df.empty else 0),
    ('Düşük Puan (<8)', len(results_df[results_df['Eşleşme_Puanı'] < 8]) if not results_df.empty else 0),
    ('Ortalama Puan', round(results_df['Eşleşme_Puanı'].mean(), 2) if not results_df.empty else 0),
]

for r, (label, value) in enumerate(stats, start=1):
    ws5.cell(row=r, column=1, value=label)
    ws5.cell(row=r, column=2, value=value)
    if label and not label.startswith('  ') and value == '':
        ws5.cell(row=r, column=1).font = Font(bold=True, name='Arial', size=11, color='FF1E3A5F')
        ws5.cell(row=r, column=1).fill = PatternFill('solid', start_color='FFE3F2FD')
    elif label:
        ws5.cell(row=r, column=1).font = Font(name='Arial', size=10)
        ws5.cell(row=r, column=2).font = Font(bold=True, name='Arial', size=10)

out = os.path.join(_data_dir, 'Mentor_Mentee_Eslestirme_2026.xlsx')
wb.save(out)
print(f"\n✅ Saved: {out}")
print(f"   Yeni eşleşme: {len(results_df)}")
print(f"   Mevcut:       {len(already_df)}")
print(f"   Eşleşmeyen:   {len(unmatched_df)}")
