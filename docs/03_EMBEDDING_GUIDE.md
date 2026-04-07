# 🚀 TEXT EMBEDDING 384 - KAPSAMLI REHBER

> **Tarih**: Apr 2026 | **Model Family**: Nomic, Sentence-Transformers | **Boyut**: 384-dim

---

## 1️⃣ EMBEDDING 384 NEDİR?

### 📌 Tanım
**Text Embedding**, bir yazı parçasını **384-boyutlu vektöre** dönüştüren makine öğrenmesi işlemi.

```
"Yazılım geliştirme ve Python programming"
              ↓ (embedding modeli)
[0.123, -0.456, 0.789, ..., 0.234]  ← 384 sayısı
```

### 🎯 Neden 384 Boyut?

| Boyut | Kullanım | Avantaj | Dezavantaj |
|-------|----------|---------|-----------|
| **64** | Ultra-hafif | Hızlı | Düşük semantik |
| **128** | Lightweight | Dengeli | Sınırlı anlayış |
| **256** | Middle | İyi dengesi | Orta hafıza |
| **384** ⭐ | **Golden** | Detaylı + hızlı | - |
| **768** | BERT-large | Çok detaylı | Yavaş + hafıza |
| **1024+** | XL Models | Maximum | Çok ağır |

**384 seçimi**: 
- ✅ Dönüştürüler (Transformers) için standart "middle" boyut
- ✅ `all-MiniLM-L6-v2` (Sentence-Transformers) çıktısı = 384
- ✅ `nomic-embed-text-v1` = 768 (ama 384 projection var)
- ✅ Hafıza-hız dengesi optimal
- ✅ Bilgisayar havuzlarında kolayca depolanır

---

## 2️⃣ EMBEDDING MODELLERI (384-dim örnekler)

### 🥇 Top Models (Açık Kaynak)

#### **1. all-MiniLM-L6-v2** (Tavsiye ✨)
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["Yazılım", "Program"])  # Shape: (2, 384)
```
- **Boyut**: 384
- **Hız**: Çok hızlı (~50 docs/sec GPU'lu)
- **Kalite**: İyi (özellikle semantik benzerlik)
- **Geliş**: 2021, MiniLM mimarisi
- **Kullanım**: Semantic search, clustering, recommendation (BEST)

#### **2. all-mpnet-base-v2**
```python
model = SentenceTransformer('all-mpnet-base-v2')
```
- **Boyut**: 768 (adapte edilebilir → 384)
- **Hız**: Orta
- **Kalite**: Çok yüksek (daha detaylı)
- **Geliş**: 2021, MPNet mimarisi
- **Kullanım**: Yüksek kalite gerekli senaryolar

#### **3. nomic-embed-text-v1** (Yeni)
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('nomic-embed-text-v1.5')
```
- **Boyut**: 768 (→ 384 ile compatible)
- **Kalite**: State-of-art
- **Eğitim**: Çok büyük veri (~300B token)
- **Kullanım**: Modern, açık-kaynak, Matryoshka embeddings

#### **4. İngilizce + Türkçe (Cross-lingual)**
```python
model = SentenceTransformer('multilingual-e5-base')  # 768-dim
# or
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # 384-dim ⭐
```
- **Dil Desteği**: 100+ dil (Türkçe dahil ✅)
- **Boyut**: 384
- **Kalite**: Multilingual'de iyi
- **Açıklama**: "paraphrase-multilingual" = parafraza & benzerlik

---

## 3️⃣ EMBEDDING NASIL ÇALIŞIR? (Teknik)

### 🧠 İç Yapı

```
METIN: "Yazılım mühendisliği"
   ↓
[Tokenlection] → ["Yazılım", "mühen", "dis", "liği"]
   ↓
[Transformer Layers] → WordPiece embeddings × attention
   ↓
[Similarity-Tuned Layer] → Kontrastif öğrenme (contra loss)
   ↓
[Output] → Normalized 384-dim vector
   ↓
EMBEDDING: [0.123, -0.456, 0.789, ..., 0.234]
```

### 📐 Similarity Hesaplama

```
Embedding_A = [0.1, 0.2, ..., 0.384]
Embedding_B = [0.15, 0.19, ..., 0.38]
                        ↓
                Cosine Similarity
                        ↓
        similarity = dot(A, B) / (||A|| × ||B||)
                        ↓
                    [0.0 - 1.0]

0.95 = Çok yüksek benzerlik (aynı anlam)
0.71 = Orta benzerlik (ilgili kavramlar)
0.50 = Düşük benzerlik
0.0  = Hiçbir ilişki
```

### 🔑 Önemli Özellik: Normalization

```python
# Cosine similarity için vektörler normalize edilmelidir
# model.encode() bunu otomatik yapar:

embeddings = model.encode(texts, normalize_embeddings=True)
# Her vector: ||v|| = 1.0

# Sonra dot product doğrudan similarity = cosine similarity
```

---

## 4️⃣ EMBEDDING'I MENTOR-MENTEE PROJESİNE UYGULAMA

### 🎯 Stratejik Kullanım

**Mevcut TF-IDF yaklaşımı**:
```
Word TF-IDF + Char N-gram + Token Overlap
  ↓
  Keyword-based (yüzeysel metin analizi)
  ↓
  Typo'lara zayıf, semantik anlamına güvensiz
```

**Embedding tabanlı yaklaşım**:
```
SentenceTransformer (384-dim)
  ↓
  Semantic (derin anlam analizi)
  ↓
  Typo'lara dayanıklı, "şirket" vs "organizasyon" eş sayar
```

### 💡 Mentorluk Konağında Embedding Avantajları

#### ✅ Avantaj 1: Semantik Anlama
```
TF-IDF: "yazılım geliştirme" ≠ "program yazımı"
        (farklı kelimeler = 0 benzerlik)

Embedding: "yazılım geliştirme" ≈ "program yazımı"
           (aynı anlam = 0.92 benzerlik) ✅
```

#### ✅ Avantaj 2: Zıt Anlamlar Yakalama
```
"arzu", "isteme", "dileme"           → pozitif anlam
"istememe", "reddetme", "olumsuz"    → negatif anlam

Embedding otomatik zıtlığı algılar:
sim("arzu", "isteme") = 0.89  (benzer)
sim("arzu", "istememe") = -0.12 (zıt, negatif similarity)
```

#### ✅ Avantaj 3: Alt Kategoriler (Hierarchy)
```
"Yazılım" (üst kategori)
   ├─ "Python" (alt)
   ├─ "JavaScript" (alt)
   └─ "C++" (alt)

Embedding clustering:
  - "Python" × "Yazılım" ≈ 0.75 (ilgili)
  - "Python" × "Mutluluk" ≈ 0.15 (ilişkisiz)
```

#### ✅ Avantaj 4: Anlamsal Mesafe
```
"Sektör" ← → "İş Alanı" = çok yakın (0.88)
"Sektör" ← → "Coğrafya" = uzak (0.22)

Hierarchical clustering:
1. Manto kariyer alanına göre grupla
2. Mentee kariyer hedefine benzer grup bul
3. Grup içinde en iyi eşleş
```

---

## 5️⃣ MENTOR-MENTEE İÇİN EMBEDDING TASARIMI

### 📐 Yeni Score Matrix Formülü

```
MENGINE APPROACHED (5 kriter):

Sektör (35pt):
  TF-IDF: sim_word + sim_char + sim_token
  YENI: + embedding_cosine(mentee_career, mento_sector)
        ↑ 0.0-1.0 scaled back to 35pt

Veya FULL EMBEDDING:

hybrid_sim = α × tfidf_similarity + (1-α) × embedding_similarity
             α = 0.3 (TF-IDF), 1-α = 0.7 (embedding)

SONUÇ: Daha insanmış anlama kapabilirlik
```

### 🏗️ Yeni Alt Modül: "embedding_module"

```
📁 mentor_mentee/
├── data/
│   ├── mentee_profiles.xlsx
│   └── mento_profiles.xlsx
├── embedding_similarity/                    ← YENİ
│   ├── embeddings_cache.pkl                 (hızlandırma)
│   ├── similarity_matrix_384.npy             (308×225)
│   ├── embedding_model.py                    (384-dim model)
│   ├── similarity_analyzer.py                (sem. analiz)
│   └── 01_EMBEDDING_GUIDE.md                 (doküm)
├── scripts/
│   ├── matcher_hungarian.py                 (TF-IDF)
│   ├── matcher_embedding.py                  (YENİ - Embedding)
│   └── matcher_hybrid.py                     (YENİ - Hybrid)
└── reports/
    ├── mentor_mentee_analysis.md             (teknik rapor)
    ├── embedding_analysis.md                 (yeni alt mod)
    └── comparison_tfidf_vs_embedding.md      (karşılaştırma)
```

---

## 6️⃣ EMBEDDING SIMILARITY İMPLEMENTASYONU

### 📝 Python Kodu (Temel)

```python
# 1. Model loading
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Mentee & Mento texts
mentee_careers = [
    "Yazılım geliştirme, Python programlama",
    "Veri analizi, İstatistik",
    # ... 308 satır
]

mento_sectors = [
    "Senior yazılım mühendisi, Python uzmanı",
    "Veri bilimci, makine öğrenmesi",
    # ... 225 satır
]

# 3. Embed
mentee_embeddings = model.encode(mentee_careers, normalize_embeddings=True)
mento_embeddings = model.encode(mento_sectors, normalize_embeddings=True)
# Shapes: (308, 384) ve (225, 384)

# 4. Similarity matrix
similarity_matrix = cosine_similarity(mentee_embeddings, mento_embeddings)
# Shape: (308, 225), values: [0.0 - 1.0]

# 5. Puan matrisi (35pt için)
score_sector_embedding = similarity_matrix * 35
```

### 🔍 Semantic Nuance Detection (İleri)

```python
# Zıt anlamları bul
opposite_terms = {
    "olumsuz": ["pozitif", "yapıcı"],
    "eleştiri": ["iltifat", "takdir"],
    "stres": ["rahatlatıcı", "yatıştırıcı"],
}

def detect_semantic_opposition(text_a, text_b, model, threshold=0.3):
    """Zıt anlam varsa uyarı ver"""
    embedding_a = model.encode(text_a, normalize_embeddings=True)
    embedding_b = model.encode(text_b, normalize_embeddings=True)
    
    sim = np.dot(embedding_a, embedding_b)
    
    if sim < threshold:  # Çok düşük similarty = potensiyel zıtlık
        return f"WARNING: Low semantic match (sim={sim:.2f})"
    return None
```

### 📊 Hierarchical Clustering (Kategoriler)

```python
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

# Mento sektörlerini cluster et
distance_matrix = pdist(mento_embeddings, metric='cosine')
linkage_matrix = linkage(distance_matrix, method='ward')

# Cluster 1: Tech (yazılım, veri, AI)
# Cluster 2: Finance (muhasebe, yatırım)
# Cluster 3: HR (insan kaynakları, kariyer)
# ...

# Mentee'nin hedefini hangi cluster'a ait?
mentee_goal = "Yazılım mimarı olmak istiyorum"
mentee_goal_emb = model.encode(mentee_goal)

# En yakın cluster'daki mentolara bak (pre-filter)
```

---

## 7️⃣ EMBEDDING + TF-IDF HYBRID YAKLAŞIMI

### 🔄 Best of Both Worlds

```
TF-İDI-Avantajlar:
✅ Keyword matching (exact terms)
✅ Hızlı
✅ Deterministic
⚠️  Semantic zayıf (typo/synonym blind)

Embedding Avantajları:
✅ Semantic anlama (deep)
✅ Synonym/antonym
✅ Context-aware
⚠️  Yavaş (model forward pass)

HYBRID (Önerilen):

sim_final = 0.4 × sim_tfidf + 0.6 × sim_embedding

30 mentee'yi 100 mento aday → 30 finalist bulunur
20 finalist → TF-IDF hızlı filtrele (fast pre-filter)
10 finalist → Embedding detailed analiz (slow, but best)
```

### 📦 Hibrit Formülü (Mento-mentee için)

```python
# Sektör/Kariyer (35pt)
sim_sector_tfidf = _word_tfidf(...) + _char_tfidf(...) + token_overlap(...)
sim_sector_embedding = cosine_similarity(...)

sim_sector_hybrid = 0.3 * sim_sector_tfidf + 0.7 * sim_sector_embedding
score_sector = sim_sector_hybrid * 35

# (Benzer bölüm, ilgi, destek için de aynı)

# FINAL PUAN (Hybrid)
final_score = (
    (w_sektör/5) * score_sector_hybrid * 35 +
    (w_bölüm/5) * score_bölüm_hybrid * 30 +
    ... (diğer kriterler benzeri)
)
```

---

## 8️⃣ EMBEDDING CACHE & OPTIMIZASYON

### ⚡ Hızlandırma Stratejileri

```python
# 1. CACHE: Một kez embed → dosyaya kaydet
import pickle

embeddings_cache = {
    'mentee_embeddings': mentee_embeddings,  # (308, 384)
    'mento_embeddings': mento_embeddings,    # (225, 384)
    'model_name': 'all-MiniLM-L6-v2',
    'timestamp': datetime.now(),
}

with open('embedding_cache.pkl', 'wb') as f:
    pickle.dump(embeddings_cache, f)

# Tekrar çalıştırmada load edin:
with open('embedding_cache.pkl', 'rb') as f:
    cached = pickle.load(f)
    mentee_embeddings = cached['mentee_embeddings']  # 0 sn! ✨
```

### 📊 Benchmark

```
ZAMAN KARŞILAŞTIRMASI:

TF-IDF (5 kriter):
  _word_tfidf():      3 sn  (vectorizer)
  _char_tfidf():      2 sn  (vectorizer)
  _token_overlap():   1 sn  (döngü)
  City:               0.1 sn
  TOPLAM:             ~6 sn ✅ Hızlı

Embedding (384-dim):
  Model load:         2 sn  (ilk kez)
  308 mentee encode:  5 sn  (GPU'suz)
  225 mento encode:   3 sn
  Cosine similarity:  0.1 sn
  TOPLAM:             ~10 sn (ilk kez), 0.1 sn (cache)

Hybrid (TF-IDF + Embedding):
  ~16 sn (ilk kez, cache'siz)
  ~6 sn (cache'li) ← KULLAN!
```

### 🎯 GPU Hızlandırma

```python
# GPU varsa otomatik kullan:
model = SentenceTransformer('all-MiniLM-L6-v2')
model.to('cuda')  # GPU'ya taşı

# Encode GPU'da:
embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    device='cuda'  # GPU kullan
)
# Hız: 50 docs/sec (GPU), 5-10 docs/sec (CPU)
```

---

## 9️⃣ ANLAMSAL NÜANSLARı YAKALAMASI

### 🎨 Zıt Anlamlar

```
Embedding Space'de Örnek:

        NEGATIF
           ↑
    ELEŞTIRI  |  İSTEMEME
    "kötü"    |  "olumsuz"
      (-0.8)  |  (-0.7)
    ────────┼────────  SEM. EKSEN
    "iyi"   |  "olumlu"
(+0.8)      |  (+0.7)
    İYİLEŞTİRME | POZİTİF
           ↓
        POZİTİF

Mentorluk örneği:
  Mentee: "Stresli, sorun çözmek istiyorum"
  → emb = negatif-taraflı
  
  Mento: "Yatıştırıcı, dinleyici, problem solver"
  → emb = pozitif-taraflı
  
  Cosine(mentee, mento) = DÜŞÜK (çıkar!)
  ⚠️  Bu mentee-mento çifti UYUMLU (terapist-hasta miş gibi)
  
  → Negatif-pozitif matching = özel kural ekle
```

### 📚 Alt Kategori Mapping

```
YAZILIM (üst)
├─ Backend (C, Python, Java)
│  └─ API Design, Database
├─ Frontend (JavaScript, React)
│  └─ UI/UX, CSS
└─ DevOps (Docker, Kubernetes)
   └─ Infrastructure

Embedding clustering:
1. Tüm mentee + mento embedding'leri al
2. K-means cluster: k=5 (tech subcategories)
3. Mentee'nin hedefini en yakın cluster'a map et
4. O cluster'daki mentoları prefer et

KOD:
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=5, random_state=42)
mento_clusters = kmeans.fit_predict(mento_embeddings)

mentee_goal_emb = model.encode(mentee_goal)
mentee_cluster = kmeans.predict([mentee_goal_emb])[0]

# Aynı cluster'daki mentorları filtrele
candidate_mentos = np.where(mento_clusters == mentee_cluster)[0]
```

### 🔗 Bağlamsal İlişkiler

```
"Yazılım" → "Bilgisayar" → "Teknoloji" → "İş"
  0.92       0.85           0.72        0.45

Embedding bu hiyerarşiyi otomatik topramlı bulur!

Uygulamada:
  Mentee: "Yazılım dalı"
  
  Rank-1: "Yazılım mimarı" (0.91) - PERFEKt
  Rank-2: "Yazılım test" (0.88) - İLGİLİ
  Rank-3: "Veri analisti" (0.72) - UZAK AMA İLGİLİ
  Rank-4: "İnsan Kaynakları" (0.25) - FARKI
```

---

## 🔟 FULL İMPLEMENTASYON ÖRNEĞI

```python
# matcher_embedding.py - Embedding-tabanlı eşleştirme

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class EmbeddingMatcher:
    def __init__(self, model_name='all-MiniLM-L6-v2', cache_path=None):
        """
        Args:
            model_name: HuggingFace model ID (384-dim)
            cache_path: Opsiyonel - embedding cache dosyası
        """
        self.model = SentenceTransformer(model_name)
        self.cache_path = cache_path
        self.mentee_embs = None
        self.mento_embs = None
    
    def encode_mentees_mentos(self, mentee_texts, mento_texts):
        """Embedding hesapla (veya cache'den yükle)"""
        
        # Cache try
        if self.cache_path:
            try:
                cache = np.load(self.cache_path)
                self.mentee_embs = cache['mentee_embs']
                self.mento_embs = cache['mento_embs']
                print(f"Cache yüklendi: {self.cache_path}")
                return
            except:
                pass
        
        # Encode
        print("Embedding hesaplanıyor...")
        self.mentee_embs = self.model.encode(
            mentee_texts, 
            normalize_embeddings=True,
            show_progress_bar=True
        )
        self.mento_embs = self.model.encode(
            mento_texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        
        # Save cache
        if self.cache_path:
            np.savez(self.cache_path, 
                     mentee_embs=self.mentee_embs,
                     mento_embs=self.mento_embs)
            print(f"Cache kaydedildi: {self.cache_path}")
    
    def compute_similarity_matrix(self):
        """Cosine similarity matrix"""
        return cosine_similarity(self.mentee_embs, self.mento_embs)
    
    def get_top_matches(self, mentee_idx, k=5):
        """Mentee'nin top k mentosu"""
        sim_matrix = self.compute_similarity_matrix()
        scores = sim_matrix[mentee_idx]
        top_k_idx = np.argsort(-scores)[:k]
        top_k_scores = scores[top_k_idx]
        return top_k_idx, top_k_scores

# KULLANIM
matcher = EmbeddingMatcher(cache_path='embeddings_cache.npz')
matcher.encode_mentees_mentos(mentee_careers, mento_sectors)

# Mentee 0'ın top 5 mentosu:
top_mentos, top_scores = matcher.get_top_matches(mentee_idx=0, k=5)
for rank, (idx, score) in enumerate(zip(top_mentos, top_scores), 1):
    print(f"{rank}. Mento-{idx}: {score:.3f}")
```

---

## 1️⃣1️⃣ ÖZETİ

### ✨ Embedding 384 Nedir?

**384-boyutlu vektör**, yazının derin semantik anlamını temsil eden sayı dizisi. TF-IDF'den çok daha güçlü anlama kapabilirliği.

### 🎯 Mentor-Mentee İçin Neden?

1. **Anlamı yakalar** (typo-proof): "yazılım" = "program"
2. **Zıt anlamları algılar**: "stres" vs "rahatlatıcı"
3. **Kategorize eder**: Alt kategoriler, hiyerarşi
4. **Bağlamsal ilişki**: "Yazılım" → "Bilgisayar" → vb

### 💻 Nasıl Uygulanır?

```
1. Model: SentenceTransformer('all-MiniLM-L6-v2')
2. Encode all texts → (N, 384) matris
3. Cosine similarity → (N, M) benzerlik
4. Hybrid: 0.3×TF-IDF + 0.7×Embedding
5. Cache: Hızlandırma için embedding'i kaydet
```

### 📊 Performans

- **Hız**: 10 sn (ilk), 0.1 sn (cache)
- **Kalite**: Semantic ✅ (TF-IDF >> Embedding)
- **Boyut**: 384-dim (512MB für 308×225)

---

**END OF EMBEDDING GUIDE**

Sonraki dosyalar: `02_EMBEDDING_IMPLEMENTATION.py`, `03_SEMANTIC_ANALYSIS.md`

