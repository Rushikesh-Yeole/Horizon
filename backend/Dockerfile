# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
# Pre-install CPU-only PyTorch to prevent downloading massive NVIDIA CUDA GPU binaries (saves ~3GB of bloat)
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application (Uses PORT env var provided by Cloud Run, defaults to 8000 locally)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
