FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run uvicorn server by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
