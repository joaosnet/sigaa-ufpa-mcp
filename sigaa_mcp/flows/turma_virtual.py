"""Read the content of SIGAA Turmas Virtuais (AVA): tópicos de aula, notícias, arquivos, referências,
avaliações, tarefas and questionários.

Turmas are always resolved through 'Todas as Turmas Virtuais' (``/sigaa/portais/discente/turmas.jsf``)
instead of the Portal do Discente card, which shows "Nenhuma turma neste semestre" outside the
enrollment window and made the old notice/activity scans silently return zero items.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from loguru import logger
from playwright.async_api import Page

from sigaa_mcp.auth import ensure_authenticated_portal
from sigaa_mcp.config import settings
from sigaa_mcp.flows.academico import _report
from sigaa_mcp.flows.frequencia import _TODAS_TURMAS_PATH, _abrir_turma_virtual
from sigaa_mcp.flows.turmas import _click_ava_menu_item
from sigaa_mcp.parsers import (
    normalize_text,
    parse_ava_atividades_html,
    parse_ava_noticias_html,
    parse_todas_turmas_html,
)
from sigaa_mcp.parsers_ava import (
    parse_ava_arquivos_html,
    parse_ava_noticia_view_html,
    parse_ava_referencias_html,
    parse_ava_topicos_html,
    parse_ava_ultima_noticia_html,
)
from sigaa_mcp.schemas import AtividadePendente, AvisoTurma, ConteudoTurmaVirtual, TurmaHistorica
from sigaa_mcp.session import SigaaSessionManager, session_manager

_PORTAL_PATH = "/sigaa/verPortalDiscente.do"

SECOES_TURMA = ("topicos", "noticias", "arquivos", "referencias", "avaliacoes", "tarefas", "questionarios")
_MENU = {
    "noticias": ("notícias", "noticias"),
    "arquivos": ("arquivos",),
    "referencias": ("referências", "referencias"),
    "avaliacoes": ("avaliações", "avaliacoes"),
    "tarefas": ("tarefas",),
    "questionarios": ("questionários", "questionarios"),
}
_TIPO_ATIVIDADE = {"avaliacoes": "Avaliação", "tarefas": "Tarefa", "questionarios": "Questionário"}


def selecionar_turmas(
    todas: list[TurmaHistorica],
    disciplina: Optional[str] = None,
    semestre: Optional[str] = None,
) -> list[TurmaHistorica]:
    """Pick turmas by discipline/semester.

    - ``semestre`` = 'AAAA.P' → that semester; 'todos' → every semester.
    - no ``semestre`` → most recent semester among the matches (so 'Circuitos' taken 3× → the latest one).
    """
    filtro = normalize_text(disciplina) if disciplina else ""
    candidatas = [
        t
        for t in todas
        if not filtro or filtro in normalize_text(t.disciplina) or filtro == normalize_text(t.codigo)
    ]
    sem = (semestre or "").strip()
    if sem.lower() in {"todos", "todas", "all", "*"}:
        return candidatas
    if sem:
        return [t for t in candidatas if t.semestre == sem]
    semestres = [t.semestre for t in candidatas if t.semestre]
    if not semestres:
        return candidatas
    ultimo = max(semestres)
    return [t for t in candidatas if t.semestre == ultimo]


async def carregar_todas_turmas_unlocked(page: Page) -> list[TurmaHistorica]:
    await page.goto(
        f"{settings.base_url}{_TODAS_TURMAS_PATH}",
        wait_until="domcontentloaded",
        timeout=settings.browser_timeout_ms,
    )
    return parse_todas_turmas_html(await page.content())


async def _ir_para_secao(page: Page, turma: TurmaHistorica, secao: str) -> bool:
    """Click an AVA left-menu entry; reopen the turma once if the menu is gone."""
    for attempt in range(2):
        for kw in _MENU[secao]:
            if await _click_ava_menu_item(page, kw):
                return True
        if attempt == 0 and not await _abrir_turma_virtual(page, turma.front_end_id):
            return False
    return False


async def _ler_noticias_unlocked(
    page: Page,
    turma: TurmaHistorica,
    limite: int,
    ler_texto: bool,
) -> list[AvisoTurma]:
    noticias = parse_ava_noticias_html(await page.content(), disciplina=turma.disciplina, semestre=turma.semestre)
    noticias = noticias[: max(0, limite)]
    if not ler_texto:
        for n in noticias:
            n.conteudo = ""
        return noticias
    for idx, noticia in enumerate(noticias):
        try:
            if idx > 0 and not await _ir_para_secao(page, turma, "noticias"):
                break
            links = page.locator("table.listing a:has(img[title='Visualizar'])")
            if idx >= await links.count():
                break
            async with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.browser_timeout_ms):
                await links.nth(idx).click()
            titulo, data, texto = parse_ava_noticia_view_html(await page.content())
            noticia.conteudo = texto or noticia.conteudo
            if data:
                noticia.data = data
            if titulo:
                noticia.titulo = titulo
        except Exception as exc:
            logger.debug(f"Não foi possível abrir a notícia '{noticia.titulo}': {exc}")
            noticia.conteudo = ""
    return noticias


async def ler_turma_unlocked(
    page: Page,
    turma: TurmaHistorica,
    secoes: Iterable[str] = SECOES_TURMA,
    limite_noticias: int = 5,
    ler_texto_noticias: bool = True,
) -> ConteudoTurmaVirtual:
    """Read the requested sections of one turma virtual. Caller holds ``session.lock``."""
    conteudo = ConteudoTurmaVirtual(
        semestre=turma.semestre, codigo=turma.codigo, disciplina=turma.disciplina, turma=turma.turma
    )
    if not await _abrir_turma_virtual(page, turma.front_end_id):
        conteudo.erros.append("Turma virtual não encontrada em 'Todas as Turmas'.")
        return conteudo

    principal_html = await page.content()
    conteudo.ultima_noticia = parse_ava_ultima_noticia_html(
        principal_html, disciplina=turma.disciplina, semestre=turma.semestre
    )
    secoes = [s for s in secoes if s in SECOES_TURMA]
    if "topicos" in secoes:
        conteudo.topicos = parse_ava_topicos_html(principal_html)
        conteudo.secoes_lidas.append("topicos")

    for secao in secoes:
        if secao == "topicos":
            continue
        try:
            if not await _ir_para_secao(page, turma, secao):
                conteudo.erros.append(f"Seção '{secao}' indisponível nesta turma.")
                continue
            html = await page.content()
            if secao == "noticias":
                conteudo.noticias = await _ler_noticias_unlocked(page, turma, limite_noticias, ler_texto_noticias)
            elif secao == "arquivos":
                conteudo.arquivos = parse_ava_arquivos_html(html)
            elif secao == "referencias":
                conteudo.referencias = parse_ava_referencias_html(html)
            else:
                itens = parse_ava_atividades_html(html, disciplina=turma.disciplina, tipo=_TIPO_ATIVIDADE[secao])
                for it in itens:
                    it.semestre = turma.semestre
                setattr(conteudo, secao, itens)
            conteudo.secoes_lidas.append(secao)
        except Exception as exc:
            logger.warning(f"Falha ao ler '{secao}' de {turma.disciplina}: {exc}")
            conteudo.erros.append(f"{secao}: {str(exc)[:160]}")
    return conteudo


async def ler_turmas_virtuais_flow(
    disciplina: Optional[str] = None,
    semestre: Optional[str] = None,
    secoes: Optional[list[str]] = None,
    limite_noticias: int = 5,
    ler_texto_noticias: bool = True,
    limite_turmas: int = 10,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> list[ConteudoTurmaVirtual]:
    """Read tópicos, notícias, arquivos, referências, avaliações, tarefas and questionários of turmas virtuais."""
    mgr = session or session_manager
    wanted = [s for s in (secoes or SECOES_TURMA) if s in SECOES_TURMA] or list(SECOES_TURMA)
    async with mgr.lock:
        page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
        selecionadas = selecionar_turmas(await carregar_todas_turmas_unlocked(page), disciplina, semestre)
        selecionadas = selecionadas[: max(1, limite_turmas)]
        resultados: list[ConteudoTurmaVirtual] = []
        for idx, turma in enumerate(selecionadas):
            await _report(ctx, idx + 1, len(selecionadas) + 1, f"Lendo turma virtual {turma.disciplina} ({turma.semestre})...")
            resultados.append(
                await ler_turma_unlocked(
                    page, turma, wanted, limite_noticias=limite_noticias, ler_texto_noticias=ler_texto_noticias
                )
            )
        await page.goto(f"{settings.base_url}{_PORTAL_PATH}", wait_until="domcontentloaded", timeout=settings.browser_timeout_ms)
        return resultados


def _dedup(itens: list, key) -> list:
    seen: set = set()
    out = []
    for it in itens:
        k = key(it)
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out


def consolidar_avisos(
    avisos_portal: list[AvisoTurma], conteudos: list[ConteudoTurmaVirtual], filtro: str = ""
) -> list[AvisoTurma]:
    filtro_norm = normalize_text(filtro) if filtro else ""
    avisos = [a for a in avisos_portal if not filtro_norm or filtro_norm in normalize_text(a.disciplina)]
    for c in conteudos:
        avisos.extend(c.noticias)
        if not c.noticias and c.ultima_noticia is not None:
            avisos.append(c.ultima_noticia)
    return _dedup(avisos, lambda a: (normalize_text(a.disciplina), normalize_text(a.titulo), a.data[:10]))


def consolidar_atividades(
    atividades_portal: list[AtividadePendente], conteudos: list[ConteudoTurmaVirtual]
) -> list[AtividadePendente]:
    todas = list(atividades_portal)
    for c in conteudos:
        todas.extend(c.tarefas + c.questionarios + c.avaliacoes)
    return _dedup(todas, lambda a: (normalize_text(a.disciplina), normalize_text(a.tipo), normalize_text(a.titulo)))
