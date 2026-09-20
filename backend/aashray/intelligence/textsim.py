from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_CORPUS = [
    "landslide rocks debris slope hillside failed",
    "road blocked debris cannot pass valley",
    "vehicle trapped under debris after slide",
    "photo of debris on blocked road after landslide",
]


def text_similarity(a: str, b: str) -> float:
    """TF-IDF cosine. Embeddings may replace this if an API is configured later."""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    try:
        vec = TfidfVectorizer(min_df=1)
        mat = vec.fit_transform(_CORPUS + [a, b])
        sim = cosine_similarity(mat[-2], mat[-1])[0][0]
        return float(max(0.0, min(1.0, sim)))
    except Exception:
        wa, wb = set(a.lower().split()), set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / len(wa | wb)
