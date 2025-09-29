FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ANONYMIZED_TELEMETRY=false \
    PATH="/root/.local/bin:/app/.venv/bin:$PATH" \
    DISPLAY=:0 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage"

# Install system dependencies
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
    clang \
    git \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    tigervnc-standalone-server \
    tigervnc-tools \
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

# Set up VNC and boot script
RUN mkdir -p /root/.vnc && \
    printf '#!/bin/sh\nunset SESSION_MANAGER\nunset DBUS_SESSION_BUS_ADDRESS\nstartxfce4' > /root/.vnc/xstartup && \
    chmod +x /root/.vnc/xstartup && \
    printf '#!/bin/bash\n\n# Use Docker secret for VNC password if available, else fallback to default\nif [ -f "/run/secrets/vnc_password" ]; then\n  cat /run/secrets/vnc_password | vncpasswd -f > /root/.vnc/passwd\nelse\n  echo "browser-use" | vncpasswd -f > /root/.vnc/passwd\nfi\nchmod 600 /root/.vnc/passwd\nvncserver -depth 24 -geometry 1920x1080 -localhost no -PasswordFile /root/.vnc/passwd :0\nproxy-login-automator 2>/dev/null || true\nexport MCP_TRANSPORT=${MCP_TRANSPORT:-http}\nwebsockify -D --web /usr/share/novnc 6080 localhost:5900 &\npython server.py' > /app/boot.sh && \
    chmod +x /app/boot.sh

EXPOSE 8000

ENTRYPOINT ["/bin/bash", "/app/boot.sh"]