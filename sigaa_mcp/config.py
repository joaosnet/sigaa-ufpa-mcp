"""Centralized typed configuration and runtime settings for SIGAA UFPA MCP."""

from __future__ import annotations

import os
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

os.environ.setdefault("FASTMCP_CHECK_FOR_UPDATES", "off")
os.environ.setdefault("FASTMCP_SHOW_SERVER_BANNER", "false")
load_dotenv()


class _InterceptHandler(logging.Handler):
    """Redirect standard library logging into Loguru on stderr (never stdout)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_stderr_logging(log_level: str | None = None) -> None:
    """Ensure 100% of logs go exclusively to sys.stderr to keep stdio JSON-RPC pure."""
    effective_level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logger.remove()
    logger.add(
        sys.stderr,
        level=effective_level,
        backtrace=False,
        diagnose=False,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(_InterceptHandler())
    root_logger.setLevel(getattr(logging, effective_level, logging.INFO))


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _parse_timeout_ms() -> int:
    raw = (os.getenv("BROWSER_TIMEOUT_MS") or os.getenv("BROWSER_TIMEOUT") or "45000").strip()
    val = int(raw)
    return val * 1000 if val < 1000 else val


def _resolve_download_dir() -> Path:
    raw = (os.getenv("DOWNLOAD_PATH") or "./downloads").strip()
    if os.name == "nt" and raw.startswith("/app"):
        raw = "./downloads"
    return Path(raw).resolve()


@dataclass(slots=True)
class Settings:
    """Typed runtime configuration loaded from environment variables."""

    base_url: str = "https://sigaa.ufpa.br"
    sigaa_username: str = field(default_factory=lambda: (os.getenv("SIGAA_USERNAME") or "").strip())
    sigaa_password: str = field(default_factory=lambda: os.getenv("SIGAA_PASSWORD") or "")
    sigaa_matricula: str = field(default_factory=lambda: (os.getenv("SIGAA_MATRICULA") or "").strip())

    mcp_transport: str = field(
        default_factory=lambda: (os.getenv("MCP_TRANSPORT") or "stdio").strip().lower()
    )
    mcp_host: str = field(
        default_factory=lambda: (os.getenv("MCP_SERVER_HOST") or "0.0.0.0").strip()
    )
    mcp_port: int = field(
        default_factory=lambda: int((os.getenv("MCP_SERVER_PORT") or "8003").strip())
    )
    log_level: str = field(
        default_factory=lambda: (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    )

    chrome_headless: bool = field(
        default_factory=lambda: _env_bool("CHROME_HEADLESS", True)
    )
    browser_timeout_ms: int = field(default_factory=_parse_timeout_ms)
    vnc_password: str = field(
        default_factory=lambda: (os.getenv("VNC_PASSWORD") or "sigaa").strip()
    )

    download_dir: Path = field(default_factory=_resolve_download_dir)
    storage_state_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("STORAGE_STATE_PATH") or ".sigaa_state/storage_state.json"
        ).resolve()
    )

    drive_folder_id: str = field(
        default_factory=lambda: (os.getenv("DRIVE_FOLDER_ID") or "").strip()
    )
    drive_client_secrets_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("DRIVE_CLIENT_SECRETS_PATH") or "client_secrets.json"
        ).resolve()
    )
    drive_token_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("DRIVE_TOKEN_PATH") or "token.json"
        ).resolve()
    )

    def __post_init__(self) -> None:
        if self.mcp_host == "0.0.0":
            self.mcp_host = "0.0.0.0"
        if self.mcp_transport == "studio":
            self.mcp_transport = "stdio"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_env_credentials(self) -> bool:
        return bool(self.sigaa_username and self.sigaa_password)

    @property
    def public_login_url(self) -> str:
        host = "localhost" if self.mcp_host in {"0.0.0.0", "127.0.0.1", "::"} else self.mcp_host
        return f"http://{host}:{self.mcp_port}/login"


settings = Settings()
