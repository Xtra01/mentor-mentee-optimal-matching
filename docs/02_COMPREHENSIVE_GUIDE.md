# COMPREHENSIVE TECHNICAL GUIDE

**Location**: `docs/02_COMPREHENSIVE_GUIDE.md`  
**Audience**: Developers, Data Scientists  
**Depth**: Deep technical dive

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────┐
│ INPUT: Excel 3-sheet (Mentee, Mentor, Hist) │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ DATA LOADING & PARSING                       │
│ - Extract fields from each sheet             │
│ - Parse importance weights (1-5)             │
│ - Parse mentor capacities                    │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ SIMILARITY MATRICES (5 Criteria)             │
│ - Word TF-IDF + Char n-gram + Token overlap  │
│ - Result: 5 matrices of shape (308, 225)     │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ WEIGHTED SCORE MATRIX                        │
│ - Apply personalized mentee weights          │
│ - Combine 5 criteria → single score          │
│ - Shape: (308, 225), values: [0, 36]         │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ BLOCK RULES APPLICATION                      │
│ - Old mentor → -1e9                          │
│ - Historical pairs → -1e9                    │
│ - ~50 pairs blocked                          │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ CAPACITY EXPANSION                           │
│ - Replicate each mentor by capacity          │
│ - Shape: (308, 1200+)                        │
│ - Ready for Hungarian                        │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ HUNGARIAN ALGORITHM                          │
│ linear_sum_assignment(-scores)               │
│ → GLOBAL OPTIMUM ASSIGNMENT ✨               │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ RESULT PROCESSING                            │
│ - Extract 308 assignments                    │
│ - Compute statistics                         │
│ - Quality binning (high/medium/low)          │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ EXCEL REPORT GENERATION                      │
│ - 4 sheets: Matches, Unmatched, Load, Stats  │
│ - Formatting: Colors, borders, freezing      │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│ OUTPUT: optimal_matching_2026.xlsx            │
└──────────────────────────────────────────────┘
```

---

## 📐 MATHEMATICAL FORMULATION

### Score Matrix Computation

```
S[i,j] = Σ (weighted_criterion_k × similarity_k[i,j])

Where:
  i ∈ [1, 308]  (mentee index)
  j ∈ [1, 225]  (mentor index)
  k ∈ [1, 5]    (criterion: sector, dept, city, interest, support)

Specifically:
  S[i,j] = (w_sector[i]/5) × 35 × sim_sector[i,j]
         + (w_dept[i]/5) × 30 × sim_dept[i,j]
         + (w_city[i]/5) × 15 × sim_city[i,j]
         + (w_interest[i]/5) × 10 × sim_interest[i,j]
         + 10 × sim_support[i,j]

Domain:
  w_X[i] ∈ [1, 5]       (mentee importance scores)
  sim_X[i,j] ∈ [0, 1]   (normalized similarity)
  S[i,j] ∈ [0, 36]      (typical range)
```

### TF-IDF Similarity Calculation

```
Layer 1: Word TF-IDF (1,2-grams)
  -----------
  1. Tokenize: "yazılım geliştirme" → ["yazılım", "geliştirme"]
  2. Normalize: Remove Turkish stopwords
  3. TF: Count term frequency
  4. IDF: Weight by rarity (inverse document frequency)
  5. Vectorize: Each text → vector
  6. Similarity: cosine(vector_i, vector_j)

Layer 2: Char N-gram TF-IDF (3-5-grams)
  ----------
  1. Extract: "yazılım" → ["yaz", "azı", "zıl", "ılı", "lım", ...]
  2. TF-IDF on characters
  3. Handles morphological variations

Layer 3: Token Overlap
  -----------
  1. Extract tokens
  2. Intersection / max(len_a, len_b)
  3. Result: [0, 1] simple ratio

Ensemble: MAX(Layer1, Layer2, Layer3)
  --------
  Rationale: At least one method will match correctly
```

### Block Rules Implementation

```python
# Rule 1: Old mentor blocking
for i in range(N):  # for each mentee
    old_mentor = mentee_data[i, 'old_mentor']
    for j in range(M):  # for each mentor
        if old_mentor == mentor_data[j, 'name']:
            score_matrix[i, j] = -1e9  # Block!

# Rule 2: Historical pair blocking
historical_pairs = load_historical_data('Son 3 yıl eşleşme')
for (mentee_name, mentor_name) in historical_pairs:
    i = find_mentee_index(mentee_name)
    j = find_mentor_index(mentor_name)
    score_matrix[i, j] = -1e9  # Block!
```

### Capacity Expansion (For Hungarian)

```
Problem: Hungarian solves assignment (each row → ≤1 column)
        But mentors have different capacities (2-5)

Solution: Replicate columns by capacity

Example:
  Mentor A: capacity=2  → [A, A]
  Mentor B: capacity=3  → [B, B, B]
  Mentor C: capacity=2  → [C, C]
  
  expanded_to_original = [0, 0, 1, 1, 1, 2, 2]
  Expanded matrix shape: (308, 7)
  
After Hungarian:
  Result row i assigned to column c
  Original mentor: expanded_to_original[c]
```

### Hungarian Algorithm (Kuhn-Munkres)

```
Input: Cost matrix C of shape (n, m)
Goal: Find assignment that minimizes total cost
      (or maximizes if negated)

Algorithm:
  1. Subtract row minima
  2. Subtract column minima
  3. Cover zeros with minimum lines
  4. Augment unmatched rows/columns
  5. Repeat until all covered

Complexity: O(n³)
Implementation: scipy.optimize.linear_sum_assignment()
Result: Optimal assignment with proof

Example:
  Mentee 0 → Mentor slot 5 (original mentor: 1)
  Mentee 1 → Mentor slot 2 (original mentor: 0)
  Mentee 2 → Mentor slot 6 (original mentor: 2)
  ...all 308 mentees assigned
```

---

## 🔬 SIMILARITY DETAILS

### Sector/Career Matching (35pt)

**Mentee Input**:
```
Career goal: "Yazılım mühendisliği"
Preference: "Python, agile development"
Support topics: "Karir planlaması"
```

**Mentor Input**:
```
Sector: "Yazılım geliştirme"
Expertise: "Python, sistem tasarımı"
Position: "Senior software architect"
Support: "Agile coaching"
```

**Computation**:
```
Combined mentee text = career + preference + support
  = "yazılım mühendisliği python agile development karir planlaması"

Combined mentor text = sector + expertise + position + support
  = "yazılım geliştirme python sistem tasarımı senior architect agile"

Similarity (ensemble):
  Layer 1 (word TF-IDF): 0.87
  Layer 2 (char n-gram): 0.89
  Layer 3 (token overlap): 0.75
  
  FINAL = MAX(0.87, 0.89, 0.75) = 0.89  ← Use this
  
Score: 0.89 × 35 = 31.15 points (out of 35)
```

### City Matching (15pt) - RULE-BASED

```python
def city_match(mentee_city, mentor_city):
    """Categorical matching, not TF-IDF"""
    
    if mentee_city == mentor_city:
        return 1.0  # Exact match
    
    # Split by comma (e.g., "Istanbul, Avcılar")
    mentee_district = mentee_city.split(',')[0].strip()
    mentor_district = mentor_city.split(',')[0].strip()
    
    if mentee_district == mentor_district:
        return 0.8  # Same district, different area
    
    # Metro city grouping
    metro_cities = {'istanbul', 'ankara', 'izmir'}
    if mentee_city.lower() in metro_cities and mentor_city.lower() in metro_cities:
        return 1.0  # Same metro region counts as close
    
    return 0.0  # Different regions
```

---

## 💾 DATA STRUCTURES

### Input DataFrame: Mentee

| Column | Type | Purpose |
|--------|------|---------|
| Name | str | Unique identifier |
| ID | int | Student ID |
| City | str | Living location |
| Major | str | Academic department |
| Career Goal | str | Long-term aspiration |
| Preference Text | str | Mentor description |
| Support Request | str | Topics to help with |
| Weight_dept | int | 1-5 importance |
| Weight_sector | int | 1-5 importance |
| Weight_city | int | 1-5 importance |
| Weight_interest | int | 1-5 importance |
| Old Mentor | str | Last year's mentor (blocking) |

### Input DataFrame: Mentor

| Column | Type | Purpose |
|--------|------|---------|
| Name | str | Unique identifier |
| City | str | Location |
| Hobbies | str | Personal interests |
| Major | str | KU graduation |
| Sector | str | Industry/domain |
| Position | str | Job title |
| Expertise | str | Skills & knowledge |
| Support | str | Mentorship areas |
| Capacity | int | Max mentees (2-5) |

### Output DataFrame: Match Results

| Column | Type | Purpose |
|--------|------|---------|
| Mentee Name | str | Who |
| Mentor Name | str | Assigned to |
| Total Score | float | 0-36 |
| Sector P | float | Criterion 1 contribution |
| Dept P | float | Criterion 2 contribution |
| City P | float | Criterion 3 contribution |
| Interest P | float | Criterion 4 contribution |
| Support P | float | Criterion 5 contribution |
| Alternatives | str | Top-3 other mentors |

---

## ⚙️ DEPENDENCIES

```python
pandas>=2.0.0          # DataFrames
numpy>=1.24.0          # Arrays, math
scipy>=1.10.0          # linear_sum_assignment (Hungarian)
scikit-learn>=1.2.0    # TfidfVectorizer
openpyxl>=3.10.0       # Excel export
```

---

## 🎯 PERFORMANCE METRICS

### Computational Performance
```
Data loading:      1.5 sec
TF-IDF vectors:    3.2 sec
Similarity matrix: 1.8 sec
Score computation: 0.5 sec
Block rules:       0.1 sec
Hungarian solve:   5.2 sec  ← Bottleneck but acceptable
Excel export:      1.5 sec

TOTAL:            ~13 sec
```

### Quality Performance (2026)
```
Success rate:  100% (308/308 matched)
High quality:  63.3% (score ≥15)
Avg score:     16.98/36
Max score:     35.9/36
Min score:     3.2/36
```

---

## 🔍 VALIDATION

**How do we know Hungarian found the optimum?**

```
1. Mathematical proof:
   - Hungarian algoritm is polynomial-time optimal
   - For any assignment problem, finds maximum-weight matching
   - Proven by König & Egerváry (1931)

2. Empirical validation:
   - Greedy result: ~4500 points
   - Hungarian result: 5229.2 points
   - Improvement: +14% (greedy was suboptimal)

3. Boundary check:
   - If all similarities were 1.0:
     Max possible = 308 × 36 = 11,088 points
   - Our result: 5229.2 points
   - Ratio: 47% of theoretical max
   - (Expected, since data is realistic, not perfect)
```

---

**See**: `03_EMBEDDING_GUIDE.md` for semantic embeddings extension  
**See**: `04_RESULTS_ANALYSIS.md` for 2026 detailed results
