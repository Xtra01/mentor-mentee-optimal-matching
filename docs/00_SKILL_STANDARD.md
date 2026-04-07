# PROJECT STRUCTURE & STANDARDIZATION GUIDE

**Version**: 1.0 | **Scope**: mentor_mentee project | **Status**: Active

---

## 📁 PROJECT FOLDER ORGANIZATION

This project follows a **strict internal classification system** to maintain clarity and scalability.

```
mentor_mentee/
├── README.md                              [Project entry]
├── .gitignore                             [Git config]
│
├── 📚 docs/                               [ALL DOCUMENTATION]
│   ├── 00_SKILL_STANDARD.md              [This file - standardization]
│   ├── 01_PROJECT_ANALYSIS.md            [Detailed technical analysis]
│   ├── 02_COMPREHENSIVE_GUIDE.md         [Full system guide]
│   ├── 03_EMBEDDING_GUIDE.md             [Embedding 384-dim]
│   ├── 04_RESULTS_ANALYSIS.md            [2026 Results & metrics]
│   └── GLOSSARY.md                       [Technical terms]
│
├── 📦 data/                               [ALL DATA - 4-TIER STRUCTURE]
│   ├── 01_raw/                           [Original source files]
│   │   └── Mentor_Mentee_2026_*.xlsx     (input)
│   ├── 02_processed/                     [Cleaned & transformed]
│   ├── 03_cache/                         [Pre-computed models]
│   │   └── embeddings_*.pkl
│   └── 04_output/                        [Results & artifacts]
│       └── optimal_matching_2026.xlsx
│
├── 💻 scripts/                            [ALL PYTHON CODE]
│   ├── 01_main_hungarian.py              [Main algorithm]
│   ├── 02_greedy_backup.py               [Legacy backup]
│   ├── 03_embedding_matcher.py           [Embedding similarity]
│   └── utils/
│       ├── __init__.py
│       ├── config.py                     [Configuration]
│       ├── turkish_nlp.py                [Turkish processing]
│       ├── similarity_engines.py         [Similarity computation]
│       └── helpers.py                    [Utilities]
│
├── 🔧 config/                             [CONFIGURATION FILES]
│   ├── default.yaml                      [Main parameters]
│   └── production.yaml                   [Production settings]
│
├── ✓ tests/                               [UNIT TESTS]
│   └── (empty - ready for tests)
│
└── 📊 reports/                            [ANALYSIS & RESULTS]
    ├── 2026_matching_results.md
    └── comparison_reports/
```

---

## 📋 NAMING CONVENTIONS

### Python Files
```
✅ 01_main_hungarian.py        [Numbered, clear purpose]
✅ 02_greedy_backup.py
✅ utils/config.py             [Helpers - no number]
✅ utils/helpers.py

❌ DataProcessor.py            [PascalCase bad]
❌ main.py                     [No context]
❌ process.py                  [Unclear]
```

### Data Files
```
✅ 01_raw/input_data.xlsx
✅ 02_processed/cleaned_data.csv
✅ 03_cache/embeddings_384.pkl
✅ 04_output/results.xlsx

❌ data.xlsx                   [Vague]
❌ v2_final_latest.xlsx        [Version chaos]
```

### Documentation
```
✅ docs/00_SKILL_STANDARD.md
✅ docs/01_PROJECT_ANALYSIS.md
✅ docs/02_COMPREHENSIVE_GUIDE.md

❌ analysis.md                 [No number, no location]
❌ final_report_v3.md          [Version mess]
```

---

## 🏗️ FOLDER PURPOSES

| Folder | Purpose | Max Size | Git-tracked |
|--------|---------|----------|-------------|
| **docs/** | Markdown documentation | 100MB | ✅ YES |
| **data/01_raw/** | Original source files | Unlimited | ✅ YES (small) |
| **data/02_processed/** | Transformed data | 1GB | ❌ .gitignore |
| **data/03_cache/** | Pre-computed models | 2GB | ❌ .gitignore |
| **data/04_output/** | Results files | 500MB | ✅ YES (key results) |
| **scripts/** | Python code | Unlimited | ✅ YES |
| **scripts/utils/** | Helper modules | Unlimited | ✅ YES |
| **config/** | Configuration YAML | 1MB | ✅ YES |
| **tests/** | Unit tests | 10MB | ✅ YES |
| **reports/** | Analysis reports | 50MB | ✅ YES |

---

## 🚀 FOLDER ORGANIZATION RULES

### RULE 1: No Files Outside Folders
```
❌ BAD:
  mentor_mentee/
  ├── script.py           (loose file!)
  ├── data.xlsx           (loose file!)
  └── report.md           (loose file!)

✅ GOOD:
  mentor_mentee/
  ├── scripts/
  │   └── 01_main.py
  ├── data/
  │   └── 01_raw/data.xlsx
  └── docs/
      └── 01_report.md
```

### RULE 2: 4-Tier Data Organization
```
Raw Data → Processed → Cache → Output

01_raw/    : Never modify, original only
02_processed/ : Cleaning, transformation
03_cache/  : Pre-computed (models, embeddings)
04_output/ : Results, artifacts, reports
```

### RULE 3: Numbered Modules in Scripts
```
01_main_hungarian.py      [Primary algorithm]
02_greedy_backup.py       [Secondary algorithm]
03_embedding_matcher.py   [New algorithm]
(Helpers stay unnumbered)
```

### RULE 4: Config in Single Location
```
❌ No hardcoded params in scripts
✅ All configs in config/default.yaml
✅ Load at startup: from utils.config import load_config
```

---

## 📖 DOCUMENTATION TIER SYSTEM

### Tier 0: Entry Point
```
README.md              → Quick start, 5-minute overview
```

### Tier 1: Overview
```
docs/00_SKILL_STANDARD.md    → This document (structure)
docs/01_PROJECT_ANALYSIS.md  → What the project does
```

### Tier 2: Technical
```
docs/02_COMPREHENSIVE_GUIDE.md   → How it works (algorithms)
docs/03_EMBEDDING_GUIDE.md       → Embedding details
```

### Tier 3: Results
```
docs/04_RESULTS_ANALYSIS.md      → 2026 results & metrics
reports/                         → Detailed reports
```

### Tier 4: Reference
```
docs/GLOSSARY.md                 → Technical terminology
```

---

## 🔄 WORKFLOW

When adding **new files**:

1. **Identify category**: Code? Data? Doc?
2. **Choose folder**: scripts/ or data/0X_*/ or docs/
3. **Pick name**:
   - Code: `NN_description.py` (numbered)
   - Data: `NN_processed_name.csv` (in data/0X_)
   - Docs: `NN_title.md` (numbered in docs/)
4. **Add to .gitignore** if too large
5. **Document** in README

---

## ✅ COMPLIANCE CHECKLIST

Before finalizing project:

- [ ] All `.py` files in `scripts/` (no loose files)
- [ ] All data in `data/` with 01_raw/ origin
- [ ] All docs in `docs/` with 00-NN_ numbering
- [ ] No files loose in root (except README, .gitignore)
- [ ] Config in `config/` YAML
- [ ] Parameters NOT hardcoded in scripts
- [ ] .gitignore covers `data/02_*`, `data/03_*`
- [ ] README.md updated with new structure

---

## 🎯 BENEFITS

This structure provides:

✅ **Clarity**: Folder name = content type (first glance)
✅ **Scalability**: Add 04_*, 05_* modules easily
✅ **Modularity**: Independent, reusable components
✅ **Hygiene**: Data 4-tier prevents mess
✅ **Versioning**: Git-friendly, no blob files
✅ **Documentation**: Multi-level, discoverable

---

**Status**: ACTIVE | **Version**: 1.0 | **Last Updated**: Apr 7, 2026
