# Minimal Playwright Docker image for Render
FROM node:20-slim

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libxkbcommon0 \
    libx11-xcb1 \
    libxcb1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm install --omit=dev

# Install Playwright and Chromium
RUN npx playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 3001

# Set environment variables
ENV NODE_ENV=production
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

# Start the server
CMD ["npm", "start"]

