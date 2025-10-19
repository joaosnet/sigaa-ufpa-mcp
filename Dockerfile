# Stage 1: Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment
RUN uv sync --frozen --no-dev

# Stage 2: Runtime stage
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

# Install system dependencies (minimal for better compatibility)
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
    xvfb \
    x11vnc \
    dbus \
    fonts-liberation \
    fonts-noto-color-emoji \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    curl \
    ca-certificates \
    python3-pip && \
    pip3 install --no-cache-dir websockify && \
    mkdir -p /usr/share/novnc && \
    curl -sSL https://github.com/novnc/noVNC/archive/v1.4.0.tar.gz | tar -xz -C /usr/share/novnc --strip-components=1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache

# Set up working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the rest of the application
COPY . .

# Install Playwright with Chromium only (minimal installation)
RUN /app/.venv/bin/playwright install chromium --no-shell && \
    rm -rf /root/.cache/ms-playwright/chromium-*/chrome-linux/swiftshader && \
    rm -rf /root/.cache/ms-playwright/chromium-*/locales/* && \
    strip /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome || true && \
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type f -name "*.pyo" -delete

# Set up boot script with Xvfb + x11vnc + noVNC
RUN printf '#!/bin/bash\nset -e\n\n# Cleanup function to stop all services\ncleanup() {\n  echo "Shutting down services..." >&2\n  pkill -f websockify || true\n  pkill -f x11vnc || true\n  pkill -f Xvfb || true\n  exit 0\n}\n\ntrap cleanup SIGTERM SIGINT EXIT\n\n# Start Xvfb (Virtual X Server) with reduced memory\nXvfb :99 -screen 0 1280x720x16 -ac +extension GLX +render -noreset >&2 &\nsleep 1\n\n# Start x11vnc (no password for simplicity, adjust if needed)\nx11vnc -display :99 -forever -shared -rfbport 5900 -nopw -noxdamage >&2 &\nsleep 1\n\n# Start noVNC websocket proxy\nexport MCP_TRANSPORT=${MCP_TRANSPORT:-http}\nwebsockify -D --web /usr/share/novnc 6080 localhost:5900 >&2\n\n# Run Python server in foreground (main process)\npython server.py\n\n# If Python exits, cleanup will be called automatically' > /app/boot.sh && \
    chmod +x /app/boot.sh

EXPOSE 8003 6080

ENTRYPOINT ["/bin/bash", "/app/boot.sh"]