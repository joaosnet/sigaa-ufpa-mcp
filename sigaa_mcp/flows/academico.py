"""Academic document and grade flows: Portal summary, Histórico PDF, Atestado PDF, and Boletim."""

from __future__ import annotations

import re
from typing import Any, Optional

from bs4 import BeautifulSoup
from loguru import logger

from sigaa_mcp.auth import ensure_authenticated_portal, invoke_portal_menu
from sigaa_mcp.config import settings
from sigaa_mcp.drive_service import GoogleDriveService, is_drive_configured
from sigaa_mcp.parsers import (
    clean_ws,
    parse_atestado_html,
    parse_historico_pdf,
    parse_minhas_notas_html,
    parse_portal_discente,
)
from sigaa_mcp.schemas import (
    AtestadoResumo,
    AtividadePendente,
    AvisoTurma,
    HistoricoResumo,
    NotaDisciplina,
    PerfilDiscenteResumo,
    TurmaMatriculada,
)
from sigaa_mcp.session import SigaaSessionManager, session_manager


async def _report(ctx: Any, progress: float, total: float, message: str) -> None:
    if ctx is not None and hasattr(ctx, "report_progress"):
        try:
            await ctx.report_progress(progress=progress, total=total, message=message)
        except Exception:
            pass


def _maybe_upload_to_drive(local_path: str, mime_type: str, enviar_drive: bool) -> Optional[str]:
    if not enviar_drive:
        return None
    if not is_drive_configured():
        logger.warning("Upload para Google Drive solicitado, mas credenciais OAuth não estão configuradas.")
        return None
    try:
        svc = GoogleDriveService()
        uploaded = svc.upload_arquivo(caminho_local=local_path, mime_type=mime_type)
        if uploaded:
            return uploaded.get("drive_link") or uploaded.get("webViewLink")
    except Exception as exc:
        logger.warning(f"Falha opcional no upload para Google Drive: {exc}")
    return None


async def obter_resumo_portal_flow(
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> tuple[PerfilDiscenteResumo, list[TurmaMatriculada], list[AvisoTurma], list[AtividadePendente]]:
    """Fetch and parse the main Portal do Discente overview."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 3, "Acessando Portal do Discente no SIGAA UFPA...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        html = await page.content()
        perfil, turmas, avisos, atividades = parse_portal_discente(html, base_url=settings.base_url)
        mgr.perfil_atual = perfil
        await _report(ctx, 3, 3, "Portal do Discente carregado.")
        return perfil, turmas, avisos, atividades


async def baixar_historico_escolar_flow(
    enviar_drive: bool = False,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> HistoricoResumo:
    """Download official Histórico Escolar PDF and parse its academic metrics."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 4, "Autenticando e abrindo menu Ensino -> Emitir Histórico...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        portal_html = await page.content()
        perfil, _, _, _ = parse_portal_discente(portal_html, base_url=settings.base_url)
        mgr.perfil_atual = perfil

        await _report(ctx, 2, 4, "Aguardando geração oficial do PDF do Histórico Escolar...")
        async with page.expect_download(timeout=max(settings.browser_timeout_ms, 45000)) as dl_info:
            action = await invoke_portal_menu(
                page, "portalDiscente.historico", expect_navigation=False, ctx=ctx, session=mgr
            )
            if not action:
                raise RuntimeError("Item de menu 'Emitir Histórico' não encontrado no Portal do Discente.")

        download = await dl_info.value
        safe_mat = re.sub(r"\W+", "", perfil.matricula or mgr.username or "discente")
        pdf_path = settings.download_dir / f"historico_{safe_mat}.pdf"
        await download.save_as(str(pdf_path))

        await _report(ctx, 3, 4, "Extraindo indicadores, cargas horárias e pendências via pypdf...")
        resumo = parse_historico_pdf(pdf_path, fallback_perfil=perfil)
        resumo.drive_link = _maybe_upload_to_drive(str(pdf_path), "application/pdf", enviar_drive)
        await _report(ctx, 4, 4, "Histórico Escolar processado com sucesso.")
        return resumo


async def emitir_atestado_matricula_flow(
    enviar_drive: bool = False,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> AtestadoResumo:
    """Emit Atestado de Matrícula (regular or supplemental), render PDF via CDP, and parse classes."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 4, "Solicitando Atestado de Matrícula no Portal do Discente...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )

        await invoke_portal_menu(
            page, "portalDiscente.atestadoMatricula", expect_navigation=True, ctx=ctx, session=mgr
        )
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        err_el = soup.select_one("#painel-erros, ul.erros")

        if err_el or soup.select_one("table#matriculas") is None:
            logger.info("Tentando fallback Atestado de Matrícula em Período Suplementar...")
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            await invoke_portal_menu(
                page,
                "portalDiscente.atestadoMatriculaPeriodoSuplementar",
                expect_navigation=True,
                ctx=ctx,
                session=mgr,
            )
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            err_el = soup.select_one("#painel-erros, ul.erros")
            if err_el and soup.select_one("table#matriculas") is None:
                err_txt = clean_ws(err_el.get_text(" ", strip=True))
                raise RuntimeError(f"SIGAA não permitiu emitir Atestado de Matrícula: {err_txt}")

        await _report(ctx, 2, 4, "Extraindo disciplinas matriculadas e código de autenticidade...")
        resumo = parse_atestado_html(html)
        if not resumo.matricula and mgr.perfil_atual.matricula:
            resumo.matricula = mgr.perfil_atual.matricula
        if not resumo.nome and mgr.perfil_atual.nome:
            resumo.nome = mgr.perfil_atual.nome
        if not resumo.curso and mgr.perfil_atual.curso:
            resumo.curso = mgr.perfil_atual.curso

        await _report(ctx, 3, 4, "Gerando PDF oficial do Atestado de Matrícula...")
        safe_mat = re.sub(r"\W+", "", resumo.matricula or mgr.username or "discente")
        safe_sem = re.sub(r"[^\d.]", "", resumo.semestre or "atual")
        pdf_path = settings.download_dir / f"atestado_matricula_{safe_mat}_{safe_sem}.pdf"
        await mgr.print_current_page_to_pdf(pdf_path)
        resumo.arquivo_pdf = str(pdf_path.resolve())
        resumo.drive_link = _maybe_upload_to_drive(str(pdf_path), "application/pdf", enviar_drive)

        # Return cleanly to Portal do Discente for subsequent operations
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        await _report(ctx, 4, 4, "Atestado de Matrícula emitido com sucesso.")
        return resumo


async def consultar_notas_frequencia_flow(
    semestre: Optional[str] = None,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[NotaDisciplina]:
    """Query 'Consultar Minhas Notas' and return structured grade/attendance records."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 3, "Acessando boletim oficial 'Consultar Minhas Notas'...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        await invoke_portal_menu(
            page, "relatorioNotasAluno.gerarRelatorio", expect_navigation=True, ctx=ctx, session=mgr
        )
        html = await page.content()
        notas = parse_minhas_notas_html(html)

        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )

        if semestre and semestre.strip():
            alvo = semestre.strip()
            notas = [n for n in notas if n.semestre == alvo]

        await _report(ctx, 3, 3, f"{len(notas)} registros de notas/frequência extraídos.")
        return notas
