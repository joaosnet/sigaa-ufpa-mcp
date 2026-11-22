"""Live attendance (turma virtual 'Mapa de Frequências') and cross-semester discipline comparison flows."""

from __future__ import annotations

import re
from typing import Any, Optional

from loguru import logger
from playwright.async_api import Page

from sigaa_mcp.auth import ensure_authenticated_portal, invoke_portal_menu
from sigaa_mcp.config import settings
from sigaa_mcp.flows.academico import _report, consultar_notas_frequencia_flow
from sigaa_mcp.flows.turmas import _click_ava_menu_item
from sigaa_mcp.parsers import (
    normalize_text,
    parse_frequencia_turma_html,
    parse_todas_turmas_html,
    parse_turmas_ofertadas_html,
)
from sigaa_mcp.schemas import (
    ComparativoDisciplina,
    DisciplinaOfertada,
    FrequenciaTurma,
    NotaDisciplina,
    SemestreDisciplinaComparada,
    TurmaHistorica,
)
from sigaa_mcp.session import SigaaSessionManager, session_manager

_TODAS_TURMAS_PATH = "/sigaa/portais/discente/turmas.jsf"
_PORTAL_PATH = "/sigaa/verPortalDiscente.do"
_CODIGO_COMPONENTE_RE = re.compile(r"^[A-Z]{2,}\d{2,}[A-Z0-9]*$")
_SEMESTRE_RE = re.compile(r"^(\d{4})\.(\d)$")


async def _goto(page: Page, path: str) -> None:
    await page.goto(
        f"{settings.base_url}{path}",
        wait_until="domcontentloaded",
        timeout=settings.browser_timeout_ms,
    )


# ---------------------------------------------------------------------------- frequência da turma virtual
async def _abrir_turma_virtual(page: Page, front_end_id: str) -> bool:
    """Enter a turma virtual from 'Todas as Turmas Virtuais' using its JSF frontEndIdTurma."""
    await _goto(page, _TODAS_TURMAS_PATH)
    link = page.locator(f"a[onclick*='{front_end_id}']").first
    if await link.count() == 0:
        return False
    async with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.browser_timeout_ms):
        await link.click()
    return True


async def _ler_frequencias_unlocked(
    page: Page,
    turmas: list[TurmaHistorica],
    ctx: Any = None,
) -> list[FrequenciaTurma]:
    resultados: list[FrequenciaTurma] = []
    for idx, turma in enumerate(turmas):
        await _report(ctx, 1 + idx, len(turmas) + 1, f"Lendo Mapa de Frequências de {turma.disciplina}...")
        base = {
            "semestre": turma.semestre,
            "codigo": turma.codigo,
            "disciplina": turma.disciplina,
            "turma": turma.turma,
        }
        try:
            if not await _abrir_turma_virtual(page, turma.front_end_id):
                resultados.append(FrequenciaTurma(**base, erro="Turma virtual não encontrada."))
                continue
            if not (
                await _click_ava_menu_item(page, "frequência")
                or await _click_ava_menu_item(page, "frequencia")
            ):
                resultados.append(FrequenciaTurma(**base, erro="Menu 'Frequência' indisponível nesta turma."))
                continue
            freq = parse_frequencia_turma_html(await page.content())
            resultados.append(freq.model_copy(update=base))
        except Exception as exc:
            logger.warning(f"Falha ao ler frequência de '{turma.disciplina}': {exc}")
            resultados.append(FrequenciaTurma(**base, erro=str(exc)[:200]))
    return resultados


async def consultar_frequencia_turmas_flow(
    disciplina_filtro: Optional[str] = None,
    semestre: Optional[str] = None,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[FrequenciaTurma]:
    """Read the live 'Mapa de Frequências' of turmas virtuais (default: most recent semester)."""
    mgr = session or session_manager
    async with mgr.lock:
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        await _goto(page, _TODAS_TURMAS_PATH)
        todas = parse_todas_turmas_html(await page.content())
        if not todas:
            return []

        alvo_sem = (semestre or "").strip()
        if not alvo_sem and not disciplina_filtro:
            semestres = [t.semestre for t in todas if t.semestre]
            alvo_sem = max(semestres) if semestres else ""
        filtro = normalize_text(disciplina_filtro) if disciplina_filtro else ""
        selecionadas = [
            t
            for t in todas
            if (not alvo_sem or t.semestre == alvo_sem)
            and (not filtro or filtro in normalize_text(t.disciplina) or filtro == normalize_text(t.codigo))
        ]
        resultados = await _ler_frequencias_unlocked(page, selecionadas, ctx=ctx)
        await _goto(page, _PORTAL_PATH)
        return resultados


def anexar_frequencia_ao_boletim(notas: list[NotaDisciplina], frequencias: list[FrequenciaTurma]) -> None:
    """Attach live turma-virtual attendance to matching boletim rows (same código + semestre)."""
    by_key = {(normalize_text(f.codigo), f.semestre): f for f in frequencias if not f.erro}
    for n in notas:
        f = by_key.get((normalize_text(n.codigo), n.semestre))
        if f is not None:
            n.frequencia_turma = f


# ---------------------------------------------------------------------------- comparativo entre semestres
async def _buscar_turmas_componente_unlocked(
    page: Page,
    ano: int,
    periodo: int,
    codigo: str = "",
    nome: str = "",
    ctx: Any = None,
    mgr: Optional[SigaaSessionManager] = None,
) -> list[DisciplinaOfertada]:
    await _goto(page, _PORTAL_PATH)
    await invoke_portal_menu(page, "buscaTurmaBean.popularBuscaGeral", expect_navigation=True, ctx=ctx, session=mgr)
    chk_ap = page.locator("#form\\:checkAnoPeriodo")
    if not await chk_ap.is_checked():
        await chk_ap.check()
    await page.locator("#form\\:inputAno").fill(str(ano))
    await page.locator("#form\\:inputPeriodo").fill(str(periodo))
    if codigo:
        await page.locator("#form\\:checkCodigo").check()
        await page.locator("#form\\:inputCodDisciplina").fill(codigo)
    else:
        await page.locator("#form\\:checkDisciplina").check()
        await page.locator("#form\\:inputNomeDisciplina").fill(nome)
    async with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.browser_timeout_ms):
        await page.locator("#form\\:buttonBuscar").click()
    return parse_turmas_ofertadas_html(await page.content(), enrolled_turmas=[])


def _to_int(value: str) -> int:
    m = re.search(r"\d+", value or "")
    return int(m.group(0)) if m else 0


def _resolver_disciplina(consulta: str, notas: list[NotaDisciplina]) -> tuple[str, str, list[NotaDisciplina]]:
    """Return (codigo, nome, boletim rows of that discipline) from a name or code query."""
    q_norm = normalize_text(consulta)
    q_code = q_norm.replace(" ", "")
    codigo = q_code if _CODIGO_COMPONENTE_RE.match(q_code) else ""

    if codigo:
        cursadas = [n for n in notas if normalize_text(n.codigo) == codigo]
    else:
        cursadas = [n for n in notas if normalize_text(n.disciplina) == q_norm]
        if not cursadas:
            cursadas = [n for n in notas if q_norm in normalize_text(n.disciplina)]
            if len({n.codigo for n in cursadas}) > 1:
                # Ambiguous substring (e.g. 'CALCULO' → I, II, III): keep the closest (shortest) name.
                menor = min(cursadas, key=lambda n: len(n.disciplina))
                cursadas = [n for n in cursadas if n.codigo == menor.codigo]
        if cursadas:
            codigo = normalize_text(cursadas[0].codigo)
    nome = cursadas[0].disciplina if cursadas else consulta.strip()
    return codigo, nome, cursadas


async def comparar_disciplina_semestres_flow(
    disciplina: str,
    semestres: Optional[list[str]] = None,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> ComparativoDisciplina:
    """Compare one componente curricular across semesters: UFPA offer + the student's own result."""
    mgr = session or session_manager
    consulta = disciplina.strip()
    if not consulta:
        raise ValueError("Informe o nome ou código da disciplina (ex.: 'Cálculo I' ou 'NITAE005').")

    notas = await consultar_notas_frequencia_flow(ctx=ctx, session=mgr)
    codigo, nome, cursadas = _resolver_disciplina(consulta, notas)
    sem_cursados = sorted({n.semestre for n in cursadas if n.semestre})

    if semestres:
        alvo = {s.strip() for s in semestres if s and s.strip()}
    else:
        recentes = sorted({n.semestre for n in notas if n.semestre}, reverse=True)[:4]
        alvo = set(sem_cursados) | set(recentes)
    alvo_ordenado = sorted(alvo)

    resultado = ComparativoDisciplina(
        consulta=consulta, codigo=codigo, disciplina=nome, semestres_cursados=sem_cursados
    )
    if not alvo_ordenado:
        resultado.observacoes.append("Nenhum semestre informado ou encontrado no boletim para comparar.")
        return resultado

    async with mgr.lock:
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        for idx, sem in enumerate(alvo_ordenado):
            await _report(ctx, 1 + idx, len(alvo_ordenado) + 1, f"Consultando oferta de {nome} em {sem}...")
            item = SemestreDisciplinaComparada(semestre=sem)
            nota = next((n for n in cursadas if n.semestre == sem), None)
            if nota is not None:
                item.cursada = True
                item.resultado_aluno = nota
            m = _SEMESTRE_RE.match(sem)
            if not m:
                item.erro = "Semestre deve estar no formato AAAA.P (ex.: 2025.2)."
                resultado.semestres.append(item)
                continue
            try:
                ofertadas = await _buscar_turmas_componente_unlocked(
                    page, int(m.group(1)), int(m.group(2)), codigo=codigo, nome=nome, ctx=ctx, mgr=mgr
                )
                if codigo:
                    ofertadas = [o for o in ofertadas if not o.codigo or normalize_text(o.codigo) == codigo]
                item.turmas_ofertadas = ofertadas
                item.docentes = sorted(
                    {re.sub(r"\s*\(\d+h\)", "", o.docente).strip() for o in ofertadas if o.docente}
                )
                item.horarios = [o.horario_bruto for o in ofertadas if o.horario_bruto]
                item.vagas_ofertadas = sum(_to_int(o.vagas_ofertadas) for o in ofertadas)
                item.vagas_ocupadas = sum(_to_int(o.vagas_ocupadas) for o in ofertadas)
                if item.vagas_ofertadas:
                    item.taxa_ocupacao = round(item.vagas_ocupadas / item.vagas_ofertadas, 3)
                if not ofertadas:
                    item.erro = "Nenhuma turma ofertada encontrada neste semestre."
            except Exception as exc:
                logger.warning(f"Falha ao consultar oferta de '{nome}' em {sem}: {exc}")
                item.erro = str(exc)[:200]
            resultado.semestres.append(item)
        await _goto(page, _PORTAL_PATH)

    for item in resultado.semestres:
        for d in item.docentes:
            if d not in resultado.docentes_distintos:
                resultado.docentes_distintos.append(d)
    if not cursadas:
        resultado.observacoes.append("Você ainda não cursou esta disciplina (não consta no boletim).")
    elif len(cursadas) > 1:
        resultado.observacoes.append(
            f"Disciplina cursada {len(cursadas)} vezes: "
            + ", ".join(f"{n.semestre} ({n.situacao}, conceito {n.resultado})" for n in cursadas)
        )
    return resultado
