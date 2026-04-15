# ─────────────────────────────────────────────────────────────
# Dockerfile — PlagiaGuard Plagiarism Analyser
# Base: Python 3.12 slim (stable, small image)
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install OS dependencies needed by PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    libfreetype6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching — only re-runs if requirements.txt changes)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of application source
COPY . .

# Create required runtime directories (uploads are ephemeral, reports persist)
RUN mkdir -p uploads reports

# Expose Flask port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the Flask app with production server
CMD ["python", "app.py"]
