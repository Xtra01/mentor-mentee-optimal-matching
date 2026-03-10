"""
══════════════════════════════════════════════════════════════════════════
  MENTOR-MENTEE OPTİMAL EŞLEŞTİRME 2026
  ────────────────────────────────────────
  Yöntem : Hungarian Algoritması (Kuhn-Munkres) — Global Optimum
  Benzerlik: TF-IDF Cosine Similarity + Exact/Containment Hybrid
  Garanti : Toplam eşleşme kalitesini MAKSİMİZE eder
  ────────────────────────────────────────
  Neden bu yöntem en iyisi?
  1. Hungarian algoritması, atama problemlerinde kanıtlanmış global
     optimum çözüm verir (Greedy sadece lokal optimum).
  2. TF-IDF, kelime frekansını ve nadir kelimelerin ayırt ediciliğini
     hesaba katar (basit token overlap'ten çok daha güçlü).
  3. Kişiselleştirilmiş ağırlıklar, her mentee'nin kendi öncelik
     sıralamasını yansıtır.
  4. Deterministik: aynı girdi → her zaman aynı çıktı.
══════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import os, glob, warnings, time
warnings.filterwarnings('ignore')

from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

# Maximum possible score = W_SECTOR + W_DEPT + W_CITY + W_INTEREST + W_SUPPORT = 100
W_SECTOR   = 35   # Career/sector alignment
W_DEPT     = 30   # Academic department match
W_CITY     = 15   # City proximity
W_INTEREST = 10   # Interest/hobby overlap
W_SUPPORT  = 10   # Support topic alignment

BLOCK_SCORE = -1e9

TURKISH_STOPWORDS = {
    've', 'ile', 'bir', 'bu', 'de', 'da', 'den', 'dan', 'için', 'gibi',
    'ya', 'veya', 'ama', 'hem', 'ne', 'her', 'daha', 'çok', 'en', 'olan',
    'olarak', 'alanında', 'alanı', 'üzerine', 'hakkında', 'olarak', 'ise',
    'vb', 'vs', 've/veya', 'yıl', 'yılı', 'bölümü', 'bölüm',
    'the', 'and', 'of', 'in', 'to', 'a', 'is', 'on', 'at', 'by', 'or',
}

# Mentee columns (by index)
M_NAME      = 1
M_ID        = 2
M_CITY      = 6
M_MAJOR     = 7
M_CAREER    = 10
M_PREF_TEXT = 12
M_SUPPORT   = 14
M_SCR_DEPT  = 15
M_SCR_SEC   = 16
M_SCR_CITY  = 19
M_SCR_INT   = 21
M_OLD_MENTOR= 23

# Mentor columns (by index)
T_NAME      = 1
T_CITY      = 6
T_HOBBIES   = 7
T_MAJOR     = 9
T_SECTOR    = 12
T_POSITION  = 13
T_EXPERTISE = 15
T_SUPPORT   = 21
T_CAPACITY  = 22

# ═════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═════════════════════════════════════════════════════════════════════════════

t0 = time.time()

print("=" * 64)
print("  MENTOR-MENTEE OPTIMAL ESLESTIRME 2026")
print("  Yontem: Hungarian Algoritmasi + TF-IDF Cosine Similarity")
print("=" * 64)

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir   = os.path.join(script_dir, '..', 'data')
xlsx_files = glob.glob(os.path.join(data_dir, 'Mentor*2026*.xlsx'))
if not xlsx_files:
    raise FileNotFoundError(f"Excel dosyasi bulunamadi: {data_dir}")

xf = pd.read_excel(xlsx_files[0], sheet_name=None)

# -- Mentee --
mentee_raw = xf['Mentee']
mcols = [c for c in mentee_raw.columns if c is not None and str(c) != 'None']
mentee = mentee_raw[mcols].copy()
mentee = mentee[mentee.iloc[:, 0].notna()].reset_index(drop=True)

# -- Mentor --
mentor_raw = xf['Mentor']
trcols = [c for c in mentor_raw.columns if c is not None]
mentor = mentor_raw[trcols].copy()
mentor = mentor[mentor.iloc[:, 0].notna()].reset_index(drop=True)

# -- History --
history = xf['Son 3 yıl eşleşme'].copy()
history.columns = ['ID', 'MenteeName', 'Mentor', 'Year']

N = len(mentee)   # ALL mentees — starting from scratch
M = len(mentor)

print(f"\n  Veri Yuklendi:")
print(f"   Mentee sayisi      : {N}  (tumu sifirdan eslestirilecek)")
print(f"   Mentor sayisi      : {M}")

# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def clean(s):
    return str(s).lower().strip() if pd.notna(s) else ''

def parse_score(val):
    s = str(val)
    return int(s[0]) if s and s[0].isdigit() else 3

def parse_capacity(val):
    try:
        return int(val)
    except Exception:
        s = str(val).lower()
        if any(k in s for k in ['tüm', 'limit', 'ne kadar', 'sayı']):
            return 5
        return 2

# ═════════════════════════════════════════════════════════════════════════════
# CAPACITY (from scratch — ignore existing fills)
# ═════════════════════════════════════════════════════════════════════════════

capacities = np.array([parse_capacity(mentor.iloc[j, T_CAPACITY]) for j in range(M)])
total_cap  = int(capacities.sum())
print(f"   Toplam kapasite    : {total_cap} slot")
yeterli = 'YETERLI' if total_cap >= N else 'YETERSIZ!'
print(f"   Kapasite yeterliligi: {yeterli} ({total_cap} >= {N})")

# ═════════════════════════════════════════════════════════════════════════════
# HISTORICAL BLOCKS
# ═════════════════════════════════════════════════════════════════════════════

historical_pairs = set()
for _, row in history.iterrows():
    if pd.notna(row['MenteeName']) and pd.notna(row['Mentor']):
        historical_pairs.add((clean(row['MenteeName']), clean(row['Mentor'])))
print(f"   Gecmis eslesme     : {len(historical_pairs)} cift (bloklanacak)")

# ═════════════════════════════════════════════════════════════════════════════
# TEXT SIMILARITY ENGINE: TF-IDF + EXACT MATCH HYBRID
# ═════════════════════════════════════════════════════════════════════════════

# Turkish suffix list for basic stemming (agglutinative language handling)
TURKISH_SUFFIXES = [
    'lerin', 'ların', 'lerin', 'lere', 'lara', 'ları', 'leri',
    'ler', 'lar', 'nın', 'nin', 'nun', 'nün', 'dan', 'den',
    'tan', 'ten', 'daki', 'deki', 'nda', 'nde',
    'lik', 'lık', 'lük', 'luk', 'sı', 'si', 'su', 'sü',
    'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm',
    'ya', 'ye', 'ı', 'i',
]
TURKISH_SUFFIXES.sort(key=len, reverse=True)  # try longest first

def normalize_turkish(text):
    """Basic Turkish morphological normalization — strip common suffixes."""
    words = text.split()
    result = []
    for w in words:
        if w in TURKISH_STOPWORDS or len(w) <= 3:
            result.append(w)
            continue
        for sfx in TURKISH_SUFFIXES:
            if len(w) > len(sfx) + 3 and w.endswith(sfx):
                w = w[:-len(sfx)]
                break
        result.append(w)
    return ' '.join(result)

def _word_tfidf_matrix(texts_a, texts_b):
    """Word-level TF-IDF cosine similarity (1,2)-grams."""
    texts_a = [normalize_turkish(t) if t.strip() else 'bos' for t in texts_a]
    texts_b = [normalize_turkish(t) if t.strip() else 'bos' for t in texts_b]
    all_texts = texts_a + texts_b
    vectorizer = TfidfVectorizer(
        analyzer='word', lowercase=True,
        stop_words=list(TURKISH_STOPWORDS),
        sublinear_tf=True, min_df=1, max_df=0.95,
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w[\w]*\b',
    )
    try:
        tfidf = vectorizer.fit_transform(all_texts)
        na = len(texts_a)
        return np.clip(cosine_similarity(tfidf[:na], tfidf[na:]), 0.0, 1.0)
    except Exception:
        return np.zeros((len(texts_a), len(texts_b)))

def _char_tfidf_matrix(texts_a, texts_b):
    """Character n-gram (3-5) TF-IDF — handles Turkish morphological variations.
    e.g. 'mühendislik' and 'mühendis' share many character n-grams."""
    texts_a = [t if t.strip() else 'bos' for t in texts_a]
    texts_b = [t if t.strip() else 'bos' for t in texts_b]
    all_texts = texts_a + texts_b
    vectorizer = TfidfVectorizer(
        analyzer='char_wb', lowercase=True,
        sublinear_tf=True, min_df=1, max_df=0.95,
        ngram_range=(3, 5),
    )
    try:
        tfidf = vectorizer.fit_transform(all_texts)
        na = len(texts_a)
        return np.clip(cosine_similarity(tfidf[:na], tfidf[na:]), 0.0, 1.0)
    except Exception:
        return np.zeros((len(texts_a), len(texts_b)))

def _token_overlap_matrix(texts_a, texts_b):
    """Simple token overlap with normalization — good for short texts."""
    na, nb = len(texts_a), len(texts_b)
    mat = np.zeros((na, nb))
    for i, a in enumerate(texts_a):
        ta = set(normalize_turkish(a).split()) - TURKISH_STOPWORDS
        if not ta:
            continue
        for j, b in enumerate(texts_b):
            tb = set(normalize_turkish(b).split()) - TURKISH_STOPWORDS
            if tb:
                intersection = len(ta & tb)
                if intersection > 0:
                    mat[i, j] = intersection / max(len(ta), len(tb))
    return mat

def ensemble_similarity(texts_a, texts_b):
    """Multi-method ensemble: takes element-wise MAX of 3 approaches.
    This is the most robust approach for Turkish agglutinative text:
    - Word TF-IDF catches exact term matches with IDF weighting
    - Char n-gram TF-IDF catches morphological variations
    - Token overlap catches simple direct matches in short texts
    """
    sim_w = _word_tfidf_matrix(texts_a, texts_b)
    sim_c = _char_tfidf_matrix(texts_a, texts_b)
    sim_t = _token_overlap_matrix(texts_a, texts_b)
    return np.maximum(np.maximum(sim_w, sim_c), sim_t)

def exact_containment_matrix(texts_a, texts_b):
    """Exact or containment match for short texts like department names."""
    na, nb = len(texts_a), len(texts_b)
    mat = np.zeros((na, nb))
    for i, a in enumerate(texts_a):
        if not a:
            continue
        for j, b in enumerate(texts_b):
            if not b:
                continue
            if a == b:
                mat[i, j] = 1.0
            elif a in b or b in a:
                mat[i, j] = 0.85
    return mat

def city_match_matrix(cities_a, cities_b):
    """City matching with hierarchical rules."""
    na, nb = len(cities_a), len(cities_b)
    mat = np.zeros((na, nb))
    for i, ca in enumerate(cities_a):
        if not ca:
            continue
        for j, cb in enumerate(cities_b):
            if not cb:
                continue
            if ca == cb:
                mat[i, j] = 1.0
            elif ca.split(',')[0].strip() == cb.split(',')[0].strip():
                mat[i, j] = 0.8
            elif 'istanbul' in ca and 'istanbul' in cb:
                mat[i, j] = 1.0
            elif 'ankara' in ca and 'ankara' in cb:
                mat[i, j] = 1.0
            elif 'izmir' in ca and 'izmir' in cb:
                mat[i, j] = 1.0
    return mat

# ═════════════════════════════════════════════════════════════════════════════
# COMPUTE 5 SIMILARITY MATRICES (vectorized)
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Benzerlik matrisleri hesaplaniyor (TF-IDF Cosine)...")

# Extract RICH text fields — use multiple columns for each criterion
# Richer input → more tokens → better TF-IDF performance

me_career = [clean(mentee.iloc[i, M_CAREER]) + ' ' + clean(mentee.iloc[i, M_PREF_TEXT]) + ' ' + clean(mentee.iloc[i, M_SUPPORT]) for i in range(N)]
mr_sector = [clean(mentor.iloc[j, T_SECTOR]) + ' ' + clean(mentor.iloc[j, T_EXPERTISE]) + ' ' + clean(mentor.iloc[j, T_POSITION]) + ' ' + clean(mentor.iloc[j, T_SUPPORT]) for j in range(M)]

me_major  = [clean(mentee.iloc[i, M_MAJOR]) for i in range(N)]
mr_major  = [clean(mentor.iloc[j, T_MAJOR]) for j in range(M)]
me_pref   = [clean(mentee.iloc[i, M_PREF_TEXT]) for i in range(N)]

me_city   = [clean(mentee.iloc[i, M_CITY]) for i in range(N)]
mr_city   = [clean(mentor.iloc[j, T_CITY]) for j in range(M)]

me_interest = [clean(mentee.iloc[i, M_PREF_TEXT]) + ' ' + clean(mentee.iloc[i, M_SUPPORT]) + ' ' + clean(mentee.iloc[i, M_CAREER]) for i in range(N)]
mr_interest = [clean(mentor.iloc[j, T_HOBBIES]) + ' ' + clean(mentor.iloc[j, T_SUPPORT]) + ' ' + clean(mentor.iloc[j, T_EXPERTISE]) for j in range(M)]

me_support = [clean(mentee.iloc[i, M_SUPPORT]) for i in range(N)]
mr_support = [clean(mentor.iloc[j, T_SUPPORT]) for j in range(M)]

# 1. Sector/Career — Ensemble (Word TF-IDF + Char TF-IDF + Token Overlap)
print("   > [1/5] Sektor/kariyer benzerligi (ensemble)...")
sim_sector = ensemble_similarity(me_career, mr_sector)

# 2. Department — Ensemble + Exact/Containment hybrid (max of all)
print("   > [2/5] Bolum benzerligi (ensemble + exact hybrid)...")
sim_dept_ensemble = ensemble_similarity(
    [maj + ' ' + pref for maj, pref in zip(me_major, me_pref)],
    mr_major
)
sim_dept_exact = exact_containment_matrix(me_major, mr_major)
sim_dept = np.maximum(sim_dept_ensemble, sim_dept_exact)

# 3. City — Rule-based (categorical, not text)
print("   > [3/5] Sehir eslesmesi (kural tabanli)...")
sim_city = city_match_matrix(me_city, mr_city)

# 4. Interest — Ensemble
print("   > [4/5] Ilgi alani benzerligi (ensemble)...")
sim_interest = ensemble_similarity(me_interest, mr_interest)

# 5. Support topics — Ensemble
print("   > [5/5] Destek konusu benzerligi (ensemble)...")
sim_support = ensemble_similarity(me_support, mr_support)

print("   TAMAM: 5 benzerlik matrisi hazir (3-katmanli ensemble)")

# ═════════════════════════════════════════════════════════════════════════════
# BUILD PERSONALIZED WEIGHTED SCORE MATRIX (fully vectorized)
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Agirlikli puan matrisi olusturuluyor...")

# Mentee importance weights (N,) — each 1-5
w_dept = np.array([parse_score(mentee.iloc[i, M_SCR_DEPT]) for i in range(N)], dtype=float)
w_sec  = np.array([parse_score(mentee.iloc[i, M_SCR_SEC])  for i in range(N)], dtype=float)
w_city_w = np.array([parse_score(mentee.iloc[i, M_SCR_CITY]) for i in range(N)], dtype=float)
w_int  = np.array([parse_score(mentee.iloc[i, M_SCR_INT])  for i in range(N)], dtype=float)

# Normalize each weight to [0, 1] by dividing by MAX (5), not sum.
# This preserves absolute importance:
#   weight=5 → full contribution (1.0)
#   weight=3 → 60% contribution (0.6)
#   weight=1 → 20% contribution (0.2)
# Max theoretical score: all weights=5, all sims=1.0 → 100 points
f_sec  = (w_sec    / 5.0)[:, np.newaxis]
f_dept = (w_dept   / 5.0)[:, np.newaxis]
f_city = (w_city_w / 5.0)[:, np.newaxis]
f_int  = (w_int    / 5.0)[:, np.newaxis]

# Fully vectorized score computation: (N, M)
score_matrix = (
    f_sec  * W_SECTOR   * sim_sector   +
    f_dept * W_DEPT     * sim_dept     +
    f_city * W_CITY     * sim_city     +
    f_int  * W_INTEREST * sim_interest +
    W_SUPPORT           * sim_support
)

print(f"   Puan matrisi boyutu: {N} x {M} = {N*M:,} cift")
print(f"   Puan araligi (blok oncesi): {score_matrix.min():.2f} - {score_matrix.max():.2f}")

# ═════════════════════════════════════════════════════════════════════════════
# APPLY HARD BLOCKS
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Blok kurallari uygulaniyor...")

me_names    = [clean(mentee.iloc[i, M_NAME]) for i in range(N)]
mr_names    = [clean(mentor.iloc[j, T_NAME]) for j in range(M)]
old_mentors = [clean(mentee.iloc[i, M_OLD_MENTOR]) for i in range(N)]

block_count = 0
for i in range(N):
    for j in range(M):
        blocked = False
        # Block 1: Old mentor
        if old_mentors[i] and old_mentors[i] == mr_names[j]:
            blocked = True
        # Block 2: Historical pair
        if (me_names[i], mr_names[j]) in historical_pairs:
            blocked = True
        if blocked:
            score_matrix[i, j] = BLOCK_SCORE
            block_count += 1

print(f"   > {block_count} cift bloklandi (eski mentor + gecmis)")

# ═════════════════════════════════════════════════════════════════════════════
# EXPAND MENTORS BY CAPACITY FOR HUNGARIAN ALGORITHM
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Mentor kapasite genisletmesi...")

expanded_to_orig = []
for j in range(M):
    expanded_to_orig.extend([j] * capacities[j])

n_slots = len(expanded_to_orig)
expanded_to_orig = np.array(expanded_to_orig)

# Build expanded score matrix (N x n_slots)
expanded_scores = score_matrix[:, expanded_to_orig]

print(f"   Genisletilmis matris: {N} mentee x {n_slots} slot")

if n_slots < N:
    print(f"   UYARI: KAPASITE YETERSIZ: {n_slots} slot < {N} mentee")

# ═════════════════════════════════════════════════════════════════════════════
# HUNGARIAN ALGORITHM — GLOBALLY OPTIMAL ASSIGNMENT
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Hungarian algoritmasi calistiriliyor (global optimum)...")
t_hung = time.time()

# linear_sum_assignment minimizes -> negate to maximize
row_ind, col_ind = linear_sum_assignment(-expanded_scores)

t_hung = time.time() - t_hung
print(f"   > Cozum suresi: {t_hung:.2f} saniye")

# ═════════════════════════════════════════════════════════════════════════════
# EXTRACT ASSIGNMENTS
# ═════════════════════════════════════════════════════════════════════════════

assignments = []    # (mentee_idx, mentor_idx, score)
mentor_load_arr = np.zeros(M, dtype=int)

for r, c in zip(row_ind, col_ind):
    orig_j = expanded_to_orig[c]
    score  = expanded_scores[r, c]
    if score <= BLOCK_SCORE / 2:
        continue
    assignments.append((int(r), int(orig_j), float(score)))
    mentor_load_arr[orig_j] += 1

matched_set    = {a[0] for a in assignments}
unmatched_idx  = [i for i in range(N) if i not in matched_set]

scores_arr = np.array([a[2] for a in assignments])

high = int((scores_arr >= 15).sum())
mid  = int(((scores_arr >= 8) & (scores_arr < 15)).sum())
low  = int((scores_arr < 8).sum())
total_score = float(scores_arr.sum())

print(f"\n{'=' * 64}")
print(f"  SONUCLAR")
print(f"{'=' * 64}")
print(f"   Eslesen mentee  : {len(assignments)} / {N}")
print(f"   Eslesemeyen     : {len(unmatched_idx)}")
print(f"   Ortalama puan   : {scores_arr.mean():.2f}")
print(f"   Medyan puan     : {np.median(scores_arr):.2f}")
print(f"   Maks puan       : {scores_arr.max():.2f}")
print(f"   Min puan        : {scores_arr.min():.2f}")
print(f"   Std sapma       : {scores_arr.std():.2f}")
print(f"   Yuksek (>=15)   : {high}  ({high/len(assignments)*100:.1f}%)")
print(f"   Orta (8-14)     : {mid}  ({mid/len(assignments)*100:.1f}%)")
print(f"   Dusuk (<8)      : {low}  ({low/len(assignments)*100:.1f}%)")
print(f"   Toplam puan     : {total_score:.1f}")

# ═════════════════════════════════════════════════════════════════════════════
# BUILD RESULT DATAFRAMES
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Sonuc tablolari hazirlaniyor...")

results = []
for me_i, mr_j, score in assignments:
    # Top-3 alternatives
    mentee_scores = score_matrix[me_i].copy()
    mentee_scores[mr_j] = -np.inf
    top3_idx = np.argsort(-mentee_scores)[:3]
    alts = []
    for aj in top3_idx:
        if mentee_scores[aj] > BLOCK_SCORE / 2:
            alts.append(f"{mentor.iloc[aj, T_NAME]} ({mentee_scores[aj]:.1f})")

    # Score breakdown per criterion
    fi_sec  = float(f_sec[me_i])
    fi_dept = float(f_dept[me_i])
    fi_city = float(f_city[me_i])
    fi_int  = float(f_int[me_i])

    s_sec = fi_sec * W_SECTOR * sim_sector[me_i, mr_j]
    s_dep = fi_dept * W_DEPT * sim_dept[me_i, mr_j]
    s_cit = fi_city * W_CITY * sim_city[me_i, mr_j]
    s_int = fi_int * W_INTEREST * sim_interest[me_i, mr_j]
    s_sup = W_SUPPORT * sim_support[me_i, mr_j]

    results.append({
        'Mentee_Adı':           mentee.iloc[me_i, M_NAME],
        'Mentee_ID':            int(mentee.iloc[me_i, M_ID]) if pd.notna(mentee.iloc[me_i, M_ID]) else '',
        'Mentee_Bölüm':        mentee.iloc[me_i, M_MAJOR],
        'Mentee_Kariyer':       str(mentee.iloc[me_i, M_CAREER])[:120],
        'Mentee_Şehir':        mentee.iloc[me_i, M_CITY],
        'Mentor_Adı':           mentor.iloc[mr_j, T_NAME],
        'Mentor_Sektör':        mentor.iloc[mr_j, T_SECTOR],
        'Mentor_Pozisyon':      mentor.iloc[mr_j, T_POSITION],
        'Mentor_Şehir':         mentor.iloc[mr_j, T_CITY],
        'Toplam_Puan':          round(score, 2),
        'Sektör_P':             round(s_sec, 2),
        'Bölüm_P':              round(s_dep, 2),
        'Şehir_P':              round(s_cit, 2),
        'İlgi_P':               round(s_int, 2),
        'Destek_P':             round(s_sup, 2),
        'Alternatifler':        ' | '.join(alts),
        'Eski_Mentor':          mentee.iloc[me_i, M_OLD_MENTOR] if pd.notna(mentee.iloc[me_i, M_OLD_MENTOR]) else '',
    })

results_df = pd.DataFrame(results)

# Unmatched
unmatched_rows = []
for ui in unmatched_idx:
    unmatched_rows.append({
        'Mentee_Adı': mentee.iloc[ui, M_NAME],
        'Mentee_ID':  mentee.iloc[ui, M_ID],
        'Sebep':      'Kapasite yetersiz veya tum mentorler bloklu',
    })
unmatched_df = pd.DataFrame(unmatched_rows) if unmatched_rows else pd.DataFrame(columns=['Mentee_Adı','Mentee_ID','Sebep'])

# Mentor load summary
load_rows = []
for j in range(M):
    load_rows.append({
        'Mentor_Adı':      mentor.iloc[j, T_NAME],
        'Sektör':          mentor.iloc[j, T_SECTOR],
        'Kapasite':        int(capacities[j]),
        'Atanan_Mentee':   int(mentor_load_arr[j]),
        'Kalan_Kapasite':  int(capacities[j] - mentor_load_arr[j]),
    })
load_df = pd.DataFrame(load_rows)

# ═════════════════════════════════════════════════════════════════════════════
# EXCEL OUTPUT — beautifully formatted
# ═════════════════════════════════════════════════════════════════════════════

print("  Excel raporu olusturuluyor...")

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()

# -- Style helpers --
BLUE_H   = 'FF1E3A5F'
GREEN_BG = 'FFE8F5E9'
AMBER_BG = 'FFFFF8E1'
RED_BG   = 'FFFFEBEE'
GREEN_H  = 'FF2E7D32'

thin = Border(
    left=Side(style='thin', color='FFD0D0D0'),
    right=Side(style='thin', color='FFD0D0D0'),
    top=Side(style='thin', color='FFD0D0D0'),
    bottom=Side(style='thin', color='FFD0D0D0'),
)

def style_header(ws, row, bg='FF1E3A5F'):
    for cell in ws[row]:
        if cell.value is None:
            continue
        cell.font = Font(bold=True, color='FFFFFFFF', name='Arial', size=10)
        cell.fill = PatternFill('solid', start_color=bg)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin

def style_row(ws, row, bg=None):
    for cell in ws[row]:
        cell.font = Font(name='Arial', size=9)
        cell.alignment = Alignment(vertical='center', wrap_text=True)
        cell.border = thin
        if bg:
            cell.fill = PatternFill('solid', start_color=bg)

def set_widths(ws, widths):
    for letter, w in widths.items():
        ws.column_dimensions[letter].width = w

# =============== SHEET 1: Eslesme Sonuclari ===============
ws1 = wb.active
ws1.title = 'Eslesmeler'
ws1.row_dimensions[1].height = 20
ws1.row_dimensions[2].height = 35

title = f'OPTIMAL Mentor-Mentee Eslestirme 2026  |  Hungarian + TF-IDF  |  {len(results_df)} eslesme, {len(unmatched_df)} eslesmeyen'
ws1['A1'] = title
ws1['A1'].font = Font(bold=True, name='Arial', size=11, color=BLUE_H)
ws1.merge_cells('A1:Q1')

headers = ['Mentee Adi', 'Mentee ID', 'Bolum', 'Kariyer Hedefi', 'Mentee Sehir',
           'Mentor Adi', 'Mentor Sektor', 'Mentor Pozisyon', 'Mentor Sehir',
           'Toplam Puan', 'Sektor P.', 'Bolum P.', 'Sehir P.', 'Ilgi P.', 'Destek P.',
           'Alternatifler', 'Eski Mentor']
ws1.append(headers)
style_header(ws1, 2)

for idx, row in results_df.iterrows():
    ws1.append(list(row))
    bg = GREEN_BG if idx % 2 == 0 else 'FFFFFFFF'
    style_row(ws1, idx + 3, bg)
    # Color score cell (column J = 10)
    sc = ws1.cell(row=idx + 3, column=10)
    try:
        v = float(sc.value)
        if v >= 15:
            sc.fill = PatternFill('solid', start_color='FFB9F6CA')
            sc.font = Font(bold=True, name='Arial', size=9, color='FF1B5E20')
        elif v >= 8:
            sc.fill = PatternFill('solid', start_color='FFFFF9C4')
            sc.font = Font(bold=True, name='Arial', size=9, color='FFF57F17')
        else:
            sc.fill = PatternFill('solid', start_color='FFFFCDD2')
            sc.font = Font(bold=True, name='Arial', size=9, color='FFB71C1C')
    except Exception:
        pass

ws1.freeze_panes = 'A3'
ws1.auto_filter.ref = f'A2:Q{len(results_df)+2}'
set_widths(ws1, {
    'A': 22, 'B': 10, 'C': 18, 'D': 32, 'E': 16,
    'F': 22, 'G': 22, 'H': 22, 'I': 16, 'J': 12,
    'K': 10, 'L': 10, 'M': 10, 'N': 10, 'O': 10,
    'P': 40, 'Q': 20,
})

# =============== SHEET 2: Eslestirilemeyenler ===============
ws2 = wb.create_sheet('Eslestirilemeyenler')
ws2['A1'] = f'Eslestirilemeyenler  |  Toplam: {len(unmatched_df)}'
ws2['A1'].font = Font(bold=True, name='Arial', size=12, color='FFB71C1C')
ws2.merge_cells('A1:C1')

if not unmatched_df.empty:
    ws2.append(['Mentee Adi', 'Mentee ID', 'Sebep'])
    style_header(ws2, 2, bg='FFB71C1C')
    for idx, row in unmatched_df.iterrows():
        ws2.append(list(row))
        style_row(ws2, idx + 3, RED_BG)
else:
    ws2['A2'] = 'Tum menteeler basariyla eslestirildi!'
    ws2['A2'].font = Font(bold=True, name='Arial', size=11, color=GREEN_H)
set_widths(ws2, {'A': 25, 'B': 12, 'C': 50})

# =============== SHEET 3: Mentor Yuk Ozeti ===============
ws3 = wb.create_sheet('Mentor Yuk')
ws3['A1'] = 'Mentor Kapasite ve Yuk Ozeti (Sifirdan Eslestirme)'
ws3['A1'].font = Font(bold=True, name='Arial', size=12, color=BLUE_H)
ws3.merge_cells('A1:E1')
ws3.row_dimensions[2].height = 35

ws3.append(['Mentor Adi', 'Sektor', 'Kapasite', 'Atanan Mentee', 'Kalan Kapasite'])
style_header(ws3, 2)

load_sorted = load_df.sort_values('Atanan_Mentee', ascending=False)
for idx, (_, row) in enumerate(load_sorted.iterrows()):
    ws3.append(list(row))
    bg = GREEN_BG if row['Kalan_Kapasite'] > 0 else AMBER_BG
    style_row(ws3, idx + 3, bg)

ws3.freeze_panes = 'A3'
ws3.auto_filter.ref = f'A2:E{len(load_df)+2}'
set_widths(ws3, {'A': 25, 'B': 28, 'C': 10, 'D': 16, 'E': 16})

# =============== SHEET 4: Ozet Istatistik ===============
ws4 = wb.create_sheet('Ozet')
ws4.column_dimensions['A'].width = 40
ws4.column_dimensions['B'].width = 20

remaining_cap = capacities - np.array([mentor_load_arr[j] for j in range(M)])
dolu_mentor = int((remaining_cap == 0).sum())
bos_mentor  = int((remaining_cap > 0).sum())
hic_atanmamis = int((np.array([mentor_load_arr[j] for j in range(M)]) == 0).sum())

stats = [
    ('OPTIMAL ESLESTIRME OZETI 2026', ''),
    ('Yontem: Hungarian Algoritmasi + TF-IDF', ''),
    ('', ''),
    ('Toplam Mentee', N),
    ('Toplam Mentor', M),
    ('Toplam Mentor Kapasitesi', total_cap),
    ('', ''),
    ('Eslesen Mentee', len(assignments)),
    ('Eslesemeyen Mentee', len(unmatched_idx)),
    ('Basari Orani', f'{len(assignments)/N*100:.1f}%'),
    ('', ''),
    ('PUAN ISTATISTIKLERI', ''),
    ('Ortalama Puan', f'{scores_arr.mean():.2f}'),
    ('Medyan Puan', f'{np.median(scores_arr):.2f}'),
    ('Standart Sapma', f'{scores_arr.std():.2f}'),
    ('Minimum Puan', f'{scores_arr.min():.2f}'),
    ('Maksimum Puan', f'{scores_arr.max():.2f}'),
    ('Toplam Puan', f'{total_score:.1f}'),
    ('', ''),
    ('PUAN DAGILIMI', ''),
    ('Yuksek (>=15)', f'{high}  ({high/len(assignments)*100:.1f}%)'),
    ('Orta (8-14)', f'{mid}  ({mid/len(assignments)*100:.1f}%)'),
    ('Dusuk (<8)', f'{low}  ({low/len(assignments)*100:.1f}%)'),
    ('', ''),
    ('MENTOR DOLULUK', ''),
    ('Dolu kapasitedeki mentor', dolu_mentor),
    ('Bos kapasitesi kalan', bos_mentor),
    ('Hic atanmamis mentor', hic_atanmamis),
    ('', ''),
    ('BLOK BILGISI', ''),
    ('Gecmis eslesme blogu', len(historical_pairs)),
    ('Toplam bloklanan cift', block_count),
    ('', ''),
    ('Hesaplama suresi', f'{time.time() - t0:.1f} saniye'),
]

for r, (label, value) in enumerate(stats, start=1):
    ws4.cell(row=r, column=1, value=label)
    ws4.cell(row=r, column=2, value=value)
    if label and value == '':
        ws4.cell(row=r, column=1).font = Font(bold=True, name='Arial', size=11, color='FF1E3A5F')
        ws4.cell(row=r, column=1).fill = PatternFill('solid', start_color='FFE3F2FD')
    elif label:
        ws4.cell(row=r, column=1).font = Font(name='Arial', size=10)
        ws4.cell(row=r, column=2).font = Font(bold=True, name='Arial', size=10)

# =============== SAVE ===============
out_path = os.path.join(data_dir, 'Mentor_Mentee_Optimal_Eslestirme_2026.xlsx')
wb.save(out_path)

elapsed = time.time() - t0
print(f"\n{'=' * 64}")
print(f"  TAMAMLANDI - {elapsed:.1f} saniye")
print(f"{'=' * 64}")
print(f"  Dosya: {out_path}")
print(f"  Eslesme: {len(assignments)} / {N}")
print(f"  Ortalama puan: {scores_arr.mean():.2f}")
print(f"  Yuksek: {high}  Orta: {mid}  Dusuk: {low}")
print(f"{'=' * 64}")
