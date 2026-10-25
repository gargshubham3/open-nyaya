FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install package and dependencies
RUN pip install --no-cache-dir -e .

# Hugging Face Spaces default port is 7860
EXPOSE 7860

CMD ["uvicorn", "nyaya.web:app", "--host", "0.0.0.0", "--port", "7860"]
