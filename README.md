# PlagiaGuard — Academic Plagiarism Analyser

A full-stack plagiarism detection web application built with Flask and a custom multi-algorithm detection engine. Designed as a college-level project demonstrating real-world NLP techniques.

---

## Features

- **Multi-format upload** — PDF, DOCX, and TXT document support
- **Three-algorithm detection engine:**
  - TF-IDF Cosine Similarity (paraphrase detection)
  - Jaccard Shingling / N-gram fingerprinting (exact phrase matching)
  - Sentence-level TF-IDF comparison (highlights specific passages)
- **Blended scoring** — Weighted combination for calibrated final percentage
- **Downloadable PDF report** — Professional report with full breakdown
- **Modern dark UI** — Drag-and-drop, animated score ring, highlighted passages

---

## Project Structure

```
plagiarism-analyser/
├── app.py                        # Flask entry point & routes
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── parser.py                 # PDF/DOCX/TXT text extraction
│   ├── analyzer.py               # Core plagiarism engine
│   └── report_generator.py       # PDF report generation (ReportLab)
├── frontend/
│   ├── templates/
│   │   └── index.html            # Main UI template
│   └── static/
│       ├── css/style.css
│       └── js/main.js
├── uploads/                      # Temp storage (auto-cleaned)
└── reports/                      # Generated PDF reports
```

---

## Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python 3.11+, Flask 3   |
| NLP       | scikit-learn (TF-IDF)   |
| PDF Parse | PyMuPDF (fitz)          |
| DOCX      | python-docx             |
| Reports   | ReportLab               |
| Frontend  | Vanilla JS + CSS        |
| Fonts     | Google Fonts (Syne, DM Mono, Instrument Serif) |

---

## Setup & Run

### 1. Clone / download the project

```bash
cd plagiarism-analyser
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python app.py
```

The app will be available at **http://localhost:5000**

---

## How the Detection Engine Works

### Step 1 — Text Extraction
Depending on the file type, the `parser.py` module uses:
- **PyMuPDF** for PDFs (page-by-page extraction)
- **python-docx** for DOCX (paragraph iteration)
- Built-in file reading for TXT files

### Step 2 — TF-IDF Cosine Similarity
Both documents are converted into TF-IDF term vectors using scikit-learn's `TfidfVectorizer` (unigram + bigram). The cosine of the angle between these vectors gives a similarity score robust to paraphrasing.

### Step 3 — Jaccard Shingling
The preprocessed text is split into overlapping 5-word "shingles" (phrases). The Jaccard coefficient between the two shingle sets measures exact/near-exact phrase overlap. This technique is similar to what tools like Turnitin use internally.

### Step 4 — Sentence-Level Matching
Each sentence from the source is compared against every sentence in each reference using TF-IDF cosine similarity. Sentences scoring ≥ 65% are flagged and returned for highlighting in the UI.

### Step 5 — Blended Final Score
The final plagiarism percentage combines:
- `55%` weight on the maximum blended match score (TF-IDF × 60% + Jaccard × 40%)
- `45%` weight on the proportion of flagged sentences

This prevents both false inflation (a single matching paragraph) and underreporting.

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET`  | `/` | Serve the UI |
| `POST` | `/analyze` | Run plagiarism analysis |
| `GET`  | `/download/<filename>` | Download PDF report |

### POST /analyze

**Request:** `multipart/form-data`
- `source_file` — The document to check (required)
- `reference_files` — One or more reference files (required, max 5)

**Response JSON:**
```json
{
  "plagiarism_percentage": 34.2,
  "original_percentage": 65.8,
  "risk_level": "Moderate Risk",
  "flagged_sentences": [
    {
      "sentence": "...",
      "similarity": 78.4,
      "matched_with": "..."
    }
  ],
  "total_sentences_analyzed": 42,
  "flagged_sentence_count": 8,
  "per_reference_breakdown": [...],
  "report_filename": "PlagiarismReport_20241215_143022.pdf"
}
```

---

## Limitations & Future Improvements

- **No internet source checking** — Currently compares only against uploaded reference files. Future work: integrate Google Scholar / CrossRef API for web-based comparison.
- **No database persistence** — Analyses are ephemeral. Adding SQLite or PostgreSQL would enable history tracking.
- **Language support** — Currently English-optimised. Multi-language stopword lists would extend support.
- **Authentication** — Adding user accounts would enable saving analyses to a personal dashboard.

---

## Team / Credits

Built as a college computer science project demonstrating:
- Full-stack web development (Python/Flask)
- Natural Language Processing (TF-IDF, N-gram shingling)
- Professional PDF generation.
- Modern web UI without external frameworks

---

## License

MIT License — for academic and educational use.
