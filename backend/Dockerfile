FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for asyncpg and building native wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the default embedding model to optimize startup time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application source code and migrations
COPY . .

# Expose default port
EXPOSE 8000

# Set default command using $PORT from environment (Render compatibility)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
