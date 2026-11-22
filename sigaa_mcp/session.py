"""Playwright browser/context lifecycle, volatile RAM credential vault, and CDP PDF helper."""

from __future__ import annotations

import asyncio
import base64
import os
import stat
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from sigaa_mcp.config import settings
from sigaa_mcp.schemas import EstadoSessao, PerfilDiscenteResumo, VinculoItem


class AuthenticationRequiredError(RuntimeError):
    """Raised when an operation requires SIGAA login and no active session or .env credentials exist."""


class _ActivityLock:
    """asyncio.Lock wrapper that tracks browser activity to drive the idle shutdown timer.

    Every ``async with session_manager.lock`` cancels the idle watchdog on entry and, on exit,
    re-arms it so Chromium is closed after ``BROWSER_IDLE_TIMEOUT_S`` seconds of inactivity.
    """

    def __init__(self, owner: "SigaaSessionManager") -> None:
        self._lock = asyncio.Lock()
        self._owner = owner

    def locked(self) -> bool:
        return self._lock.locked()

    async def acquire(self) -> bool:
        await self._lock.acquire()
        self._owner._cancel_idle_timer()
        return True

    def release(self) -> None:
        self._lock.release()
        self._owner._arm_idle_timer()

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(self, *exc: object) -> None:
        self.release()


class SigaaSessionManager:
    """Thread/task-safe singleton managing Playwright Chromium and SIGAA session state."""

    def __init__(self) -> None:
        self._lock = _ActivityLock(self)
        self._idle_task: Optional[asyncio.Task[None]] = None
        self._last_activity: float = time.monotonic()
        # In-memory cookie snapshot kept after an idle shutdown so the next call resumes the
        # SIGAA session without a full re-login (never written to disk unless persistence is on).
        self._ram_storage_state: Optional[dict] = None
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Volatile RAM credentials (initialized from optional .env if provided; never written to disk)
        self._username: str = settings.sigaa_username
        self._password: str = settings.sigaa_password
        self._preferred_matricula: str = settings.sigaa_matricula
        self._persist_cookies: bool = False

        # Live session metadata
        self.authenticated: bool = False
        self.awaiting_vinculo_selection: bool = False
        self.vinculos: list[VinculoItem] = []
        self.perfil_atual: PerfilDiscenteResumo = PerfilDiscenteResumo()
        self._change_listeners: list[Callable[[], Awaitable[None]]] = []

    @property
    def lock(self) -> _ActivityLock:
        return self._lock

    @property
    def browser_running(self) -> bool:
        return self._browser is not None

    # ------------------------------------------------------------------ idle shutdown
    def _cancel_idle_timer(self) -> None:
        task = self._idle_task
        self._idle_task = None
        if task is not None and not task.done() and task is not asyncio.current_task():
            task.cancel()

    def _arm_idle_timer(self) -> None:
        self._last_activity = time.monotonic()
        timeout = settings.browser_idle_timeout_s
        if timeout <= 0 or self._browser is None:
            return
        self._cancel_idle_timer()
        try:
            self._idle_task = asyncio.get_running_loop().create_task(self._idle_watchdog(timeout))
        except RuntimeError:
            self._idle_task = None

    async def _idle_watchdog(self, timeout: float) -> None:
        try:
            while True:
                remaining = self._last_activity + timeout - time.monotonic()
                if remaining > 0:
                    await asyncio.sleep(remaining)
                    continue
                if self._lock.locked():
                    return  # busy again; release() re-arms the watchdog
                if self.awaiting_vinculo_selection:
                    # User still has to pick a vínculo on the open page; give them another window.
                    self._last_activity = time.monotonic()
                    continue
                async with self._lock._lock:
                    await self._shutdown_idle_browser_unlocked()
                return
        except asyncio.CancelledError:
            pass

    async def _shutdown_idle_browser_unlocked(self) -> None:
        if self._browser is None:
            return
        snapshot: Optional[dict] = None
        if self._context is not None:
            try:
                snapshot = await self._context.storage_state()
            except Exception as exc:
                logger.debug(f"Não foi possível capturar cookies antes do desligamento ocioso: {exc}")
            await self.save_storage_state_if_enabled()
        await self._close_browser_unlocked()
        self._ram_storage_state = snapshot
        logger.info(
            f"Chromium encerrado após {settings.browser_idle_timeout_s:.0f}s ocioso "
            "(será reaberto automaticamente na próxima chamada)."
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self._username and self._password)

    @property
    def username(self) -> str:
        return self._username

    @property
    def preferred_matricula(self) -> str:
        return self._preferred_matricula or settings.sigaa_matricula

    def set_ram_credentials(
        self,
        username: str,
        password: str,
        persist_cookies: bool = False,
        preferred_matricula: Optional[str] = None,
    ) -> None:
        """Store credentials strictly in volatile process RAM."""
        self._username = username.strip()
        self._password = password
        self._persist_cookies = bool(persist_cookies)
        if preferred_matricula is not None:
            self._preferred_matricula = preferred_matricula.strip()

    def clear_ram_credentials(self, keep_env_fallback: bool = False) -> None:
        """Wipe credentials from RAM (and optionally avoid reloading .env until requested)."""
        if keep_env_fallback and settings.has_env_credentials:
            self._username = settings.sigaa_username
            self._password = settings.sigaa_password
        else:
            self._username = ""
            self._password = ""
        self._persist_cookies = False

    def get_password_for_form(self) -> str:
        """Return active password strictly for internal Playwright form submission (e.g. profile save)."""
        return self._password

    def register_change_listener(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._change_listeners.append(callback)

    async def notify_session_changed(self) -> None:
        for cb in self._change_listeners:
            try:
                await cb()
            except Exception as exc:
                logger.warning(f"Falha ao notificar listener de mudança de sessão: {exc}")

    async def ensure_browser_page(self) -> Page:
        """Launch Chromium and create BrowserContext + Page if not yet active."""
        if self._page is not None and not self._page.is_closed():
            return self._page

        resume_state = self._ram_storage_state
        await self._close_browser_unlocked()
        self._ram_storage_state = resume_state
        logger.info(
            f"Inicializando Chromium Playwright (headless={settings.chrome_headless}, timeout={settings.browser_timeout_ms}ms)..."
        )
        self._playwright = await async_playwright().start()
        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1366,860",
        ]
        self._browser = await self._playwright.chromium.launch(
            headless=settings.chrome_headless,
            args=launch_args,
        )

        context_kwargs: dict = {
            "accept_downloads": True,
            "viewport": {"width": 1366, "height": 820},
            "locale": "pt-BR",
            "timezone_id": "America/Belem",
        }
        if self._ram_storage_state is not None:
            context_kwargs["storage_state"] = self._ram_storage_state
            logger.info("Retomando sessão SIGAA a partir dos cookies mantidos em RAM.")
        elif settings.storage_state_path.is_file():
            try:
                context_kwargs["storage_state"] = str(settings.storage_state_path)
                self._persist_cookies = True
                logger.info(f"Carregando storage_state de cookies salvo em {settings.storage_state_path}")
            except Exception as exc:
                logger.warning(f"Ignorando storage_state inválido: {exc}")

        self._context = await self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(settings.browser_timeout_ms)
        self._page = await self._context.new_page()
        self._ram_storage_state = None
        return self._page

    async def save_storage_state_if_enabled(self) -> None:
        """Persist session cookies ONLY (never plaintext password) when requested by user."""
        if not self._persist_cookies or self._context is None:
            return
        try:
            target = settings.storage_state_path
            target.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(target))
            try:
                os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
            logger.info(f"Sessão de cookies salva com segurança em {target}")
        except Exception as exc:
            logger.warning(f"Não foi possível salvar storage_state: {exc}")

    def remove_saved_storage_state(self) -> None:
        """Delete persisted cookie file on logout."""
        try:
            if settings.storage_state_path.is_file():
                settings.storage_state_path.unlink(missing_ok=True)
                logger.info("Arquivo storage_state.json removido do disco.")
        except Exception as exc:
            logger.warning(f"Falha ao remover storage_state.json: {exc}")

    async def print_current_page_to_pdf(self, output_path: Path) -> Path:
        """Render current page to PDF via CDP Page.printToPDF (works in both headless and headed Xvfb!)."""
        if self._context is None or self._page is None:
            raise RuntimeError("Navegador não inicializado para impressão em PDF.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cdp = await self._context.new_cdp_session(self._page)
        try:
            await cdp.send("Emulation.setEmulatedMedia", {"media": "screen"})
            pdf_res = await cdp.send(
                "Page.printToPDF",
                {
                    "printBackground": True,
                    "preferCSSPageSize": False,
                    "paperWidth": 8.27,
                    "paperHeight": 11.69,
                    "marginTop": 0.35,
                    "marginBottom": 0.35,
                    "marginLeft": 0.35,
                    "marginRight": 0.35,
                },
            )
            pdf_bytes = base64.b64decode(pdf_res["data"])
            output_path.write_bytes(pdf_bytes)
            return output_path
        finally:
            try:
                await cdp.detach()
            except Exception:
                pass

    def get_estado_sessao(self, mensagem: str = "") -> EstadoSessao:
        """Build a safe, password-free snapshot of the current authentication state."""
        modo = (
            "cookies_disco"
            if (self._persist_cookies or settings.storage_state_path.is_file())
            else ("credenciais_env" if settings.has_env_credentials and self._username == settings.sigaa_username else "volatil_ram")
        )
        return EstadoSessao(
            autenticado=self.authenticated,
            usuario=self._username,
            nome_discente=self.perfil_atual.nome,
            matricula_ativa=self.perfil_atual.matricula or self.preferred_matricula,
            curso_ativo=self.perfil_atual.curso,
            semestre_atual=self.perfil_atual.semestre_atual,
            modo_persistencia=modo,
            tem_credenciais_env=settings.has_env_credentials,
            tem_sessao_salva_disco=settings.storage_state_path.is_file(),
            multiplos_vinculos=len(self.vinculos) > 1,
            aguardando_escolha_vinculo=self.awaiting_vinculo_selection,
            vinculos=list(self.vinculos),
            login_url=settings.public_login_url,
            mensagem=mensagem
            or (
                f"Sessão ativa para {self.perfil_atual.nome or self._username}."
                if self.authenticated
                else "Sessão não autenticada. Utilize o Login Visual ou acesse a URL local de login."
            ),
        )

    async def _close_browser_unlocked(self) -> None:
        for obj, method in (
            (self._page, "close"),
            (self._context, "close"),
            (self._browser, "close"),
            (self._playwright, "stop"),
        ):
            if obj is not None:
                try:
                    await getattr(obj, method)()
                except Exception:
                    pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        self._ram_storage_state = None

    async def close(self) -> None:
        self._cancel_idle_timer()
        async with self._lock._lock:
            await self._close_browser_unlocked()
            self.authenticated = False


session_manager = SigaaSessionManager()
