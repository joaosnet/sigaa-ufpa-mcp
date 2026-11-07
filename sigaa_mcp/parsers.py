"""Deterministic HTML (BeautifulSoup4/lxml), PDF (pypdf 7), and UFPA schedule parsers."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Optional

from bs4 import BeautifulSoup
from pypdf import PdfReader

from sigaa_mcp.schemas import (
    AtestadoResumo,
    AtividadePendente,
    AvisoTurma,
    CargaHorariaItem,
    ChoqueHorario,
    DisciplinaOfertada,
    HistoricoResumo,
    NotaDisciplina,
    PerfilDiscenteResumo,
    SlotHorario,
    TurmaMatriculada,
    VinculoItem,
)

DIAS_UFPA: dict[str, str] = {
    "1": "Domingo",
    "2": "Segunda-feira",
    "3": "Terça-feira",
    "4": "Quarta-feira",
    "5": "Quinta-feira",
    "6": "Sexta-feira",
    "7": "Sábado",
}

TURNOS_UFPA: dict[str, str] = {
    "M": "Manhã",
    "T": "Tarde",
    "N": "Noite",
}

FAIXAS_HORARIAS_UFPA: dict[tuple[str, int], tuple[str, str]] = {
    ("M", 1): ("07:30", "08:20"),
    ("M", 2): ("08:20", "09:10"),
    ("M", 3): ("09:20", "10:10"),
    ("M", 4): ("10:10", "11:00"),
    ("M", 5): ("11:10", "12:00"),
    ("M", 6): ("12:00", "12:50"),
    ("T", 1): ("13:00", "13:50"),
    ("T", 2): ("13:50", "14:40"),
    ("T", 3): ("14:50", "15:40"),
    ("T", 4): ("15:40", "16:30"),
    ("T", 5): ("16:40", "17:30"),
    ("T", 6): ("17:30", "18:20"),
    ("N", 1): ("18:30", "19:20"),
    ("N", 2): ("19:20", "20:10"),
    ("N", 3): ("20:10", "21:00"),
    ("N", 4): ("21:00", "21:50"),
}

_SCHEDULE_TOKEN_RE = re.compile(r"\b([1-7]+)([MTN])([1-6]+)\b", re.IGNORECASE)
_DATE_RANGE_RE = re.compile(r"\((\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})\)")


def normalize_text(value: str) -> str:
    """Collapse whitespace and strip accents for resilient fuzzy matching."""
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    nfkd = unicodedata.normalize("NFKD", cleaned)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).upper()


def clean_ws(value: str) -> str:
    """Collapse whitespace while preserving UTF-8 accents."""
    return re.sub(r"\s+", " ", value or "").strip()


def decode_ufpa_schedule(raw_schedule: str) -> tuple[list[SlotHorario], str]:
    """Decode UFPA schedule codes like '24M56 (24/08/2026 - 23/12/2026)' into individual slots."""
    if not raw_schedule:
        return [], ""

    date_match = _DATE_RANGE_RE.search(raw_schedule)
    periodo_datas = clean_ws(date_match.group(1)) if date_match else ""
    without_dates = _DATE_RANGE_RE.sub("", raw_schedule)

    slots: list[SlotHorario] = []
    seen: set[tuple[str, str, int]] = set()

    for match in _SCHEDULE_TOKEN_RE.finditer(without_dates):
        days_str, shift_raw, nums_str = match.groups()
        shift = shift_raw.upper()
        token_str = match.group(0).upper()
        for day_code in days_str:
            dia_nome = DIAS_UFPA.get(day_code, f"Dia {day_code}")
            turno_nome = TURNOS_UFPA.get(shift, shift)
            for num_ch in nums_str:
                slot_num = int(num_ch)
                key = (day_code, shift, slot_num)
                if key in seen:
                    continue
                seen.add(key)
                inicio, fim = FAIXAS_HORARIAS_UFPA.get((shift, slot_num), ("--:--", "--:--"))
                slots.append(
                    SlotHorario(
                        dia_codigo=day_code,
                        dia_nome=dia_nome,
                        turno_codigo=shift,
                        turno_nome=turno_nome,
                        slot_numero=slot_num,
                        hora_inicio=inicio,
                        hora_fim=fim,
                        codigo_original=token_str,
                    )
                )

    slots.sort(key=lambda s: (int(s.dia_codigo), {"M": 1, "T": 2, "N": 3}.get(s.turno_codigo, 9), s.slot_numero))
    return slots, periodo_datas


def detect_schedule_conflicts(turmas: Iterable[TurmaMatriculada]) -> list[ChoqueHorario]:
    """Identify overlapping classes in the same weekday, shift, and 50-minute UFPA slot."""
    grid: dict[tuple[str, str, int], list[str]] = {}
    meta: dict[tuple[str, str, int], SlotHorario] = {}

    for turma in turmas:
        slots = turma.slots_decodificados
        if not slots and turma.horario_bruto:
            slots, _ = decode_ufpa_schedule(turma.horario_bruto)
        label = f"{turma.codigo} - {turma.disciplina}".strip(" -")
        for slot in slots:
            key = (slot.dia_codigo, slot.turno_codigo, slot.slot_numero)
            meta[key] = slot
            bucket = grid.setdefault(key, [])
            if label not in bucket:
                bucket.append(label)

    conflicts: list[ChoqueHorario] = []
    for key in sorted(grid.keys(), key=lambda k: (int(k[0]), {"M": 1, "T": 2, "N": 3}.get(k[1], 9), k[2])):
        disciplinas = grid[key]
        if len(disciplinas) > 1:
            slot = meta[key]
            conflicts.append(
                ChoqueHorario(
                    dia_nome=slot.dia_nome,
                    turno_nome=slot.turno_nome,
                    slot_numero=slot.slot_numero,
                    faixa_horaria=f"{slot.hora_inicio}-{slot.hora_fim}",
                    disciplinas=disciplinas,
                )
            )
    return conflicts


def check_candidate_conflict(
    candidate_horario: str, enrolled_turmas: Iterable[TurmaMatriculada]
) -> tuple[bool, list[str]]:
    """Check whether a candidate offered class collides with the student's current schedule."""
    cand_slots, _ = decode_ufpa_schedule(candidate_horario)
    if not cand_slots:
        return False, []

    occupied: dict[tuple[str, str, int], list[str]] = {}
    for turma in enrolled_turmas:
        slots = turma.slots_decodificados or decode_ufpa_schedule(turma.horario_bruto)[0]
        label = f"{turma.codigo} {turma.disciplina}".strip()
        for slot in slots:
            occupied.setdefault((slot.dia_codigo, slot.turno_codigo, slot.slot_numero), []).append(label)

    details: list[str] = []
    for cslot in cand_slots:
        key = (cslot.dia_codigo, cslot.turno_codigo, cslot.slot_numero)
        if key in occupied:
            owners = ", ".join(occupied[key])
            msg = f"{cslot.dia_nome} {cslot.hora_inicio}-{cslot.hora_fim} ({cslot.turno_codigo}{cslot.slot_numero}) com {owners}"
            if msg not in details:
                details.append(msg)

    return bool(details), details


def build_schedule_csv(turmas: Iterable[TurmaMatriculada]) -> str:
    """Serialize enrolled classes and decoded weekly slots into UTF-8 CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "Semestre",
            "Codigo",
            "Disciplina",
            "Turma",
            "Local",
            "Dia_Semana",
            "Turno",
            "Horario_Inicio",
            "Horario_Fim",
            "Codigo_SIGAA",
            "Periodo_Letivo",
        ]
    )
    for turma in turmas:
        slots = turma.slots_decodificados
        periodo_datas = turma.periodo_datas
        if not slots and turma.horario_bruto:
            slots, detected_dates = decode_ufpa_schedule(turma.horario_bruto)
            periodo_datas = periodo_datas or detected_dates

        if not slots:
            writer.writerow(
                [
                    turma.semestre,
                    turma.codigo,
                    turma.disciplina,
                    turma.turma,
                    turma.local,
                    "Sem horário fixo",
                    "-",
                    "-",
                    "-",
                    turma.horario_bruto or "-",
                    periodo_datas,
                ]
            )
            continue

        for slot in slots:
            writer.writerow(
                [
                    turma.semestre,
                    turma.codigo,
                    turma.disciplina,
                    turma.turma,
                    turma.local,
                    slot.dia_nome,
                    slot.turno_nome,
                    slot.hora_inicio,
                    slot.hora_fim,
                    slot.codigo_original,
                    periodo_datas,
                ]
            )
    return buffer.getvalue()


def parse_vinculos_html(html: str) -> list[VinculoItem]:
    """Extract institutional vínculos from '/sigaa/vinculos.jsf' or '/sigaa/escolhaVinculo.do'."""
    soup = BeautifulSoup(html, "lxml")
    vinculos: list[VinculoItem] = []

    tables = soup.select("table.listagem, table.subFormulario, #conteudo table")
    idx = 0
    for table in tables:
        if any("ThemeOffice" in c for c in (table.get("class") or [])):
            continue
        for tr in table.find_all("tr"):
            cells = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if len(cells) < 2:
                continue
            link = tr.find("a")
            if not link:
                continue
            row_text = " | ".join(c for c in cells if c)
            mat_match = re.search(r"\b(\d{8,14})\b", row_text)
            matricula = mat_match.group(1) if mat_match else ""
            nivel = ""
            for cand in ("GRADUAÇÃO", "GRADUACAO", "MESTRADO", "DOUTORADO", "PÓS-GRADUAÇÃO", "TÉCNICO", "RESIDÊNCIA"):
                if cand in row_text.upper():
                    nivel = cand.title()
                    break
            situacao = "ATIVO"
            for st in ("INATIVO", "CONCLUÍDO", "CONCLUIDO", "CANCELADO", "TRANCADO", "FORMANDO", "ATIVO"):
                if st in row_text.upper():
                    situacao = st
                    break
            ativo = situacao not in {"INATIVO", "CONCLUÍDO", "CONCLUIDO", "CANCELADO"}
            curso_parts = [c for c in cells if c and c != matricula and len(c) > 4]
            curso = curso_parts[-1] if curso_parts else row_text[:80]
            vinculos.append(
                VinculoItem(
                    indice=idx,
                    identificador=clean_ws(link.get_text(" ", strip=True)) or f"vinculo_{idx}",
                    matricula=matricula,
                    curso=curso,
                    nivel=nivel,
                    situacao=situacao,
                    ativo=ativo,
                )
            )
            idx += 1

    return vinculos


def parse_portal_discente(html: str, base_url: str = "https://sigaa.ufpa.br") -> tuple[PerfilDiscenteResumo, list[TurmaMatriculada], list[AvisoTurma], list[AtividadePendente]]:
    """Extract profile, academic indices, enrolled classes, ticker notices, and portal activities."""
    soup = BeautifulSoup(html, "lxml")
    perfil = PerfilDiscenteResumo()

    info_usuario = soup.select_one("#info-usuario")
    if info_usuario:
        user_span = info_usuario.select_one("p.usuario span, .usuario")
        if user_span:
            perfil.nome = clean_ws(user_span.get_text(" ", strip=True))
        periodo_span = info_usuario.select_one("p.periodo-atual strong, .periodo-atual")
        if periodo_span:
            sem_match = re.search(r"(\d{4}\.\d)", periodo_span.get_text())
            if sem_match:
                perfil.semestre_atual = sem_match.group(1)

    perfil_box = soup.select_one("#perfil-docente")
    if perfil_box:
        if not perfil.nome:
            p_nome = perfil_box.select_one("p.info-docente span, span.nome, b")
            if p_nome:
                perfil.nome = clean_ws(p_nome.get_text(" ", strip=True))
        img = perfil_box.select_one("img")
        if img and img.get("src"):
            src = img["src"].strip()
            if src.startswith("/"):
                src = f"{base_url.rstrip('/')}{src}"
            perfil.foto_url = src

        p_desc = perfil_box.select_one("p.info-docente")
        if p_desc:
            desc_txt = clean_ws(p_desc.get_text(" ", strip=True))
            if desc_txt and "perfil" not in desc_txt.lower()[:20]:
                perfil.descricao_pessoal = desc_txt

        for tr in perfil_box.find_all("tr"):
            tds = [clean_ws(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
            if len(tds) == 2:
                k, v = tds[0].rstrip(":").upper(), tds[1]
                if "MATRICULA" in normalize_text(k):
                    perfil.matricula = v
                elif k == "CURSO":
                    perfil.curso = v
                elif "NIVEL" in normalize_text(k):
                    perfil.nivel = v
                elif k == "STATUS":
                    perfil.status = v
                elif "MAIL" in k:
                    perfil.email = v
                elif k == "ENTRADA":
                    perfil.entrada = v

            # Academic indices table often places pairs (ACRONYM, VALUE) across columns
            acronym_els = tr.find_all("acronym")
            if acronym_els:
                cells = [clean_ws(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
                for i in range(0, len(cells) - 1, 2):
                    sigla = cells[i].rstrip(":").strip()
                    val = cells[i + 1].strip()
                    if sigla and re.match(r"^[A-Z]{2,6}$", sigla) and val:
                        perfil.indices[sigla] = val

        # Fallback regex extraction for indices if not wrapped in <acronym>
        box_txt = clean_ws(perfil_box.get_text(" ", strip=True))
        for idx_name in ("MC", "CRG", "MCN", "IECH", "IEPL", "IEA", "IEAN", "IRA"):
            if idx_name not in perfil.indices:
                m = re.search(rf"\b{idx_name}\s*:?\s*(\d+[.,]\d+)\b", box_txt)
                if m:
                    perfil.indices[idx_name] = m.group(1)

    # Parse #turmas-portal (both ticker notices and enrolled classes)
    turmas: list[TurmaMatriculada] = []
    avisos_portal: list[AvisoTurma] = []
    turmas_box = soup.select_one("#turmas-portal")
    if turmas_box:
        # Ticker news items (e.g. "30/10/2026 - SINAIS E SISTEMAS (2026.4) Nova Notícia: Convolução")
        raw_box_lines = [clean_ws(el.get_text(" ", strip=True)) for el in turmas_box.select("p, div.noticia, li, td")]
        seen_notices: set[tuple[str, str]] = set()
        for line in raw_box_lines:
            m_news = re.match(
                r"^(\d{2}/\d{2}/\d{4})\s*-\s*(.+?)\s*\((\d{4}\.\d)\)\s*(?:Nova Not[íi]cia:\s*)?(.+)$",
                line,
                flags=re.IGNORECASE,
            )
            if m_news:
                dt, disc, sem, body = m_news.groups()
                key = (disc, body[:80])
                if key not in seen_notices:
                    seen_notices.add(key)
                    avisos_portal.append(
                        AvisoTurma(
                            disciplina=clean_ws(disc),
                            semestre=sem,
                            data=dt,
                            titulo=clean_ws(body[:90]),
                            conteudo=clean_ws(body),
                            origem="portal_atualizacoes",
                        )
                    )

        current_sem = perfil.semestre_atual
        in_turmas_table = False
        for tr in turmas_box.find_all("tr"):
            ths = [clean_ws(th.get_text(" ", strip=True)) for th in tr.find_all("th")]
            if any("Componente Curricular" in h for h in ths):
                in_turmas_table = True
                continue
            if not in_turmas_table:
                continue

            tds = tr.find_all("td")
            texts = [clean_ws(td.get_text(" ", strip=True)) for td in tds]
            non_empty = [t for t in texts if t]
            if not non_empty:
                continue
            if len(non_empty) == 1 and re.match(r"^\d{4}\.\d$", non_empty[0]):
                current_sem = non_empty[0]
                if not perfil.semestre_atual:
                    perfil.semestre_atual = current_sem
                continue

            desc_td = tr.select_one("td.descricao") or (tds[0] if tds else None)
            if not desc_td:
                continue
            disc_full = clean_ws(desc_td.get_text(" ", strip=True))
            if not disc_full or "Componente Curricular" in disc_full:
                continue

            cod = ""
            disc_name = disc_full
            m_cod = re.match(r"^([A-Z]{2,6}\d{3,6})\s*-\s*(.+)$", disc_full)
            if m_cod:
                cod, disc_name = m_cod.group(1), m_cod.group(2)

            local = texts[1] if len(texts) > 1 else ""
            horario_raw = texts[2] if len(texts) > 2 else ""
            slots, periodo_datas = decode_ufpa_schedule(horario_raw)
            turmas.append(
                TurmaMatriculada(
                    codigo=cod,
                    disciplina=disc_name,
                    local=local,
                    horario_bruto=horario_raw,
                    periodo_datas=periodo_datas,
                    semestre=current_sem,
                    slots_decodificados=slots,
                )
            )

    # Parse #avaliacoes-portal (Minhas Atividades summary on portal home)
    atividades_portal: list[AtividadePendente] = []
    aval_box = soup.select_one("#avaliacoes-portal")
    if aval_box:
        for tr in aval_box.find_all("tr"):
            cells = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            non_empty = [c for c in cells if c]
            if len(non_empty) >= 2:
                joined = " | ".join(non_empty)
                if "não há" in joined.lower() or "nenhuma" in joined.lower():
                    continue
                prazo_match = re.search(r"(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)", joined)
                prazo = prazo_match.group(1) if prazo_match else non_empty[0]
                desc = non_empty[-1]
                disc = non_empty[1] if len(non_empty) >= 3 else "Portal do Discente"
                tipo = "Avaliação" if "avalia" in joined.lower() else "Tarefa"
                done = bool(tr.find("img", src=re.compile(r"check|sim|ok", re.I)))
                atividades_portal.append(
                    AtividadePendente(
                        disciplina=disc,
                        tipo=tipo,
                        titulo=desc,
                        prazo=prazo,
                        situacao="Concluída" if done else "Pendente",
                        concluida=done,
                    )
                )

    return perfil, turmas, avisos_portal, atividades_portal


def parse_minhas_notas_html(html: str) -> list[NotaDisciplina]:
    """Parse 'Consultar Minhas Notas' tables ('table.tabelaRelatorio')."""
    soup = BeautifulSoup(html, "lxml")
    resultados: list[NotaDisciplina] = []

    for tbl in soup.select("table.tabelaRelatorio"):
        caption = tbl.find("caption")
        semestre = clean_ws(caption.get_text(" ", strip=True)) if caption else ""
        headers = [normalize_text(th.get_text(" ", strip=True)) for th in tbl.find_all("th")]

        def _col_idx(patterns: tuple[str, ...], default: int = -1) -> int:
            for idx, h in enumerate(headers):
                if any(p in h for p in patterns):
                    return idx
            return default

        idx_cod = _col_idx(("CODIGO", "COD"), 0)
        idx_disc = _col_idx(("DISCIPLINA", "COMPONENTE"), 1)
        idx_u1 = _col_idx(("UNIDADE. 1", "UNIDADE 1", "1A UNID", "AVAL. 1"))
        idx_u2 = _col_idx(("UNIDADE. 2", "UNIDADE 2", "2A UNID", "AVAL. 2"))
        idx_u3 = _col_idx(("UNIDADE. 3", "UNIDADE 3", "3A UNID", "AVAL. 3"))
        idx_rec = _col_idx(("RECUPERAC", "EXAME", "FINAL"))
        idx_res = _col_idx(("RESULTADO", "MEDIA", "CONCEITO"))
        idx_fal = _col_idx(("FALTAS", "FREQUENCIA"))
        idx_sit = _col_idx(("SITUAC", "STATUS"))

        for tr in tbl.find_all("tr"):
            tds = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if len(tds) < 4:
                continue
            cod = tds[idx_cod] if 0 <= idx_cod < len(tds) else ""
            disc = tds[idx_disc] if 0 <= idx_disc < len(tds) else ""
            if not disc or normalize_text(disc) in {"DISCIPLINA", "LEGENDA"}:
                continue

            def _val(i: int, fallback: str = "-") -> str:
                if 0 <= i < len(tds) and tds[i] != "":
                    return tds[i]
                return fallback

            resultados.append(
                NotaDisciplina(
                    semestre=semestre,
                    codigo=cod,
                    disciplina=disc,
                    unidade_1=_val(idx_u1),
                    unidade_2=_val(idx_u2),
                    unidade_3=_val(idx_u3),
                    recuperacao=_val(idx_rec),
                    resultado=_val(idx_res),
                    faltas=_val(idx_fal, "0"),
                    situacao=_val(idx_sit),
                )
            )

    return resultados


def parse_atestado_html(html: str) -> AtestadoResumo:
    """Parse Atestado de Matrícula HTML ('#matriculas' + header + authenticity code)."""
    soup = BeautifulSoup(html, "lxml")
    full_text = clean_ws(soup.get_text(" ", strip=True))
    resumo = AtestadoResumo()

    m_sem = re.search(r"Per[íi]odo Letivo:\s*(\d{4}\.\d)", full_text, re.I)
    if m_sem:
        resumo.semestre = m_sem.group(1)

    m_mat = re.search(r"Matr[íi]cula:\s*(\d{6,15})", full_text, re.I)
    if m_mat:
        resumo.matricula = m_mat.group(1)

    m_nome = re.search(r"Nome:\s*(.+?)\s*(?:Curso:|N[íi]vel:|V[íi]nculo:)", full_text)
    if m_nome:
        resumo.nome = clean_ws(m_nome.group(1))

    m_curso = re.search(r"Curso:\s*(.+?)\s*(?:Formação:|Modalidade:|Turno:|Polo:|Cód\.|$)", full_text)
    if m_curso:
        resumo.curso = clean_ws(m_curso.group(1))[:120]

    m_ver = re.search(r"c[óo]digo de verifica[çc][ãa]o\s+([a-f0-9]{6,20})", full_text, re.I)
    if m_ver:
        resumo.codigo_verificacao = m_ver.group(1)

    tbl = soup.select_one("table#matriculas") or soup.select_one("table.listagem")
    if tbl:
        for tr in tbl.find_all("tr"):
            tds = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if len(tds) < 5:
                continue
            cod, comp_docente, turma_num, _status, horario_raw = tds[:5]
            if not cod or not re.match(r"^[A-Z0-9]{4,12}$", cod):
                continue

            # Split component name vs docente inside cell
            comp_clean = re.sub(r"\s*Tipo:\s*.*$", "", comp_docente).strip()
            docente = ""
            # Check inner elements if structured with spans/strongs/br
            td_comp = tr.find_all("td")[1]
            lines = [clean_ws(s) for s in td_comp.stripped_strings if clean_ws(s) and "Tipo:" not in s]
            if len(lines) >= 2:
                disc_name = lines[0]
                docente = ", ".join(lines[1:])
            else:
                disc_name = comp_clean

            slots, periodo_datas = decode_ufpa_schedule(horario_raw)
            resumo.turmas.append(
                TurmaMatriculada(
                    codigo=cod,
                    disciplina=disc_name,
                    turma=turma_num,
                    docente=docente,
                    horario_bruto=horario_raw,
                    periodo_datas=periodo_datas,
                    semestre=resumo.semestre,
                    slots_decodificados=slots,
                )
            )

    resumo.choques_horario = detect_schedule_conflicts(resumo.turmas)
    return resumo


def parse_historico_pdf(pdf_path: str | Path, fallback_perfil: Optional[PerfilDiscenteResumo] = None) -> HistoricoResumo:
    """Extract structured academic summary from UFPA's official Histórico Escolar PDF via pypdf 7."""
    reader = PdfReader(str(pdf_path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    raw_all = "\n".join(pages_text)
    flat = clean_ws(raw_all)

    resumo = HistoricoResumo(arquivo_pdf=str(Path(pdf_path).resolve()))
    if fallback_perfil:
        resumo.nome = fallback_perfil.nome
        resumo.matricula = fallback_perfil.matricula
        resumo.curso = fallback_perfil.curso
        resumo.status = fallback_perfil.status
        resumo.crg = fallback_perfil.indices.get("CRG", "")
        resumo.mc = fallback_perfil.indices.get("MC", "")
        resumo.iea = fallback_perfil.indices.get("IEA", "")

    if not resumo.matricula:
        m_mat = re.search(r"Matr[íi]cula:\s*(\d{8,15})", raw_all)
        if m_mat:
            resumo.matricula = m_mat.group(1)

    if not resumo.nome:
        m_nome = re.search(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{6,})\s*Nome:", raw_all)
        if m_nome:
            resumo.nome = clean_ws(m_nome.group(1))

    m_status = re.search(r"Status:\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ]+)", raw_all)
    if m_status:
        resumo.status = m_status.group(1)

    for attr, label in (("crg", "CRG"), ("mc", "MC"), ("iea", "IEA")):
        if not getattr(resumo, attr):
            m_idx = re.search(rf"\b{label}\b\s*:?\s*(\d+[.,]\d+)", flat)
            if m_idx:
                setattr(resumo, attr, m_idx.group(1))

    # Count completed/enrolled curriculum rows (e.g. lines starting with YYYY.P)
    comp_matches = re.findall(r"(?m)^\s*20\d{2}\.[1-4]\b", raw_all)
    resumo.componentes_cursados_ou_cursando = len(comp_matches)

    # Extract pending mandatory courses count & sample
    m_pend_cnt = re.search(r"Componentes Curriculares Obrigat[óo]rios Pendentes:\s*(\d+)", raw_all, re.I)
    if m_pend_cnt:
        resumo.obrigatorias_pendentes_qtd = int(m_pend_cnt.group(1))

    if "Obrigatórios Pendentes" in raw_all or "Obrigatorios Pendentes" in normalize_text(raw_all):
        pend_section_match = re.search(
            r"Componentes Curriculares Obrigat[óo]rios Pendentes:\s*\d+(.*?)(?:Equival[êe]ncias:|Observa[çc][õo]es:|Para verificar a autenticidade|$)",
            raw_all,
            flags=re.S | re.I,
        )
        if pend_section_match:
            for line in pend_section_match.group(1).splitlines():
                cleaned_line = clean_ws(line)
                if (
                    cleaned_line
                    and "Componente Curricular" not in cleaned_line
                    and len(cleaned_line) > 5
                    and re.search(r"\b\d+\s*h", cleaned_line)
                ):
                    resumo.obrigatorias_pendentes_amostra.append(cleaned_line)

    # Extract Exigido / Integralizado / Pendente workload numbers if present
    # UFPA PDFs usually print three rows of numbers (Obrigatórias, Optativos, Complementares, Total)
    m_exigido = re.search(r"Exigido\s+((?:\d+\s*h?\s*){2,5})", raw_all, re.I)
    m_integ = re.search(r"Integralizado\s+((?:\d+\s*h?\s*){2,5})", raw_all, re.I)
    m_pend_ch = re.search(r"Pendente\s+((?:\d+\s*h?\s*){2,5})", raw_all, re.I)
    if m_exigido and m_integ:
        ex_nums = [int(x) for x in re.findall(r"\d+", m_exigido.group(1))]
        in_nums = [int(x) for x in re.findall(r"\d+", m_integ.group(1))]
        pe_nums = [int(x) for x in re.findall(r"\d+", m_pend_ch.group(1))] if m_pend_ch else []
        if ex_nums and in_nums:
            total_ex = max(ex_nums)
            idx_total = ex_nums.index(total_ex)
            total_in = in_nums[idx_total] if idx_total < len(in_nums) else max(in_nums)
            total_pe = pe_nums[idx_total] if idx_total < len(pe_nums) else max(0, total_ex - total_in)
            resumo.carga_horaria_total = CargaHorariaItem(
                exigido=total_ex, integralizado=total_in, pendente=total_pe
            )

    return resumo


def parse_ava_noticias_html(html: str, disciplina: str, semestre: str = "") -> list[AvisoTurma]:
    """Parse notices table ('table.listing') inside a SIGAA Turma Virtual (AVA)."""
    soup = BeautifulSoup(html, "lxml")
    avisos: list[AvisoTurma] = []
    for tbl in soup.select("table.listing, table.listagem"):
        for tr in tbl.find_all("tr"):
            tds = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if len(tds) >= 2:
                titulo, data = tds[0], tds[1]
                if not titulo or normalize_text(titulo) in {"TITULO", "NENHUMA NOTICIA CADASTRADA"}:
                    continue
                if "nenhuma" in titulo.lower() and "cadastrad" in titulo.lower():
                    continue
                avisos.append(
                    AvisoTurma(
                        disciplina=disciplina,
                        semestre=semestre,
                        data=data,
                        titulo=titulo,
                        conteudo=titulo,
                        origem="ava_noticias",
                    )
                )
    return avisos


def parse_ava_atividades_html(html: str, disciplina: str, tipo: str = "Tarefa") -> list[AtividadePendente]:
    """Parse tasks, quizzes, or exams inside a SIGAA Turma Virtual (AVA)."""
    soup = BeautifulSoup(html, "lxml")
    itens: list[AtividadePendente] = []

    for tbl in soup.select("table.listing, table.listagem, table.formulario"):
        if any("ThemeOffice" in c for c in (tbl.get("class") or [])):
            continue
        for tr in tbl.find_all("tr"):
            tds = tr.find_all("td")
            texts = [clean_ws(td.get_text(" ", strip=True)) for td in tds]
            non_empty = [t for t in texts if t]
            if len(non_empty) < 2:
                continue
            joined_low = " ".join(non_empty).lower()
            if any(
                skip in joined_low
                for skip in (
                    "nenhuma tarefa",
                    "nenhum question",
                    "nenhuma avalia",
                    "não há",
                    "menu turma virtual",
                    "dados do discente",
                    "título período",
                )
            ):
                continue

            titulo = non_empty[0]
            date_matches = re.findall(r"\d{2}/\d{2}/\d{4}(?:\s+(?:às\s+)?\d{1,2}h?\d{0,2}|\s+\d{2}:\d{2})?", " ".join(non_empty))
            prazo = " a ".join(date_matches[:2]) if date_matches else (non_empty[1] if len(non_empty) > 1 else "")
            concluida = any(
                w in joined_low for w in ("enviada", "submetida", "corrigida", "finalizada", "respondido")
            )
            situacao = "Concluída/Enviada" if concluida else "Aberta/Pendente"
            itens.append(
                AtividadePendente(
                    disciplina=disciplina,
                    tipo=tipo,
                    titulo=titulo,
                    prazo=prazo,
                    situacao=situacao,
                    concluida=concluida,
                )
            )
    return itens


def parse_dados_pessoais_html(html: str) -> dict[str, str]:
    """Extract CPF and Data de Nascimento from 'Meus Dados Pessoais' in RAM only."""
    soup = BeautifulSoup(html, "lxml")
    dados: dict[str, str] = {}

    for tr in soup.select("table.formulario tr, table.visualizacao tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = normalize_text(th.get_text(" ", strip=True))
        inp = td.find("input")
        val = clean_ws(inp.get("value", "")) if inp and inp.get("value") else clean_ws(td.get_text(" ", strip=True))
        if not val:
            continue
        if "CPF" in label and "cpf" not in dados:
            m_cpf = re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", val)
            if m_cpf:
                dados["cpf"] = m_cpf.group(0)
        elif "NASCIMENTO" in label and "DATA" in label and "data_nascimento" not in dados:
            m_dt = re.search(r"\d{2}/\d{2}/\d{4}", val)
            if m_dt:
                dados["data_nascimento"] = m_dt.group(0)

    return dados


def parse_turmas_ofertadas_html(
    html: str, enrolled_turmas: Optional[Iterable[TurmaMatriculada]] = None
) -> list[DisciplinaOfertada]:
    """Parse SIGAA 'Consultar Turma' results ('table.listagem' with 'tr.agrupador' headers)."""
    soup = BeautifulSoup(html, "lxml")
    enrolled_list = list(enrolled_turmas or [])
    resultados: list[DisciplinaOfertada] = []

    tbl = soup.select_one("table#lista-turmas") or soup.select_one("table.listagem")
    if not tbl:
        return resultados

    headers = [normalize_text(th.get_text(" ", strip=True)) for th in tbl.find_all("th")]

    def _hidx(keys: tuple[str, ...], default: int = -1) -> int:
        for i, h in enumerate(headers):
            if any(k in h for k in keys):
                return i
        return default

    idx_per = _hidx(("ANO", "PERIODO"), 0)
    idx_turma = _hidx(("TURMA",), 1)
    idx_docente = _hidx(("DOCENTE",), 2)
    idx_horario = _hidx(("HORARIO",), 6)
    idx_local = _hidx(("LOCAL",), 7)
    idx_cap = _hidx(("MATRICULA", "CAPACIDADE", "VAGAS", "MAT./CAP", "CAP."), 8)

    current_cod = ""
    current_disc = ""

    for tr in tbl.find_all("tr"):
        classes = tr.get("class") or []
        if (
            "agrupador" in classes
            or "destaque" in classes
            or tr.select_one("td.agrupador, td.destaque, span.tituloDisciplina")
        ):
            grp_txt = clean_ws(tr.get_text(" ", strip=True))
            m_grp = re.match(r"^([A-Z0-9]{4,12})\s*-\s*(.+)$", grp_txt)
            if m_grp:
                current_cod = m_grp.group(1)
                current_disc = re.sub(r"\s*\((?:\d+h|GRADUA|PÓS|POS|TECNIC).*$", "", m_grp.group(2), flags=re.I).strip()
            else:
                current_disc = grp_txt
            continue

        tds = [clean_ws(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
        if len(tds) < 5 or not current_disc:
            continue
        # Skip sub-rows that are just action links or empty
        ano_per = tds[idx_per] if 0 <= idx_per < len(tds) else ""
        if ano_per and not re.search(r"\d{4}", ano_per) and not tds[1]:
            continue

        turma_code = tds[idx_turma] if 0 <= idx_turma < len(tds) else ""
        docente = tds[idx_docente] if 0 <= idx_docente < len(tds) else ""
        horario_raw = tds[idx_horario] if 0 <= idx_horario < len(tds) else ""
        local = tds[idx_local] if 0 <= idx_local < len(tds) else ""
        cap_raw = tds[idx_cap] if 0 <= idx_cap < len(tds) else ""

        # Fallback heuristic if columns shift across public vs internal search
        if not _SCHEDULE_TOKEN_RE.search(horario_raw):
            for cell in tds:
                if _SCHEDULE_TOKEN_RE.search(cell):
                    horario_raw = cell
                    break
        if "/" not in cap_raw:
            for cell in reversed(tds):
                if re.match(r"^\d+\s*/\s*\d+", cell):
                    cap_raw = cell
                    break

        vagas_ocup, vagas_ofert = "", ""
        m_cap = re.search(r"(\d+)\s*/\s*(\d+)", cap_raw)
        if m_cap:
            vagas_ocup, vagas_ofert = m_cap.group(1), m_cap.group(2)

        tem_choque, detalhes_choque = check_candidate_conflict(horario_raw, enrolled_list)
        resultados.append(
            DisciplinaOfertada(
                codigo=current_cod,
                disciplina=current_disc,
                turma=turma_code,
                docente=docente,
                horario_bruto=horario_raw,
                local=local,
                ano_periodo=ano_per,
                vagas_ocupadas=vagas_ocup,
                vagas_ofertadas=vagas_ofert,
                tem_choque_com_grade=tem_choque,
                detalhes_choque=detalhes_choque,
            )
        )

    return resultados
