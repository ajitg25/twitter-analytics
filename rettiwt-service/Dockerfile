# Node.js with Playwright for Render
FROM node:20-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files first (better caching)
COPY package*.json ./

# Install npm dependencies
RUN npm install

# Install Playwright Chromium browser
RUN npx playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 3001

# Start the server
CMD ["node", "server.js"]

