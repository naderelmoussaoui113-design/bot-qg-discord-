FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Playwright / Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium --with-deps

COPY . .

CMD ["python", "agent_core.py"]
