FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DISPLAY=:99 \
    MCP_TRANSPORT=http \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8003 \
    CHROME_HEADLESS=false \
    VNC_PASSWORD=sigaa \
    DOWNLOAD_PATH=/app/downloads \
    STORAGE_STATE_PATH=/app/.sigaa_state/storage_state.json

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        xvfb \
        x11vnc \
        fluxbox \
        dbus-x11 \
        websockify \
        novnc \
        curl \
        ca-certificates \
        fonts-liberation \
        fonts-freefont-ttf \
        fonts-noto-color-emoji && \
    ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies & Playwright Chromium with OS libraries (cached layers)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

RUN printf 'Acquire::Retries "8";\nAcquire::http::Pipeline-Depth "0";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' > /etc/apt/apt.conf.d/80-retries && \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && \
    uv run playwright install --with-deps chromium && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application code (secrets excluded via .dockerignore)
COPY . .
RUN uv sync --frozen --no-dev && \
    mkdir -p /app/downloads /app/.sigaa_state

RUN cat <<'EOF' > /app/boot.sh && sed -i 's/\r$//' /app/boot.sh && chmod +x /app/boot.sh
#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  echo "[boot] Encerrando serviços auxiliares X11/noVNC..." >&2
  pkill -f websockify 2>/dev/null || true
  pkill -f x11vnc 2>/dev/null || true
  pkill -f fluxbox 2>/dev/null || true
  pkill -f Xvfb 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true

Xvfb :99 -screen 0 1366x860x24 -ac +extension GLX +render -noreset >&2 &
sleep 1

fluxbox -display :99 >&2 &
sleep 1

if [ -n "${VNC_PASSWORD:-}" ]; then
  mkdir -p /root/.vnc
  x11vnc -storepasswd "${VNC_PASSWORD}" /root/.vnc/passwd >&2
  x11vnc -display :99 -forever -shared -rfbport 5900 -rfbauth /root/.vnc/passwd >&2 &
else
  x11vnc -display :99 -forever -shared -rfbport 5900 -nopw >&2 &
fi
sleep 1

websockify -D --web /usr/share/novnc 6080 localhost:5900 >&2

exec /app/.venv/bin/python /app/server.py
EOF

EXPOSE 8003 6080 5900

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8003/health || exit 1

ENTRYPOINT ["/app/boot.sh"]
