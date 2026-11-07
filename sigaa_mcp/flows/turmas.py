"""Class schedule CSV export, AVA notices, pending tasks, and offered classes search flows."""

from __future__ import annotations

import re
from typing import Any, Optional

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Page

from sigaa_mcp.auth import ensure_authenticated_portal, invoke_portal_menu
from sigaa_mcp.config import settings
from sigaa_mcp.flows.academico import _maybe_upload_to_drive, _report
from sigaa_mcp.parsers import (
    build_schedule_csv,
    clean_ws,
    detect_schedule_conflicts,
    normalize_text,
    parse_atestado_html,
    parse_ava_atividades_html,
    parse_ava_noticias_html,
    parse_portal_discente,
    parse_turmas_ofertadas_html,
)
from sigaa_mcp.schemas import (
    AtividadePendente,
    AvisoTurma,
    DisciplinaOfertada,
    HorariosExportadosResumo,
    TurmaMatriculada,
)
from sigaa_mcp.session import AuthenticationRequiredError, SigaaSessionManager, session_manager


async def _click_ava_menu_item(page: Page, keyword: str) -> bool:
    """Trigger a left-menu item inside SIGAA's AVA ('#formMenu') bypassing collapsed RichFaces accordions."""
    js = """(kw) => {
        const root = document.getElementById('formMenu') || document;
        const links = Array.from(root.querySelectorAll('a, div.itemMenu'));
        for (const el of links) {
            const txt = (el.textContent || '').trim().toLowerCase();
            if (txt === kw || txt.includes(kw)) {
                const a = el.tagName.toLowerCase() === 'a' ? el : el.closest('a') || el.querySelector('a');
                if (a) {
                    a.click();
                    return true;
                }
            }
        }
        return false;
    }"""
    try:
        async with page.expect_navigation(wait_until="domcontentloaded", timeout=20000):
            clicked = await page.evaluate(js, keyword.lower())
            if not clicked:
                return False
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        return True
    except Exception as exc:
        logger.debug(f"Menu AVA '{keyword}' não navegou ou indisponível: {exc}")
        return False


async def exportar_horarios_csv_flow(
    enviar_drive: bool = False,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> HorariosExportadosResumo:
    """Decode UFPA weekly schedule codes, check conflicts, and export UTF-8 CSV."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 3, "Lendo turmas e horários matriculados no Portal do Discente...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        portal_html = await page.content()
        perfil, turmas, _, _ = parse_portal_discente(portal_html, base_url=settings.base_url)
        mgr.perfil_atual = perfil

        # Enrich codes/docentes via Atestado de Matrícula if portal rows omit component codes
        if turmas and any(not t.codigo for t in turmas):
            try:
                await invoke_portal_menu(
                    page, "portalDiscente.atestadoMatricula", expect_navigation=True, ctx=ctx, session=mgr
                )
                at_res = parse_atestado_html(await page.content())
                if at_res.turmas:
                    turmas = at_res.turmas
                await page.goto(
                    f"{settings.base_url}/sigaa/verPortalDiscente.do",
                    wait_until="domcontentloaded",
                    timeout=settings.browser_timeout_ms,
                )
            except Exception as exc:
                logger.debug(f"Mantendo turmas do portal sem enriquecimento do atestado: {exc}")

        await _report(ctx, 2, 3, "Decodificando códigos de horário UFPA e gerando CSV...")
        csv_text = build_schedule_csv(turmas)
        semestre = perfil.semestre_atual or (turmas[0].semestre if turmas else "atual")
        safe_sem = re.sub(r"[^\w.]", "_", semestre)
        csv_path = settings.download_dir / f"horarios_{safe_sem}.csv"
        csv_path.write_text(csv_text, encoding="utf-8")

        choques = detect_schedule_conflicts(turmas)
        total_slots = sum(len(t.slots_decodificados) for t in turmas)
        drive_link = _maybe_upload_to_drive(str(csv_path), "text/csv", enviar_drive)

        await _report(ctx, 3, 3, "Grade horária exportada com sucesso.")
        return HorariosExportadosResumo(
            semestre=semestre,
            total_turmas=len(turmas),
            total_slots_semanais=total_slots,
            arquivo_csv=str(csv_path.resolve()),
            drive_link=drive_link,
            turmas=turmas,
            choques_horario=choques,
        )


async def listar_avisos_turmas_flow(
    disciplina_filtro: Optional[str] = None,
    limite_por_turma: int = 5,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[AvisoTurma]:
    """Gather recent class notices from Portal do Discente and each enrolled Turma Virtual (AVA)."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 4, "Coletando últimas atualizações do Portal do Discente...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        portal_html = await page.content()
        perfil, turmas, avisos_portal, _ = parse_portal_discente(portal_html, base_url=settings.base_url)
        mgr.perfil_atual = perfil

        filtro_norm = normalize_text(disciplina_filtro) if disciplina_filtro else ""
        avisos: list[AvisoTurma] = [
            a for a in avisos_portal if not filtro_norm or filtro_norm in normalize_text(a.disciplina)
        ]
        seen = {(normalize_text(a.disciplina), normalize_text(a.titulo)) for a in avisos}

        total_turmas = len(turmas)
        for idx, turma in enumerate(turmas):
            if filtro_norm and filtro_norm not in normalize_text(turma.disciplina) and filtro_norm not in normalize_text(turma.codigo):
                continue

            await _report(
                ctx,
                2 + (idx / max(total_turmas, 1)),
                4,
                f"Consultando notícias da turma {turma.disciplina}...",
            )
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            links = page.locator("#turmas-portal td.descricao a")
            if idx >= await links.count():
                continue

            try:
                async with page.expect_navigation(
                    wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
                ):
                    await links.nth(idx).click()

                if await _click_ava_menu_item(page, "notícias") or await _click_ava_menu_item(page, "noticias"):
                    ava_avisos = parse_ava_noticias_html(
                        await page.content(),
                        disciplina=turma.disciplina,
                        semestre=turma.semestre or perfil.semestre_atual,
                    )
                    for av in ava_avisos[: max(1, limite_por_turma)]:
                        key = (normalize_text(av.disciplina), normalize_text(av.titulo))
                        if key not in seen:
                            seen.add(key)
                            avisos.append(av)
            except Exception as exc:
                logger.warning(f"Não foi possível ler notícias da turma '{turma.disciplina}': {exc}")

        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        await _report(ctx, 4, 4, f"{len(avisos)} avisos/notícias consolidados.")
        return avisos


async def listar_atividades_pendentes_flow(
    incluir_concluidas: bool = False,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[AtividadePendente]:
    """Scan Portal do Discente and enrolled AVA rooms for tasks, quizzes, and scheduled exams."""
    mgr = session or session_manager
    async with mgr.lock:
        await _report(ctx, 1, 4, "Verificando painel 'Minhas Atividades' no Portal do Discente...")
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        portal_html = await page.content()
        perfil, turmas, _, atividades_portal = parse_portal_discente(portal_html, base_url=settings.base_url)
        mgr.perfil_atual = perfil

        todas: list[AtividadePendente] = list(atividades_portal)
        seen = {(normalize_text(a.disciplina), normalize_text(a.titulo)) for a in todas}

        for idx, turma in enumerate(turmas):
            await _report(
                ctx,
                2 + (idx / max(len(turmas), 1)),
                4,
                f"Inspecionando tarefas, questionários e avaliações em {turma.disciplina}...",
            )
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            links = page.locator("#turmas-portal td.descricao a")
            if idx >= await links.count():
                continue

            try:
                async with page.expect_navigation(
                    wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
                ):
                    await links.nth(idx).click()

                for kw, label in (
                    ("tarefas", "Tarefa"),
                    ("questionários", "Questionário"),
                    ("avaliações", "Avaliação"),
                ):
                    if await _click_ava_menu_item(page, kw):
                        items = parse_ava_atividades_html(
                            await page.content(), disciplina=turma.disciplina, tipo=label
                        )
                        for it in items:
                            key = (normalize_text(it.disciplina), normalize_text(it.titulo))
                            if key not in seen:
                                seen.add(key)
                                todas.append(it)
            except Exception as exc:
                logger.warning(f"Falha parcial ao inspecionar atividades em '{turma.disciplina}': {exc}")

        await page.goto(
            f"{settings.base_url}/sigaa/verPortalDiscente.do",
            wait_until="domcontentloaded",
            timeout=settings.browser_timeout_ms,
        )
        if not incluir_concluidas:
            todas = [a for a in todas if not a.concluida]

        await _report(ctx, 4, 4, f"{len(todas)} atividades encontradas.")
        return todas


def _match_select_option(html: str, select_id: str, query: str) -> Optional[tuple[str, str]]:
    """Find best <option value='...'> inside a JSF <select> matching query without accents."""
    soup = BeautifulSoup(html, "lxml")
    sel = soup.find("select", id=select_id)
    if not sel:
        return None
    q_norm = normalize_text(query)
    q_tokens = [t for t in q_norm.split() if len(t) > 2]

    best: Optional[tuple[int, str, str]] = None
    for opt in sel.find_all("option"):
        val = (opt.get("value") or "").strip()
        label = clean_ws(opt.get_text(" ", strip=True))
        if not val or val in {"0", "-1"} or "SELECIONE" in label.upper():
            continue
        lbl_norm = normalize_text(label)
        score = 0
        if q_norm == lbl_norm:
            score = 100
        elif q_norm in lbl_norm:
            score = 80 + (20 if "BELEM" in lbl_norm else 0)
        elif q_tokens and all(tok in lbl_norm for tok in q_tokens):
            score = 60 + (15 if "BELEM" in lbl_norm else 0)
        if score > 0 and (best is None or score > best[0]):
            best = (score, val, label)

    return (best[1], best[2]) if best else None


async def listar_disciplinas_ofertadas_flow(
    curso_ou_unidade: str,
    turno: Optional[str] = None,
    ano: Optional[int] = None,
    periodo: Optional[int] = None,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[DisciplinaOfertada]:
    """Search offered classes in SIGAA UFPA and automatically detect schedule conflicts with current enrollment."""
    mgr = session or session_manager
    termo = curso_ou_unidade.strip()
    if not termo:
        raise ValueError("Informe o nome do curso ou faculdade/instituto (ex.: 'Engenharia da Computação').")

    turno_code = ""
    if turno and turno.strip():
        t_up = normalize_text(turno)
        if t_up.startswith("M") or "MANHA" in t_up or "MATUTINO" in t_up:
            turno_code = "M"
        elif t_up.startswith("T") or "TARDE" in t_up or "VESPERTINO" in t_up:
            turno_code = "T"
        elif t_up.startswith("N") or "NOITE" in t_up or "NOTURNO" in t_up:
            turno_code = "N"
        else:
            turno_code = turno.strip().upper()

    async with mgr.lock:
        enrolled_turmas: list[TurmaMatriculada] = []
        can_use_internal = False
        page = await mgr.ensure_browser_page()

        try:
            await _report(ctx, 1, 3, f"Preparando busca de turmas ofertadas para '{termo}'...")
            page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
            portal_html = await page.content()
            _, enrolled_turmas, _, _ = parse_portal_discente(portal_html, base_url=settings.base_url)
            can_use_internal = True
        except AuthenticationRequiredError:
            can_use_internal = False

        if can_use_internal:
            await invoke_portal_menu(
                page, "buscaTurmaBean.popularBuscaGeral", expect_navigation=True, ctx=ctx, session=mgr
            )
            form_html = await page.content()
            matched_curso = _match_select_option(form_html, "form:selectCurso", termo)
            matched_unid = (
                None if matched_curso else _match_select_option(form_html, "form:selectUnidade", termo)
            )

            if not matched_curso and not matched_unid:
                raise ValueError(
                    f"Curso ou unidade '{termo}' não encontrado na lista oficial do SIGAA UFPA."
                )

            if ano is not None or periodo is not None:
                chk_ap = page.locator("#form\\:checkAnoPeriodo")
                if await chk_ap.count() > 0 and not await chk_ap.is_checked():
                    await chk_ap.check()
                if ano is not None:
                    await page.locator("#form\\:inputAno").fill(str(ano))
                if periodo is not None:
                    await page.locator("#form\\:inputPeriodo").fill(str(periodo))

            if matched_curso:
                chk_c = page.locator("#form\\:checkCurso")
                if not await chk_c.is_checked():
                    await chk_c.check()
                await page.locator("#form\\:selectCurso").select_option(value=matched_curso[0])
            elif matched_unid:
                chk_u = page.locator("#form\\:checkUnidade")
                if not await chk_u.is_checked():
                    await chk_u.check()
                await page.locator("#form\\:selectUnidade").select_option(value=matched_unid[0])

            if turno_code and len(turno_code) > 1:
                chk_h = page.locator("#form\\:checkHorario")
                if not await chk_h.is_checked():
                    await chk_h.check()
                await page.locator("#form\\:inputHorario").fill(turno_code)

            await _report(ctx, 2, 3, "Executando consulta de turmas e analisando conflitos de horário...")
            async with page.expect_navigation(
                wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
            ):
                await page.locator("#form\\:buttonBuscar").click()

            res_html = await page.content()
            ofertadas = parse_turmas_ofertadas_html(res_html, enrolled_turmas=enrolled_turmas)

            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
        else:
            # Public fallback when user has not authenticated yet
            await page.goto(
                f"{settings.base_url}/sigaa/public/turmas/listar.jsf?aba=p-ensino",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            pub_html = await page.content()
            matched_depto = _match_select_option(pub_html, "formTurma:inputDepto", termo)
            if not matched_depto:
                raise ValueError(
                    f"Unidade '{termo}' não localizada na consulta pública. Autentique-se no SIGAA para buscar por Curso específico."
                )
            await page.locator("#formTurma\\:inputDepto").select_option(value=matched_depto[0])
            if ano is not None:
                await page.locator("#formTurma\\:inputAno").fill(str(ano))
            if periodo is not None:
                await page.locator("#formTurma\\:inputPeriodo").select_option(value=str(periodo))
            async with page.expect_navigation(
                wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
            ):
                await page.locator("input[type='submit'][value='Buscar']").first.click()
            ofertadas = parse_turmas_ofertadas_html(await page.content(), enrolled_turmas=[])

        if turno_code in {"M", "T", "N"}:
            ofertadas = [
                o
                for o in ofertadas
                if re.search(rf"[1-7]+{turno_code}[1-6]+", o.horario_bruto or "", re.I)
            ]

        await _report(ctx, 3, 3, f"{len(ofertadas)} turmas ofertadas encontradas.")
        return ofertadas
