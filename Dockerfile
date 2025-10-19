FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ANONYMIZED_TELEMETRY=false \
    PATH="/root/.local/bin:/app/.venv/bin:$PATH" \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

# Install system dependencies (minimal X11 + Chromium + noVNC)
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
    clang \
    git \
    xvfb \
    x11vnc \
    fluxbox \
    dbus-x11 \
    fonts-freefont-ttf \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-symbola \
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
    nodejs \
    npm \
    websockify \
    novnc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install proxy-login-automator
RUN npm install -g npm@latest && \
    npm i -g proxy-login-automator || echo "proxy-login-automator installation failed, continuing..."

# Set up working directory and copy project files
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# Install Playwright
RUN uvx playwright install chromium --with-deps --no-shell

# Set up boot script with Xvfb + x11vnc + noVNC
RUN printf '#!/bin/bash\nset -e\n\n# Cleanup function to stop all services\ncleanup() {\n  echo "Shutting down services..." >&2\n  pkill -f websockify || true\n  pkill -f x11vnc || true\n  pkill -f Xvfb || true\n  pkill -f fluxbox || true\n  pkill -f proxy-login-automator || true\n  exit 0\n}\n\ntrap cleanup SIGTERM SIGINT EXIT\n\n# Start Xvfb (Virtual X Server)\nXvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset >&2 &\nsleep 2\n\n# Start lightweight window manager\nfluxbox -display :99 >&2 &\nsleep 1\n\n# Start x11vnc (no password for simplicity, adjust if needed)\nx11vnc -display :99 -forever -shared -rfbport 5900 -nopw >&2 &\nsleep 2\n\n# Start proxy-login-automator\nproxy-login-automator 2>/dev/null || true &\n\n# Start noVNC websocket proxy\nexport MCP_TRANSPORT=${MCP_TRANSPORT:-http}\nwebsockify -D --web /usr/share/novnc 6080 localhost:5900 >&2\n\n# Run Python server in foreground (main process)\npython server.py\n\n# If Python exits, cleanup will be called automatically' > /app/boot.sh && \
    chmod +x /app/boot.sh

EXPOSE 8000 6080

ENTRYPOINT ["/bin/bash", "/app/boot.sh"]