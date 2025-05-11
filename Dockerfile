# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libyaml-dev \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY kubeflow_pipelines/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GROQ_API_KEY=""

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
