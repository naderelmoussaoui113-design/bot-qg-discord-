FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including Node.js and Chromium deps
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium --with-deps || true

COPY . .

CMD ["python", "jarvis_agent.py"]
