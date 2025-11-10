# Use a current slim base (buster is EOL). Stick with Python 3.10 if you need it.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create a dedicated work dir ('.' as a workdir is fragile in containers)
WORKDIR /app

# Install build tools only if needed by your wheels; else remove this block
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Layer cache for deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Now copy your project
COPY . .

# Helpful metadata for GHCR
LABEL org.opencontainers.image.title="QCloudSim-SigSim2025" \
      org.opencontainers.image.description="Digital-twin simulation of a quantum cloud environment" \
      org.opencontainers.image.source="https://github.com/wolfatthegate/QCloudSim-SigSim2025" \
      org.opencontainers.image.licenses="Apache-2.0"

# Default command = run both use-cases, exactly like you had
# Using 'sh -lc' keeps behavior identical without depending on bash being present
CMD ["sh", "-lc", "python Section-6-Use-case-1.py && python Section-6-Use-case-2.py"]
