import pandas as pd
import numpy as np
import yaml
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ---------------------------------------------------------
# PhD-Level Mentor-Mentee Hybrid Matching Algorithm v3.0
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class HybridMatcherV3:
    """
    Advanced Matching System Incorporating 5 Core Redesigns:
    1. Multi-lingual Text Encoding (Turkish & English Contexts)
    2. Temporal-Career Trajectory Scoring (Mentor Quality / Peer-Mentorship)
    3. Semantic Category Extraction (Sector vs Sub-Sector Granularity)
    4. Network Effects Integration (Prioritizing missing network traits)
    5. Contextual Uncertainty Handling (Routing "unsure" mentees to general career coaches)
    """

    def __init__(self, config_path="../config/default.yaml"):
        # Load Configuration
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            logging.info("Configuration loaded.")
        except FileNotFoundError:
            self.config = {}
            logging.warning("No config found, proceeding with defaults.")

        # Load Multi-lingual Embedding Model (Solves Problem 1)
        # Using a model capable of bridging English and Turkish text natively
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logging.info("Loaded multi-lingual sentence transformer (384-dim).")
        
        # Uncertainty Triggers (Solves Problem 5)
        self.uncertainty_keywords = [
            "emin değilim", "kararsızım", "arayıştayım", 
            "not sure", "undecided", "don't know", "bilmiyorum",
            "karar veremedim"
        ]
        
        # International Intent Triggers
        self.international_keywords = [
            "yurtdışı", "avrupa", "amerika", "abroad", 
            "international", "global", "overseas"
        ]

    def _detect_uncertainty(self, text):
        """Detects if a mentee is highly uncertain about their career."""
        text_lower = str(text).lower()
        return any(keyword in text_lower for keyword in self.uncertainty_keywords)

    def _detect_international_intent(self, text):
        """Detects if a mentee specifically wants international/abroad scope."""
        text_lower = str(text).lower()
        return any(keyword in text_lower for keyword in self.international_keywords)

    def compute_mentor_quality_score(self, mentor_row):
        """
        Solves Problem 2: Temporal-Career Trajectory Scoring.
        Heuristics on graduation year and title string to infer seniority.
        """
        score = 0
        title = str(mentor_row.get("Guncel_Unvan", "")).lower()
        grad_year = mentor_row.get("Lisans_Mezuniyet_Yili", 2026)

        # Title heuristics
        if any(w in title for w in ["kurucu", "founder", "ceo", "director", "direktör", "manager", "müdür"]):
            score += 3
        elif any(w in title for w in ["kıdemli", "senior", "lead", "uzman"]):
            score += 2
        else:
            score += 1

        # Year heuristics (older = more senior)
        try:
            years_exp = 2026 - int(grad_year)
            if years_exp > 10:
                score += 3
            elif years_exp > 5:
                score += 2
            else:
                score += 1
        except:
            score += 1

        return score

    def compute_hybrid_similarity(self, mentee, mentor):
        """
        Computes the dense 5-factor similarity between a mentee and a mentor.
        """
        score = 0.0

        mentee_goal = str(mentee.get("Kariyer_Hedefi", ""))
        mentor_dept = str(mentor.get("Guncel_Departman", ""))
        mentor_sector = str(mentor.get("Guncel_Sektor", ""))
        mentor_title = str(mentor.get("Guncel_Unvan", ""))

        # 1. Uncertainty Handling (Routing logic)
        is_uncertain = self._detect_uncertainty(mentee_goal)
        if is_uncertain:
            # Look for HR, Coaching, or highly senior mentors
            if any(w in mentor_dept.lower() for w in ["ik", "hr", "insan kaynakları", "koçluk", "talent"]):
                score += 5.0  # Massive boost for HR/Coaching
            score += self.compute_mentor_quality_score(mentor) * 0.5  # High penalty avoidance
        else:
            # 2. Semantic Category Extraction (Sector + Sub-Sector Similarity)
            mentee_emb = self.model.encode(mentee_goal)
            mentor_text = f"{mentor_sector} {mentor_dept} {mentor_title}"
            mentor_emb = self.model.encode(mentor_text)
            
            sim = cosine_similarity([mentee_emb], [mentor_emb])[0][0]
            score += sim * 10.0  # Base similarity
            
            # 3. International Intent Hard Constraint
            if self._detect_international_intent(mentee_goal):
                mentor_loc = str(mentor.get("Guncel_Lokasyon", "")).lower()
                # If mentor is not in Turkey, massive boost
                if "türkiye" not in mentor_loc and "turkey" not in mentor_loc and mentor_loc != "":
                    score += 8.0

            # 4. Network & Expectation Match
            mentee_expect = str(mentee.get("Beklenti", "")).lower()
            mentor_topic = str(mentor.get("Destek_Alanlari", "")).lower()
            
            if "network" in mentee_expect and "network" in mentor_topic:
                score += 2.0
            if "teknik" in mentee_expect and "teknik" in mentor_topic:
                score += 2.0

        return round(score, 3)

    def match_batch(self, mentees_df, mentors_df):
        """
        Applies the hybrid logic across the full dataset and builds the cost matrix
        for the Hungarian Algorithm. Pre-computes embeddings for performance.
        """
        logging.info("Building Hybrid Cost Matrix...")
        num_mentees = len(mentees_df)
        num_mentors = len(mentors_df)
        
        # 1. Pre-compute embeddings to save thousands of redundant operations
        logging.info("Pre-computing sentence embeddings...")
        mentee_texts = [str(m.get("Kariyer_Hedefi", "")) for _, m in mentees_df.iterrows()]
        mentee_embeddings = self.model.encode(mentee_texts)
        
        mentor_texts = [
            f"{str(m.get('Guncel_Sektor', ''))} {str(m.get('Guncel_Departman', ''))} {str(m.get('Guncel_Unvan', ''))}" 
            for _, m in mentors_df.iterrows()
        ]
        mentor_embeddings = self.model.encode(mentor_texts)
        
        cost_matrix = np.zeros((num_mentees, num_mentors))

        for i, mentee in mentees_df.iterrows():
            logging.info(f"Processing Mentee {i+1}/{num_mentees}...")
            # Mentee pre-computations
            mentee_expect = str(mentee.get("Beklenti", "")).lower()
            mentee_goal = mentee_texts[i]
            mentee_emb = mentee_embeddings[i]
            
            is_uncertain = self._detect_uncertainty(mentee_goal)
            is_intl = self._detect_international_intent(mentee_goal)

            for j, mentor in mentors_df.iterrows():
                score = 0.0
                
                mentor_dept = str(mentor.get("Guncel_Departman", "")).lower()
                mentor_loc = str(mentor.get("Guncel_Lokasyon", "")).lower()
                mentor_topic = str(mentor.get("Destek_Alanlari", "")).lower()
                mentor_emb = mentor_embeddings[j]
                
                # 1. Uncertainty Handling
                if is_uncertain:
                    if any(w in mentor_dept for w in ["ik", "hr", "insan kaynakları", "koçluk", "talent"]):
                        score += 5.0
                    score += self.compute_mentor_quality_score(mentor) * 0.5
                else:
                    # 2. Semantic Similarity via pre-computed embeddings
                    sim = cosine_similarity([mentee_emb], [mentor_emb])[0][0]
                    score += sim * 10.0
                    
                    # 3. International Match
                    if is_intl and ("türkiye" not in mentor_loc and "turkey" not in mentor_loc and mentor_loc != ""):
                        score += 8.0

                    # 4. Network and Topic Match
                    if "network" in mentee_expect and "network" in mentor_topic:
                        score += 2.0
                    if "teknik" in mentee_expect and "teknik" in mentor_topic:
                        score += 2.0

                cost_matrix[i, j] = round(score, 3)

        logging.info("Cost Matrix built successfully.")
        return cost_matrix


if __name__ == "__main__":
    import os
    import glob
    from scipy.optimize import linear_sum_assignment

    logging.info("Initializing Hybrid Matcher v3...")
    matcher = HybridMatcherV3()
    
    # 1. Load Data
    raw_dir = r"E:\Programming\mentor_mentee\data\01_raw"
    search_pattern = os.path.join(raw_dir, "Mentor Mezun*.xlsx")
    files = glob.glob(search_pattern)
    
    if not files:
        logging.error("Could not find the raw Mentor Mentee Excel file in data/01_raw/")
        exit(1)
        
    input_file = files[0]
    logging.info(f"Loading data from: {input_file}")
    
    try:
        xf = pd.read_excel(input_file, sheet_name=None)
        mentee_df = xf['Mentee'].copy()
        mentor_df = xf['Mentor'].copy()
        
        # Drop completely null columns or rows if any
        mentee_df.dropna(how='all', inplace=True)
        mentor_df.dropna(how='all', inplace=True)
        
        logging.info(f"Loaded {len(mentee_df)} Mentees and {len(mentor_df)} Mentors.")
    except Exception as e:
        logging.error(f"Failed to read data: {e}")
        exit(1)

    # 2. Build Matrix
    cost_matrix = matcher.match_batch(mentee_df, mentor_df)
    
    # 3. Optimize (Maximize similarity -> Minimize negative similarity)
    logging.info("Running Hungarian Algorithm (Linear Sum Assignment)...")
    row_ind, col_ind = linear_sum_assignment(-cost_matrix)
    
    # 4. Generate Output
    logging.info("Building Output DataFrames...")
    results = []
    
    for r, c in zip(row_ind, col_ind):
        mentee = mentee_df.iloc[r]
        mentor = mentor_df.iloc[c]
        similarity_score = cost_matrix[r, c]
        
        results.append({
            "Mentee_Ad": mentee.get("Ad", "Bilinmiyor"),
            "Mentee_Soyad": mentee.get("Soyad", "Bilinmiyor"),
            "Mentee_Bolum": mentee.get("Okuduğu_Bölüm", mentee.get("Bolum", "")),
            "Mentee_Hedef": mentee.get("Kariyer_Hedefi", ""),
            "Mentor_Ad": mentor.get("Ad", "Bilinmiyor"),
            "Mentor_Soyad": mentor.get("Soyad", "Bilinmiyor"),
            "Mentor_Sirket": mentor.get("Guncel_Sirket", ""),
            "Mentor_Unvan": mentor.get("Guncel_Unvan", ""),
            "Mentor_Departman": mentor.get("Guncel_Departman", ""),
            "Similarity_Score": similarity_score,
            "Mentee_Index": r,
            "Mentor_Index": c
        })
        
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="Similarity_Score", ascending=False)
    
    # 5. Save Output
    out_dir = r"E:\Programming\mentor_mentee\data\04_output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "Mentor_Mentee_Optimal_Eslestirme_v3.xlsx")
    
    try:
        results_df.to_excel(out_path, index=False)
        logging.info(f"Successfully saved assignments to {out_path}.")
    except Exception as e:
        logging.error(f"Failed to save Excel file: {e}")
        
    logging.info("Pipeline Complete!")

