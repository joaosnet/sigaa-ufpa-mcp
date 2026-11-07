"""Deterministic SIGAA UFPA authentication, vínculo selection, and JSCookMenu navigation."""

from __future__ import annotations

from typing import Any, Optional

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Page

from sigaa_mcp.config import settings
from sigaa_mcp.parsers import clean_ws, parse_portal_discente, parse_vinculos_html
from sigaa_mcp.schemas import EstadoSessao
from sigaa_mcp.session import AuthenticationRequiredError, SigaaSessionManager, session_manager


def _extract_login_error(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in ("#painel-erros", "ul.erros", "div.erros", "#conteudo center", "font[color='red']"):
        el = soup.select_one(sel)
        if el:
            txt = clean_ws(el.get_text(" ", strip=True))
            if txt and any(
                w in txt.lower()
                for w in ("inválid", "invalid", "incorret", "expirad", "erro", "negado", "bloquead")
            ):
                return txt
    return ""


def _is_login_screen(url: str, html: str) -> bool:
    low_url = url.lower()
    if "vertelalogin.do" in low_url or "tela_login" in low_url:
        return True
    soup = BeautifulSoup(html, "lxml")
    return soup.select_one("input[name='user.login']") is not None


def _is_vinculo_screen(url: str, html: str) -> bool:
    low_url = url.lower()
    if "vinculo" in low_url:
        return True
    soup = BeautifulSoup(html, "lxml")
    txt = clean_ws(soup.get_text(" ", strip=True)).lower()
    return "escolha o vínculo" in txt or "selecione o vínculo" in txt


def _is_portal_discente_ready(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return (
        soup.select_one("#perfil-docente") is not None
        or soup.select_one("#turmas-portal") is not None
        or soup.select_one("form[id*='form_menu_discente']") is not None
    )


async def _bypass_intermediate_screens(page: Page) -> None:
    """Bypass post-login questionnaires, notices, or calendar landing screens."""
    for _ in range(4):
        url = page.url.lower()
        html = await page.content()
        if _is_portal_discente_ready(html) or _is_vinculo_screen(url, html) or _is_login_screen(url, html):
            return

        cont_btn = page.locator(
            "input[type='submit'][value*='Continuar'], "
            "input[type='button'][value*='Continuar'], "
            "a:has-text('Continuar >>'), "
            "a:has-text('Portal do Discente')"
        ).first
        if await cont_btn.count() > 0 and await cont_btn.is_visible():
            try:
                async with page.expect_navigation(wait_until="domcontentloaded", timeout=20000):
                    await cont_btn.click()
                continue
            except Exception:
                pass

        # Common UFPA post-login screen: calendarios_graduacao_vigentes.jsf
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        return


async def _click_vinculo_on_page(page: Page, target_index: int) -> bool:
    """Click the link inside the target vínculo row."""
    links = page.locator("table.listagem tr a, table.subFormulario tr a, #conteudo table tr a")
    count = await links.count()
    if 0 <= target_index < count:
        async with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.browser_timeout_ms):
            await links.nth(target_index).click()
        return True
    return False


async def _resolve_vinculo_if_needed(
    session: SigaaSessionManager,
    page: Page,
    ctx: Any = None,
    allow_pause_for_visual_choice: bool = False,
) -> bool:
    """Resolve multi-vínculo screen automatically or pause for visual UI choice."""
    html = await page.content()
    if not _is_vinculo_screen(page.url, html):
        session.awaiting_vinculo_selection = False
        return True

    vinculos = parse_vinculos_html(html)
    session.vinculos = vinculos
    if not vinculos:
        session.awaiting_vinculo_selection = False
        return True

    pref_mat = session.preferred_matricula
    if pref_mat:
        for v in vinculos:
            if v.matricula == pref_mat or pref_mat in v.curso or pref_mat in v.identificador:
                await _click_vinculo_on_page(page, v.indice)
                session.awaiting_vinculo_selection = False
                await _bypass_intermediate_screens(page)
                return True

    ativos = [v for v in vinculos if v.ativo]
    if len(vinculos) == 1 or len(ativos) == 1:
        chosen = ativos[0] if len(ativos) == 1 else vinculos[0]
        await _click_vinculo_on_page(page, chosen.indice)
        session.awaiting_vinculo_selection = False
        await _bypass_intermediate_screens(page)
        return True

    if allow_pause_for_visual_choice:
        session.awaiting_vinculo_selection = True
        return False

    # Try FastMCP elicitation if supported by host client
    chosen_idx = (ativos[0].indice if ativos else 0)
    if ctx is not None and hasattr(ctx, "elicit"):
        try:
            opcoes_str = ", ".join(
                f"{v.indice}: {v.matricula or v.identificador} ({v.curso})" for v in vinculos
            )
            elicit_res = await ctx.elicit(
                f"Múltiplos vínculos encontrados no SIGAA ({opcoes_str}). Informe a matrícula ou índice desejado:",
                response_type=str,
            )
            ans = str(getattr(elicit_res, "data", "") or "").strip()
            if ans:
                for v in vinculos:
                    if ans == str(v.indice) or (v.matricula and ans == v.matricula):
                        chosen_idx = v.indice
                        session.set_ram_credentials(
                            session.username,
                            session.get_password_for_form(),
                            preferred_matricula=v.matricula or str(v.indice),
                        )
                        break
        except Exception as exc:
            logger.debug(f"Cliente MCP sem suporte interativo a elicit(); selecionando vínculo ativo padrão: {exc}")

    await _click_vinculo_on_page(page, chosen_idx)
    session.awaiting_vinculo_selection = False
    await _bypass_intermediate_screens(page)
    return True


async def _refresh_portal_snapshot_unlocked(session: SigaaSessionManager, page: Page) -> None:
    if not _is_portal_discente_ready(await page.content()):
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        await _bypass_intermediate_screens(page)

    html = await page.content()
    if _is_portal_discente_ready(html):
        perfil, _, _, _ = parse_portal_discente(html, base_url=settings.base_url)
        session.perfil_atual = perfil
        session.authenticated = True
        session.awaiting_vinculo_selection = False
        await session.save_storage_state_if_enabled()


async def authenticate_with_credentials(
    username: str,
    password: str,
    manter_sessao: bool = False,
    matricula_preferida: Optional[str] = None,
    allow_pause_for_visual_choice: bool = True,
    session: Optional[SigaaSessionManager] = None,
) -> EstadoSessao:
    """Perform a clean login on SIGAA UFPA using volatile RAM credentials."""
    mgr = session or session_manager
    clean_user = username.strip()
    if not clean_user or not password:
        return mgr.get_estado_sessao("Informe usuário e senha válidos do SIGAA UFPA.")

    async with mgr.lock:
        mgr.set_ram_credentials(
            username=clean_user,
            password=password,
            persist_cookies=manter_sessao,
            preferred_matricula=matricula_preferida,
        )
        page = await mgr.ensure_browser_page()
        logger.info(f"Iniciando autenticação determinística no SIGAA para usuário '{clean_user}'...")

        # Ensure clean login screen if another user was previously logged in
        await page.goto(
            f"{settings.base_url}/sigaa/logar.do?dispatch=logOff",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        await page.goto(
            f"{settings.base_url}/sigaa/verTelaLogin.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )

        login_input = page.locator("input[name='user.login']").first
        senha_input = page.locator("input[name='user.senha']").first
        await login_input.fill(clean_user)
        await senha_input.fill(password)

        submit_btn = page.locator(
            "#conteudo div.logon input[type='submit'], input[value*='Entrar'], input[type='submit']"
        ).first
        async with page.expect_navigation(
            wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
        ):
            await submit_btn.click()

        post_html = await page.content()
        if _is_login_screen(page.url, post_html):
            err_msg = _extract_login_error(post_html) or "Usuário ou senha recusados pelo SIGAA UFPA."
            mgr.authenticated = False
            mgr.clear_ram_credentials(keep_env_fallback=False)
            logger.warning(f"Falha de autenticação no SIGAA para '{clean_user}': {err_msg}")
            return mgr.get_estado_sessao(f"Falha no login: {err_msg}")

        await _bypass_intermediate_screens(page)
        resolved = await _resolve_vinculo_if_needed(
            mgr,
            page,
            ctx=None,
            allow_pause_for_visual_choice=allow_pause_for_visual_choice,
        )
        if not resolved and mgr.awaiting_vinculo_selection:
            await mgr.notify_session_changed()
            return mgr.get_estado_sessao(
                "Autenticação aceita! Selecione abaixo qual vínculo institucional deseja utilizar."
            )

        await _refresh_portal_snapshot_unlocked(mgr, page)
        await mgr.notify_session_changed()
        if mgr.authenticated:
            logger.info(
                f"Login concluído com sucesso: {mgr.perfil_atual.nome} ({mgr.perfil_atual.matricula})"
            )
            return mgr.get_estado_sessao(
                f"Autenticado com sucesso como {mgr.perfil_atual.nome} (Matrícula {mgr.perfil_atual.matricula})."
            )
        return mgr.get_estado_sessao("Não foi possível alcançar o Portal do Discente após o login.")


async def select_vinculo(
    identificador_ou_matricula: str,
    session: Optional[SigaaSessionManager] = None,
) -> EstadoSessao:
    """Switch or complete institutional vínculo selection visually."""
    mgr = session or session_manager
    target = identificador_ou_matricula.strip()
    async with mgr.lock:
        page = await mgr.ensure_browser_page()
        if not _is_vinculo_screen(page.url, await page.content()):
            await page.goto(
                f"{settings.base_url}/sigaa/escolhaVinculo.do?dispatch=listar",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )

        html = await page.content()
        vinculos = parse_vinculos_html(html)
        mgr.vinculos = vinculos
        if not vinculos:
            return mgr.get_estado_sessao("Lista de vínculos não disponível nesta conta.")

        chosen = None
        for v in vinculos:
            if (
                target == str(v.indice)
                or (v.matricula and target == v.matricula)
                or target.lower() in v.curso.lower()
                or target.lower() in v.identificador.lower()
            ):
                chosen = v
                break
        if chosen is None:
            chosen = vinculos[0]

        mgr._preferred_matricula = chosen.matricula or str(chosen.indice)
        await _click_vinculo_on_page(page, chosen.indice)
        await _bypass_intermediate_screens(page)
        await _refresh_portal_snapshot_unlocked(mgr, page)
        await mgr.notify_session_changed()
        return mgr.get_estado_sessao(
            f"Vínculo ativo alterado para {mgr.perfil_atual.curso} ({mgr.perfil_atual.matricula})."
        )


async def ensure_authenticated_portal(
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> Page:
    """Guarantee the Playwright page is authenticated and positioned on Portal do Discente.

    Assumes caller ALREADY holds ``session.lock``.
    Raises ``AuthenticationRequiredError`` when logged out and no credentials/cookies exist.
    """
    mgr = session or session_manager
    if (
        not mgr.authenticated
        and not mgr.has_credentials
        and not settings.storage_state_path.is_file()
    ):
        raise AuthenticationRequiredError(
            "Sessão do SIGAA não autenticada. Utilize a janela de Login Visual no chat "
            f"ou acesse {settings.public_login_url} para entrar com seu usuário e senha."
        )

    page = await mgr.ensure_browser_page()

    # 1. Fast check if already on Portal do Discente
    if page.url.startswith(settings.base_url):
        cur_html = await page.content()
        if _is_portal_discente_ready(cur_html):
            perfil, _, _, _ = parse_portal_discente(cur_html, base_url=settings.base_url)
            if perfil.matricula or perfil.nome:
                mgr.perfil_atual = perfil
            mgr.authenticated = True
            return page

    # 2. Try navigating directly to Portal do Discente ONLY if we already have an active session or saved cookies
    if mgr.authenticated or settings.storage_state_path.is_file():
        try:
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            await _bypass_intermediate_screens(page)
            await _resolve_vinculo_if_needed(mgr, page, ctx=ctx, allow_pause_for_visual_choice=False)
            cur_html = await page.content()
            if _is_portal_discente_ready(cur_html):
                perfil, _, _, _ = parse_portal_discente(cur_html, base_url=settings.base_url)
                mgr.perfil_atual = perfil
                mgr.authenticated = True
                return page
        except Exception as exc:
            logger.debug(f"Revalidação direta de cookies falhou, prosseguindo para login completo: {exc}")

    # 3. Session expired or unauthenticated -> auto-login if RAM or .env credentials exist
    if not mgr.has_credentials:
        mgr.authenticated = False
        raise AuthenticationRequiredError(
            "Sessão do SIGAA não autenticada. Utilize a janela de Login Visual no chat "
            f"ou acesse {settings.public_login_url} para entrar com seu usuário e senha."
        )

    logger.info(f"Autenticando sessão no SIGAA para '{mgr.username}'...")
    await page.goto(
        f"{settings.base_url}/sigaa/verTelaLogin.do",
        wait_until="domcontentloaded",
        timeout=settings.browser_timeout_ms,
    )
    await page.locator("input[name='user.login']").first.fill(mgr.username)
    await page.locator("input[name='user.senha']").first.fill(mgr.get_password_for_form())
    submit_btn = page.locator(
        "#conteudo div.logon input[type='submit'], input[value*='Entrar'], input[type='submit']"
    ).first
    async with page.expect_navigation(
        wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
    ):
        await submit_btn.click()

    post_html = await page.content()
    if _is_login_screen(page.url, post_html):
        err = _extract_login_error(post_html) or "Credenciais inválidas no SIGAA."
        mgr.authenticated = False
        raise AuthenticationRequiredError(f"Não foi possível autenticar no SIGAA: {err}")

    await _bypass_intermediate_screens(page)
    await _resolve_vinculo_if_needed(mgr, page, ctx=ctx, allow_pause_for_visual_choice=False)
    await _refresh_portal_snapshot_unlocked(mgr, page)
    if not mgr.authenticated:
        raise AuthenticationRequiredError("Sessão autenticada não alcançou o Portal do Discente.")
    return page


async def invoke_portal_menu(
    page: Page,
    bean_substring: str,
    expect_navigation: bool = True,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> Optional[str]:
    """Trigger a JSCookMenu action on Portal do Discente via JSF '_cmItemList'."""
    mgr = session or session_manager
    if not _is_portal_discente_ready(await page.content()):
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)

    js = """(sub) => {
        if (typeof _cmItemList === 'undefined') return null;
        for (const it of _cmItemList) {
            if (Array.isArray(it) && typeof it[2] === 'string' && it[2].includes(sub)) {
                const target = it[3] || 'menu:form_menu_discente';
                const form = document.forms[target];
                if (form && form.elements['jscook_action']) {
                    form.elements['jscook_action'].value = it[2];
                    form.submit();
                    return it[2];
                }
            }
        }
        return null;
    }"""

    if expect_navigation:
        async with page.expect_navigation(
            wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
        ):
            action_id = await page.evaluate(js, bean_substring)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        return action_id

    return await page.evaluate(js, bean_substring)


async def logout_sigaa(session: Optional[SigaaSessionManager] = None) -> EstadoSessao:
    """Log off from SIGAA, wipe volatile RAM credentials, delete saved cookies, and purge caches."""
    mgr = session or session_manager
    async with mgr.lock:
        if mgr._page is not None and not mgr._page.is_closed():
            try:
                await mgr._page.goto(
                    f"{settings.base_url}/sigaa/logar.do?dispatch=logOff",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            except Exception:
                pass
        await mgr._close_browser_unlocked()
        mgr.clear_ram_credentials(keep_env_fallback=False)
        mgr.remove_saved_storage_state()
        mgr.authenticated = False
        mgr.awaiting_vinculo_selection = False
        mgr.vinculos = []
        mgr.perfil_atual = mgr.perfil_atual.__class__()
        await mgr.notify_session_changed()
        logger.info("Sessão do SIGAA encerrada e credenciais voláteis limpas.")
        return mgr.get_estado_sessao("Sessão encerrada com sucesso. Credenciais e cookies removidos.")


async def restart_sigaa_session(session: Optional[SigaaSessionManager] = None) -> EstadoSessao:
    """Reset Playwright browser/context and re-validate session if credentials or cookies exist."""
    mgr = session or session_manager
    async with mgr.lock:
        await mgr._close_browser_unlocked()
        mgr.authenticated = False
        await mgr.notify_session_changed()
        if mgr.has_credentials or settings.storage_state_path.is_file():
            try:
                await ensure_authenticated_portal(session=mgr)
                return mgr.get_estado_sessao(
                    f"Sessão reiniciada e reautenticada para {mgr.perfil_atual.nome or mgr.username}."
                )
            except AuthenticationRequiredError as exc:
                return mgr.get_estado_sessao(str(exc))
        return mgr.get_estado_sessao(
            "Navegador reiniciado em estado limpo. Faça login visual para iniciar nova sessão."
        )
