"""Unit tests for UFPA schedule decoder, conflict detector, HTML parsers, and CSV export."""

from __future__ import annotations

from sigaa_mcp.parsers import (
    build_schedule_csv,
    check_candidate_conflict,
    decode_ufpa_schedule,
    detect_schedule_conflicts,
    parse_atestado_html,
    parse_dados_pessoais_html,
    parse_minhas_notas_html,
    parse_portal_discente,
    parse_turmas_ofertadas_html,
    parse_vinculos_html,
)
from sigaa_mcp.schemas import TurmaMatriculada


def test_decode_ufpa_schedule_with_date_range() -> None:
    slots, periodo = decode_ufpa_schedule("24M56 (24/08/2026 - 23/12/2026)")
    assert periodo == "24/08/2026 - 23/12/2026"
    assert len(slots) == 4
    assert slots[0].dia_nome == "Segunda-feira"
    assert slots[0].turno_codigo == "M"
    assert slots[0].slot_numero == 5
    assert slots[0].hora_inicio == "11:10"
    assert slots[0].hora_fim == "12:00"
    assert slots[-1].dia_nome == "Quarta-feira"
    assert slots[-1].hora_fim == "12:50"


def test_detect_schedule_conflicts_and_candidate_collision() -> None:
    t1_slots, _ = decode_ufpa_schedule("24M56")
    t2_slots, _ = decode_ufpa_schedule("4M6 6T12")
    t1 = TurmaMatriculada(codigo="EC01020", disciplina="SINAIS E SISTEMAS", horario_bruto="24M56", slots_decodificados=t1_slots)
    t2 = TurmaMatriculada(codigo="EC01035", disciplina="COMUNICACOES DIGITAIS", horario_bruto="4M6 6T12", slots_decodificados=t2_slots)

    conflicts = detect_schedule_conflicts([t1, t2])
    assert len(conflicts) == 1
    assert conflicts[0].dia_nome == "Quarta-feira"
    assert conflicts[0].slot_numero == 6
    assert len(conflicts[0].disciplinas) == 2

    has_clash, details = check_candidate_conflict("2M5", [t1])
    assert has_clash is True
    assert any("Segunda-feira" in d for d in details)

    free_ok, free_details = check_candidate_conflict("35N12", [t1])
    assert free_ok is False
    assert free_details == []


def test_build_schedule_csv() -> None:
    slots, per = decode_ufpa_schedule("35T12 (24/08/2026 - 23/12/2026)")
    turma = TurmaMatriculada(
        semestre="2026.4",
        codigo="EC01004",
        disciplina="PROGRAMAÇÃO",
        turma="01",
        local="LAB 02",
        horario_bruto="35T12",
        periodo_datas=per,
        slots_decodificados=slots,
    )
    csv_out = build_schedule_csv([turma])
    lines = csv_out.strip().splitlines()
    assert len(lines) == 5  # 1 header + 4 weekly slots
    assert "PROGRAMAÇÃO" in csv_out
    assert "Terça-feira" in csv_out
    assert "13:00,13:50" in csv_out


def test_parse_portal_discente_and_minhas_notas() -> None:
    portal_html = """
    <div id="info-usuario">
      <p class="usuario"><span>JOÃO ESTUDANTE TESTE</span></p>
      <p class="periodo-atual">Semestre atual: <strong>2026.4</strong></p>
    </div>
    <div id="perfil-docente">
      <table>
        <tr><td>Matrícula:</td><td>202006840099</td></tr>
        <tr><td>Curso:</td><td>ENGENHARIA DA COMPUTACAO/ITEC - BELÉM</td></tr>
        <tr><td>Status:</td><td>FORMANDO</td></tr>
        <tr><td><acronym>CRG</acronym></td><td>8.45</td><td><acronym>MC</acronym></td><td>8.72</td></tr>
      </table>
    </div>
    <div id="turmas-portal">
      <p>30/10/2026 - SINAIS E SISTEMAS (2026.4) Nova Notícia: Convolução discreta</p>
      <table>
        <tr><th>Componente Curricular</th><th>Local</th><th>Horário</th></tr>
        <tr><td>2026.4</td></tr>
        <tr><td class="descricao"><a href="#">EC01020 - SINAIS E SISTEMAS</a></td><td>TELECOM 301</td><td>24M56 (24/08/2026 - 23/12/2026)</td></tr>
      </table>
    </div>
    """
    perfil, turmas, avisos, _ = parse_portal_discente(portal_html)
    assert perfil.nome == "JOÃO ESTUDANTE TESTE"
    assert perfil.matricula == "202006840099"
    assert perfil.indices["CRG"] == "8.45"
    assert len(turmas) == 1
    assert turmas[0].codigo == "EC01020"
    assert len(turmas[0].slots_decodificados) == 4
    assert len(avisos) == 1
    assert "Convolução" in avisos[0].titulo

    notas_html = """
    <table class="tabelaRelatorio">
      <caption>2026.4</caption>
      <tr><th>Código</th><th>Disciplina</th><th>Unidade. 1</th><th>Unidade. 2</th><th>Recuperação</th><th>Resultado</th><th>Faltas</th><th>Situação</th></tr>
      <tr><td>EC01037</td><td>ESTÁGIO SUPERVISIONADO I</td><td></td><td></td><td></td><td>E</td><td>0</td><td>APROVADO</td></tr>
      <tr><td>EC01020</td><td>SINAIS E SISTEMAS</td><td>8.5</td><td></td><td></td><td>-</td><td>2</td><td>MATRICULADO</td></tr>
    </table>
    """
    notas = parse_minhas_notas_html(notas_html)
    assert len(notas) == 2
    assert notas[0].resultado == "E"
    assert notas[1].unidade_1 == "8.5"
    assert notas[1].faltas == "2"


def test_parse_atestado_ofertadas_vinculos_and_dados_pessoais() -> None:
    atestado_html = """
    <div>Período Letivo: 2026.4 Matrícula: 202006840099 Nome: JOÃO TESTE Curso: ENGENHARIA Cód.</div>
    <table id="matriculas">
      <tr><th>Cód.</th><th>Componentes Curriculares/Docentes</th><th>Turma</th><th>Status</th><th>Horário</th></tr>
      <tr><td>EC01020</td><td><span>SINAIS E SISTEMAS</span><br/><span>PROF. EXEMPLO</span></td><td>01</td><td>MATRICULADO</td><td>24M56</td></tr>
    </table>
    <p>informando a matrícula e o código de verificação a1b2c3d4e5</p>
    """
    at = parse_atestado_html(atestado_html)
    assert at.semestre == "2026.4"
    assert at.codigo_verificacao == "a1b2c3d4e5"
    assert len(at.turmas) == 1
    assert at.turmas[0].docente == "PROF. EXEMPLO"

    ofertadas_html = """
    <table id="lista-turmas" class="listagem">
      <tr><th>Ano Período</th><th></th><th>Docente(s)</th><th>Tipo</th><th>Modalidade</th><th>Situação</th><th>Horário</th><th>Local</th><th>Mat./Cap.</th></tr>
      <tr class="destaque"><td colspan="9">EC01099 - TÓPICOS EM IA (GRADUAÇÃO)</td></tr>
      <tr class="linhaPar"><td>2026.4</td><td>Turma 01</td><td>DRA. ANA (60h)</td><td>REGULAR</td><td>Presencial</td><td>ABERTA</td><td>24M56 (24/08/2026 - 23/12/2026)</td><td>LAB IA</td><td>18/30 alunos</td></tr>
      <tr class="linhaImpar"><td>2026.4</td><td>Turma 02</td><td>DR. CARLOS (60h)</td><td>REGULAR</td><td>Presencial</td><td>ABERTA</td><td>35T34 (24/08/2026 - 23/12/2026)</td><td>LAB IA</td><td>12/30 alunos</td></tr>
    </table>
    """
    ofertadas = parse_turmas_ofertadas_html(ofertadas_html, enrolled_turmas=at.turmas)
    assert len(ofertadas) == 2
    assert ofertadas[0].tem_choque_com_grade is True
    assert ofertadas[1].tem_choque_com_grade is False
    assert ofertadas[0].vagas_ocupadas == "18"
    assert ofertadas[0].vagas_ofertadas == "30"

    vinculos_html = """
    <table class="listagem">
      <tr><td><a href="#">Selecionar</a></td><td>202006840099</td><td>GRADUAÇÃO</td><td>ATIVO</td><td>ENGENHARIA DA COMPUTAÇÃO</td></tr>
      <tr><td><a href="#">Selecionar</a></td><td>201800011122</td><td>TÉCNICO</td><td>CONCLUÍDO</td><td>INFORMÁTICA</td></tr>
    </table>
    """
    vincs = parse_vinculos_html(vinculos_html)
    assert len(vincs) == 2
    assert vincs[0].ativo is True
    assert vincs[1].ativo is False

    mdp_html = """
    <table class="formulario">
      <tr><th>CPF:</th><td>123.456.789-00</td></tr>
      <tr><th>Data de Nascimento:</th><td><input value="01/02/2000" /></td></tr>
    </table>
    """
    dados = parse_dados_pessoais_html(mdp_html)
    assert dados["cpf"] == "123.456.789-00"
    assert dados["data_nascimento"] == "01/02/2000"
