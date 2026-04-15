"""
analyzer.py — Core Plagiarism Detection Engine

Uses multiple techniques for robust plagiarism detection:
1. TF-IDF Cosine Similarity     — structural/semantic similarity between documents
2. Shingling (N-gram fingerprinting) — exact/near-exact phrase matching
3. Sentence-level comparison    — highlights specific plagiarized passages

This is intentionally multi-layered to reflect a real plagiarism checker.
"""

import re
import string
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ─────────────────────────────────────────────
# Text Preprocessing
# ─────────────────────────────────────────────

STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "with", "this", "that", "are",
    "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "shall", "can", "from", "by", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "so", "yet",
    "up", "about", "than", "also", "its"
}


def preprocess(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Split into words, filter stopwords and single-chars."""
    words = preprocess(text).split()
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def split_sentences(text: str) -> list[str]:
    """Simple rule-based sentence splitter."""
    # Split on . ! ? followed by space and capital, or newlines
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?<=\n)\n+', text.strip())
    return [s.strip() for s in raw if len(s.strip()) > 30]


# ─────────────────────────────────────────────
# Shingling: N-gram fingerprinting
# ─────────────────────────────────────────────

def get_shingles(text: str, k: int = 5) -> set:
    """
    Create a set of k-word shingles from the text.
    Shingles capture phrases, making them useful for detecting
    near-exact copying regardless of word order variations.
    """
    words = tokenize(text)
    if len(words) < k:
        return set(words)
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two shingle sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


# ─────────────────────────────────────────────
# TF-IDF Cosine Similarity
# ─────────────────────────────────────────────

def tfidf_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity using TF-IDF vectors.
    Captures vocabulary and topic overlap even with paraphrasing.
    """
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),      # unigrams + bigrams
            min_df=1,
            stop_words=list(STOPWORDS)
        )
        tfidf_matrix = vectorizer.fit_transform([
            preprocess(text_a),
            preprocess(text_b)
        ])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(score)
    except Exception:
        return 0.0


# ─────────────────────────────────────────────
# Sentence-Level Matching
# ─────────────────────────────────────────────

def find_matched_sentences(
    source_text: str,
    reference_text: str,
    similarity_threshold: float = 0.65
) -> list[dict]:
    """
    Compare each sentence in source against all sentences in reference.
    Returns sentences in source that are plagiarized, with match info.

    Args:
        source_text: The document being analyzed.
        reference_text: The reference document to compare against.
        similarity_threshold: Minimum cosine similarity to flag as plagiarism.

    Returns:
        List of dicts: {sentence, similarity, matched_reference_sentence}
    """
    source_sentences = split_sentences(source_text)
    ref_sentences = split_sentences(reference_text)

    if not source_sentences or not ref_sentences:
        return []

    matched = []

    for src_sent in source_sentences:
        best_score = 0.0
        best_match = ""

        for ref_sent in ref_sentences:
            score = tfidf_similarity(src_sent, ref_sent)
            if score > best_score:
                best_score = score
                best_match = ref_sent

        if best_score >= similarity_threshold:
            matched.append({
                "sentence": src_sent,
                "similarity": round(best_score * 100, 1),
                "matched_with": best_match
            })

    return matched


# ─────────────────────────────────────────────
# Main Analysis Function
# ─────────────────────────────────────────────

def analyze(source_text: str, reference_texts: list[str]) -> dict:
    """
    Full plagiarism analysis of source against a list of references.

    Combines:
    - TF-IDF cosine similarity (overall structural match)
    - Jaccard shingling (phrase-level fingerprinting)
    - Sentence-level matching (highlights specific passages)

    Returns a structured result dict for the frontend.
    """
    if not source_text.strip():
        return {"error": "Source document is empty."}

    if not reference_texts:
        return {"error": "No reference documents provided."}

    results_per_reference = []
    all_flagged_sentences = []
    max_overall_score = 0.0

    for i, ref_text in enumerate(reference_texts):
        if not ref_text.strip():
            continue

        # 1. TF-IDF similarity
        cosine_score = tfidf_similarity(source_text, ref_text)

        # 2. Shingle (Jaccard) similarity
        src_shingles = get_shingles(source_text)
        ref_shingles = get_shingles(ref_text)
        jaccard_score = jaccard_similarity(src_shingles, ref_shingles)

        # 3. Weighted blend: TF-IDF is more reliable for paraphrasing
        blended_score = (cosine_score * 0.6) + (jaccard_score * 0.4)

        # 4. Sentence-level matches
        flagged = find_matched_sentences(source_text, ref_text)

        results_per_reference.append({
            "reference_index": i,
            "cosine_similarity": round(cosine_score * 100, 2),
            "jaccard_similarity": round(jaccard_score * 100, 2),
            "blended_score": round(blended_score * 100, 2),
            "flagged_sentence_count": len(flagged)
        })

        all_flagged_sentences.extend(flagged)
        if blended_score > max_overall_score:
            max_overall_score = blended_score

    # Deduplicate flagged sentences by sentence text
    seen = set()
    unique_flagged = []
    for item in sorted(all_flagged_sentences, key=lambda x: -x["similarity"]):
        if item["sentence"] not in seen:
            seen.add(item["sentence"])
            unique_flagged.append(item)

    # Calculate overall plagiarism %
    # Use both max match and proportion of flagged sentences
    source_sentences = split_sentences(source_text)
    total_sentences = max(len(source_sentences), 1)
    flagged_ratio = len(unique_flagged) / total_sentences

    # Final score: weight blend of max match and sentence-level ratio
    final_score = (max_overall_score * 0.55) + (flagged_ratio * 0.45)
    final_score = min(final_score * 100, 100.0)

    return {
        "plagiarism_percentage": round(final_score, 1),
        "original_percentage": round(100 - final_score, 1),
        "flagged_sentences": unique_flagged[:30],        # top 30 matches
        "total_sentences_analyzed": total_sentences,
        "flagged_sentence_count": len(unique_flagged),
        "per_reference_breakdown": results_per_reference,
        "risk_level": _risk_label(final_score)
    }


def _risk_label(score: float) -> str:
    """Map score to human-readable risk category."""
    if score < 15:
        return "Low Risk"
    elif score < 40:
        return "Moderate Risk"
    elif score < 70:
        return "High Risk"
    else:
        return "Critical"
