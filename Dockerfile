FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend and source code
COPY frontend/ /app/frontend/
COPY src/ /app/src/
COPY .env /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for the API
EXPOSE 8000

# Entry point command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 