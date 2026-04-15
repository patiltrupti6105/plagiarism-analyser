"""
parser.py — Document text extraction module
Supports PDF, DOCX, and TXT file formats.
"""

import fitz  # PyMuPDF
from docx import Document
import os


def extract_text(filepath: str) -> str:
    """
    Extract plain text from a file based on its extension.

    Args:
        filepath: Absolute path to the uploaded file.

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If the file format is unsupported.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return _extract_from_pdf(filepath)
    elif ext == ".docx":
        return _extract_from_docx(filepath)
    elif ext == ".txt":
        return _extract_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _extract_from_pdf(filepath: str) -> str:
    """Extract text from PDF using PyMuPDF (fitz)."""
    text_chunks = []
    with fitz.open(filepath) as doc:
        for page in doc:
            text_chunks.append(page.get_text())
    return "\n".join(text_chunks).strip()


def _extract_from_docx(filepath: str) -> str:
    """Extract text from Word document paragraphs."""
    doc = Document(filepath)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def _extract_from_txt(filepath: str) -> str:
    """Read plain text file with UTF-8 encoding fallback."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            return f.read().strip()
