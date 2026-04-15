"""
tests/test_unit.py — Unit Tests for PlagiaGuard
Run with: pytest tests/test_unit.py -v

Covers:
  - Text preprocessing functions
  - Shingling / Jaccard similarity
  - TF-IDF cosine similarity
  - Full analyze() function
  - Flask API endpoints
  - File parser (TXT)
"""

import os
import sys
import json
import tempfile
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.analyzer import (
    preprocess,
    tokenize,
    get_shingles,
    jaccard_similarity,
    tfidf_similarity,
    split_sentences,
    find_matched_sentences,
    analyze,
    _risk_label,
)
from backend.parser import extract_text
from app import app as flask_app


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    with flask_app.test_client() as c:
        yield c


SAMPLE_TEXT_A = (
    "Machine learning is a subset of artificial intelligence. "
    "It enables computers to learn from data without explicit programming. "
    "Deep neural networks power modern AI systems. "
    "Natural language processing allows machines to understand text. "
    "These systems are applied across healthcare and finance."
)

SAMPLE_TEXT_B = (
    "Machine learning is a subset of artificial intelligence. "
    "It enables computers to learn from data without explicit programming. "
    "Deep neural networks power modern AI systems. "
    "Natural language processing allows machines to understand text. "
    "These systems are applied across healthcare and finance."
)

SAMPLE_TEXT_C = (
    "The water cycle describes how water moves through the environment. "
    "Evaporation turns liquid water into vapour. "
    "Clouds form when water vapour condenses. "
    "Precipitation returns water to the ground as rain or snow. "
    "Rivers carry water back to the ocean completing the cycle."
)


# ─────────────────────────────────────────────
# 1. Preprocessing Tests
# ─────────────────────────────────────────────

class TestPreprocessing:

    def test_preprocess_lowercases(self):
        result = preprocess("Hello World")
        assert result == result.lower()

    def test_preprocess_removes_punctuation(self):
        result = preprocess("Hello, World! How are you?")
        assert "," not in result
        assert "!" not in result
        assert "?" not in result

    def test_preprocess_collapses_whitespace(self):
        result = preprocess("hello   world")
        assert "  " not in result

    def test_tokenize_removes_stopwords(self):
        tokens = tokenize("the cat sat on the mat")
        assert "the" not in tokens
        assert "on" not in tokens

    def test_tokenize_returns_list(self):
        tokens = tokenize("artificial intelligence machine learning")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenize_filters_single_chars(self):
        tokens = tokenize("a b c hello world")
        for t in tokens:
            assert len(t) > 1


# ─────────────────────────────────────────────
# 2. Shingling Tests
# ─────────────────────────────────────────────

class TestShingling:

    def test_shingles_returns_set(self):
        shingles = get_shingles(SAMPLE_TEXT_A)
        assert isinstance(shingles, set)

    def test_shingles_identical_texts(self):
        s1 = get_shingles(SAMPLE_TEXT_A)
        s2 = get_shingles(SAMPLE_TEXT_A)
        assert s1 == s2

    def test_jaccard_identical(self):
        s = get_shingles(SAMPLE_TEXT_A)
        score = jaccard_similarity(s, s)
        assert score == 1.0

    def test_jaccard_disjoint(self):
        s1 = get_shingles(SAMPLE_TEXT_A)
        s2 = get_shingles(SAMPLE_TEXT_C)
        score = jaccard_similarity(s1, s2)
        assert score < 0.2

    def test_jaccard_empty_sets(self):
        score = jaccard_similarity(set(), set())
        assert score == 0.0

    def test_jaccard_range(self):
        s1 = get_shingles(SAMPLE_TEXT_A)
        s2 = get_shingles(SAMPLE_TEXT_C)
        score = jaccard_similarity(s1, s2)
        assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────
# 3. TF-IDF Similarity Tests
# ─────────────────────────────────────────────

class TestTFIDF:

    def test_identical_texts_score_near_one(self):
        score = tfidf_similarity(SAMPLE_TEXT_A, SAMPLE_TEXT_B)
        assert score > 0.95

    def test_different_texts_score_low(self):
        score = tfidf_similarity(SAMPLE_TEXT_A, SAMPLE_TEXT_C)
        assert score < 0.3

    def test_score_in_range(self):
        score = tfidf_similarity(SAMPLE_TEXT_A, SAMPLE_TEXT_C)
        assert 0.0 <= score <= 1.0

    def test_empty_text_returns_zero(self):
        score = tfidf_similarity("", SAMPLE_TEXT_A)
        assert score == 0.0


# ─────────────────────────────────────────────
# 4. Sentence Splitting Tests
# ─────────────────────────────────────────────

class TestSentenceSplitting:

    def test_splits_multiple_sentences(self):
        text = (
            "Artificial intelligence is transforming industries. "
            "Machine learning is a core branch of AI. "
            "Deep learning uses neural networks to solve problems."
        )
        sentences = split_sentences(text)
        assert len(sentences) >= 1

    def test_ignores_short_fragments(self):
        sentences = split_sentences("Hi. Hello. OK.")
        # All under 30 chars, should return empty or minimal
        for s in sentences:
            assert len(s) >= 30

    def test_returns_list(self):
        assert isinstance(split_sentences(SAMPLE_TEXT_A), list)


# ─────────────────────────────────────────────
# 5. Full Analyze() Tests
# ─────────────────────────────────────────────

class TestAnalyze:

    def test_identical_texts_high_score(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_B])
        assert result["plagiarism_percentage"] > 70

    def test_different_texts_low_score(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_C])
        assert result["plagiarism_percentage"] < 40

    def test_result_has_required_keys(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_C])
        required = [
            "plagiarism_percentage",
            "original_percentage",
            "flagged_sentences",
            "total_sentences_analyzed",
            "flagged_sentence_count",
            "per_reference_breakdown",
            "risk_level",
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_percentages_sum_to_100(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_C])
        total = result["plagiarism_percentage"] + result["original_percentage"]
        assert abs(total - 100.0) < 0.5

    def test_empty_source_returns_error(self):
        result = analyze("", [SAMPLE_TEXT_A])
        assert "error" in result

    def test_no_references_returns_error(self):
        result = analyze(SAMPLE_TEXT_A, [])
        assert "error" in result

    def test_multiple_references(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_B, SAMPLE_TEXT_C])
        assert "plagiarism_percentage" in result
        assert len(result["per_reference_breakdown"]) == 2

    def test_score_is_between_0_and_100(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_B])
        assert 0 <= result["plagiarism_percentage"] <= 100

    def test_flagged_sentences_are_list(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_B])
        assert isinstance(result["flagged_sentences"], list)

    def test_breakdown_has_correct_fields(self):
        result = analyze(SAMPLE_TEXT_A, [SAMPLE_TEXT_C])
        bd = result["per_reference_breakdown"][0]
        assert "cosine_similarity" in bd
        assert "jaccard_similarity" in bd
        assert "blended_score" in bd


# ─────────────────────────────────────────────
# 6. Risk Label Tests
# ─────────────────────────────────────────────

class TestRiskLabel:

    def test_low_risk(self):
        assert _risk_label(10) == "Low Risk"

    def test_moderate_risk(self):
        assert _risk_label(25) == "Moderate Risk"

    def test_high_risk(self):
        assert _risk_label(55) == "High Risk"

    def test_critical_risk(self):
        assert _risk_label(80) == "Critical"


# ─────────────────────────────────────────────
# 7. Parser Tests
# ─────────────────────────────────────────────

class TestParser:

    def test_extract_txt(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w",
                                         delete=False, encoding="utf-8") as f:
            f.write("Hello world this is a test document.")
            path = f.name
        try:
            text = extract_text(path)
            assert "Hello world" in text
        finally:
            os.unlink(path)

    def test_unsupported_format_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            path = f.name
        try:
            with pytest.raises(ValueError):
                extract_text(path)
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────
# 8. Flask API Tests
# ─────────────────────────────────────────────

class TestFlaskRoutes:

    def test_index_returns_200(self, client):
        res = client.get("/")
        assert res.status_code == 200

    def test_analyze_no_files_returns_400(self, client):
        res = client.post("/analyze")
        assert res.status_code == 400

    def test_analyze_missing_reference_returns_400(self, client):
        data = {
            "source_file": (
                tempfile.SpooledTemporaryFile(), "source.txt"
            )
        }
        # Send source but no reference
        src = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        src.write(b"Some source text for testing purposes here.")
        src.flush()
        src.seek(0)

        res = client.post(
            "/analyze",
            data={"source_file": (src, "source.txt")},
            content_type="multipart/form-data"
        )
        assert res.status_code == 400
        src.close()
        os.unlink(src.name)

    def test_analyze_invalid_extension_returns_400(self, client):
        src = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
        src.write(b"some bytes")
        src.flush()
        src.seek(0)

        ref = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
        ref.write(b"other bytes")
        ref.flush()
        ref.seek(0)

        res = client.post(
            "/analyze",
            data={
                "source_file": (src, "malware.exe"),
                "reference_files": (ref, "ref.exe"),
            },
            content_type="multipart/form-data"
        )
        assert res.status_code == 400
        src.close(); os.unlink(src.name)
        ref.close(); os.unlink(ref.name)

    def test_analyze_valid_txt_files(self, client):
        src_text = (
            b"Machine learning is a subset of artificial intelligence. "
            b"It enables computers to learn from data without explicit programming. "
            b"Deep neural networks power modern AI systems today."
        )
        ref_text = (
            b"Machine learning is a subset of artificial intelligence. "
            b"It enables computers to learn from data without explicit programming. "
            b"Deep neural networks power modern AI systems today."
        )

        src = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        src.write(src_text); src.flush(); src.seek(0)

        ref = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        ref.write(ref_text); ref.flush(); ref.seek(0)

        res = client.post(
            "/analyze",
            data={
                "source_file": (src, "source.txt"),
                "reference_files": (ref, "reference.txt"),
            },
            content_type="multipart/form-data"
        )
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "plagiarism_percentage" in data
        assert data["plagiarism_percentage"] > 50

        src.close(); os.unlink(src.name)
        ref.close(); os.unlink(ref.name)

    def test_download_nonexistent_returns_404(self, client):
        res = client.get("/download/nonexistent_file_xyz.pdf")
        assert res.status_code == 404


# ─────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
