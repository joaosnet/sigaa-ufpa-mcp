"""Parsers for the SIGAA Turma Virtual (AVA): tópicos de aula, notícias, arquivos and referências."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Optional

from bs4 import BeautifulSoup, Tag

from sigaa_mcp.parsers import clean_ws, normalize_text
from sigaa_mcp.schemas import ArquivoTurma, AvisoTurma, MaterialTopico, ReferenciaTurma, TopicoAula

_PERIODO_RE = re.compile(r"\((\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})\)")
_DATA_HORA_RE = re.compile(r"(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)")
_VAZIO_MARKERS = ("NENHUM ITEM FOI ENCONTRADO", "NENHUMA NOTICIA", "NENHUM FORUM")


def _root(html: str) -> Tag:
    soup = BeautifulSoup(html, "lxml")
    root = soup.find(id="conteudo") or soup.body or soup
    for junk in root.select("#formMenu, script, style"):
        junk.decompose()
    return root


def _text(el: Optional[Tag]) -> str:
    return clean_ws(el.get_text(" ", strip=True)) if el is not None else ""


def _data_rows(root: Tag) -> list[list[Tag]]:
    """Return <td> lists for every data row of every 'table.listing' (header rows skipped)."""
    rows: list[list[Tag]] = []
    for tbl in root.select("table.listing"):
        for tr in tbl.find_all("tr"):
            tds = tr.find_all("td", recursive=False) or tr.find_all("td")
            if tds:
                rows.append(tds)
    return rows


def ava_secao_vazia(html: str) -> bool:
    """True when the AVA section explicitly reports it has no items."""
    txt = normalize_text(_text(_root(html)))
    return any(m in txt for m in _VAZIO_MARKERS)


def parse_ava_topicos_html(html: str) -> list[TopicoAula]:
    """Parse 'div.topico-aula' blocks from the turma virtual main page."""
    root = _root(html)
    topicos: list[TopicoAula] = []
    for blk in root.select("div.topico-aula"):
        titulo_el = blk.select_one("div.titulo")
        titulo_raw = _text(titulo_el)
        m = _PERIODO_RE.search(titulo_raw)
        periodo = clean_ws(m.group(1)) if m else ""
        titulo = clean_ws(_PERIODO_RE.sub("", titulo_raw)) if m else titulo_raw

        materiais: list[MaterialTopico] = []
        conteudo_el = blk.select_one("div.conteudotopico")
        if conteudo_el is not None:
            for item in conteudo_el.select("div.item"):
                nome = _text(item.find("a")) or _text(item.find("span"))
                if not nome:
                    continue
                img = item.find("img")
                tipo = PurePosixPath(img.get("src", "")).stem if img is not None else ""
                desc = _text(item.select_one("div.descricao-item"))
                materiais.append(MaterialTopico(nome=nome, tipo=tipo, descricao=desc))
                item.decompose()
            for junk in conteudo_el.select("div.drag_indicator, div.drgind_fly"):
                junk.decompose()
        conteudo = _text(conteudo_el)
        if titulo or conteudo or materiais:
            topicos.append(TopicoAula(titulo=titulo, periodo=periodo, conteudo=conteudo, materiais=materiais))
    return topicos


def parse_ava_ultima_noticia_html(html: str, disciplina: str = "", semestre: str = "") -> Optional[AvisoTurma]:
    """Parse the 'Última Notícia' box (div#ultimaNoticia) on the turma virtual main page."""
    root = _root(html)
    box = root.find(id="ultimaNoticia")
    if box is None:
        return None
    h4 = box.find("h4")
    cabecalho = re.sub(r"(?i)^\s*última notícia\s*", "", _text(h4))
    data = ""
    m = re.search(r"\s+-\s+" + _DATA_HORA_RE.pattern + r"\s*$", cabecalho)
    if m:
        data = m.group(1)
        cabecalho = cabecalho[: m.start()]
    if h4 is not None:
        h4.decompose()
    autor_el = box.find("small")
    if autor_el is not None:
        autor_el.decompose()
    corpo = _text(box)
    if not cabecalho and not corpo:
        return None
    return AvisoTurma(
        disciplina=disciplina,
        semestre=semestre,
        data=data,
        titulo=clean_ws(cabecalho) or "Última notícia",
        conteudo=corpo,
        origem="ava_ultima_noticia",
    )


def parse_ava_noticia_view_html(html: str) -> tuple[str, str, str]:
    """Parse 'Visualização de Notícia' → (titulo, data, texto)."""
    root = _root(html)
    titulo = data = texto = ""
    for th in root.find_all("th"):
        label = normalize_text(_text(th)).rstrip(":").strip()
        td = th.find_next_sibling("td")
        if td is None:
            continue
        if label == "TITULO":
            titulo = _text(td)
        elif label == "DATA":
            data = _text(td)
        elif label == "TEXTO":
            texto = _text(td)
    if not (titulo and data and texto):
        full = _text(root)
        m = re.search(r"Título:\s*(.*?)\s*Data:\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)\s*(?:Texto:\s*(.*))?$", full)
        if m:
            titulo = titulo or clean_ws(m.group(1))
            data = data or m.group(2)
            texto = texto or clean_ws(m.group(3) or "")
    return titulo, data, texto


def parse_ava_arquivos_html(html: str) -> list[ArquivoTurma]:
    """Parse 'Arquivos' listing (Título | Descrição | Tópico de Aula)."""
    out: list[ArquivoTurma] = []
    for tds in _data_rows(_root(html)):
        cells = [_text(td) for td in tds]
        if not cells or not cells[0]:
            continue
        out.append(
            ArquivoTurma(
                titulo=cells[0],
                descricao=cells[1] if len(cells) > 1 else "",
                topico=cells[2] if len(cells) > 2 else "",
            )
        )
    return out


def parse_ava_referencias_html(html: str) -> list[ReferenciaTurma]:
    """Parse 'Referências' listing (Nome | Tipo | URL | Tópico de Aula)."""
    out: list[ReferenciaTurma] = []
    for tds in _data_rows(_root(html)):
        cells = [_text(td) for td in tds]
        if not cells or not cells[0]:
            continue
        url = ""
        if len(tds) > 2:
            a = tds[2].find("a", href=True)
            href = (a.get("href") or "").strip() if a is not None else ""
            if href and href not in {"http://", "https://", "#"}:
                url = href
        out.append(
            ReferenciaTurma(
                nome=cells[0],
                tipo=cells[1] if len(cells) > 1 else "",
                url=url,
                topico=cells[3] if len(cells) > 3 else "",
            )
        )
    return out
