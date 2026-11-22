"""Parsers for turma-virtual attendance, 'Todas as Turmas' and boletim/frequência merging."""

from __future__ import annotations

from sigaa_mcp.flows.frequencia import _resolver_disciplina, anexar_frequencia_ao_boletim
from sigaa_mcp.parsers import parse_frequencia_turma_html, parse_todas_turmas_html
from sigaa_mcp.schemas import FrequenciaTurma, NotaDisciplina

FREQ_HTML = """
<html><body><div id="conteudo">
<h3>Mapa de Freqüências</h3>
<p>Tiver presença em um número de aulas igual ou superior a 75.0% da carga horária do componente curricular.</p>
<table class="listing"><thead><tr><th>Data</th><th>Situação</th></tr></thead><tbody>
<tr><td>10/03/2026</td><td>Presente</td></tr>
<tr><td>12/03/2026</td><td>2 Faltas</td></tr>
<tr><td>17/03/2026</td><td>Presente</td></tr>
</tbody></table>
<div>Frequência: 4</div>
<div>Número de Aulas Ministradas: 6</div>
<div>Porcentagem de Frequência em relação as Aulas Ministradas: 66%</div>
<div>Número de Aulas definidas pela CH do Componente: 72</div>
<div>Porcentagem de Frequência em relação a CH: 5%</div>
</div></body></html>
"""

TURMAS_HTML = """
<div id="conteudo"><table class="listagem">
<tr><td colspan="5">2025.4</td></tr>
<tr class="linhaPar"><td>EC01035 - COMUNICACOES DIGITAIS I</td><td>01</td><td>60h</td>
<td>35T65 (24/11/2025 - 03/04/2026)</td>
<td><a href="#" onclick="jsfcljs(f,{'frontEndIdTurma':'ABC123','x':'y'},'');" title="Acessar Turma Virtual"></a></td></tr>
<tr><td colspan="5">2026.2</td></tr>
<tr class="linhaImpar"><td>EC01020 - SINAIS E SISTEMAS</td><td>01</td><td>60h</td><td>24M56</td>
<td><a href="#" onclick="jsfcljs(f,{'frontEndIdTurma':'DEF456'},'');"></a></td></tr>
</table></div>
"""


def test_parse_frequencia_turma():
    f = parse_frequencia_turma_html(FREQ_HTML)
    assert [r.faltas for r in f.registros] == [0, 2, 0]
    assert f.presencas == 4
    assert f.aulas_ministradas == 6
    assert f.faltas == 2
    assert f.aulas_carga_horaria == 72
    assert f.limite_faltas == 18
    assert f.faltas_restantes == 16
    assert f.percentual_frequencia_ministradas == "66%"
    assert not f.em_risco


def test_parse_todas_turmas():
    turmas = parse_todas_turmas_html(TURMAS_HTML)
    assert [(t.semestre, t.codigo, t.front_end_id) for t in turmas] == [
        ("2025.4", "EC01035", "ABC123"),
        ("2026.2", "EC01020", "DEF456"),
    ]
    assert turmas[0].disciplina == "COMUNICACOES DIGITAIS I"


def test_anexar_frequencia_ao_boletim():
    notas = [
        NotaDisciplina(semestre="2026.2", codigo="EC01020", disciplina="SINAIS E SISTEMAS", faltas="10"),
        NotaDisciplina(semestre="2025.4", codigo="EC01020", disciplina="SINAIS E SISTEMAS", faltas="4"),
    ]
    freq = FrequenciaTurma(semestre="2026.2", codigo="EC01020", disciplina="SINAIS E SISTEMAS", faltas=12)
    anexar_frequencia_ao_boletim(notas, [freq])
    assert notas[0].frequencia_turma is not None and notas[0].frequencia_turma.faltas == 12
    assert notas[1].frequencia_turma is None
    assert notas[0].fonte_faltas == "boletim"


def test_resolver_disciplina_por_nome_e_codigo():
    notas = [
        NotaDisciplina(semestre="2022.2", codigo="NITAE005", disciplina="CALCULO I", situacao="REPROVADO"),
        NotaDisciplina(semestre="2022.4", codigo="NITAE005", disciplina="CALCULO I", situacao="APROVADO"),
        NotaDisciplina(semestre="2021.4", codigo="EC01013", disciplina="CALCULO III"),
    ]
    codigo, nome, cursadas = _resolver_disciplina("Cálculo I", notas)
    assert (codigo, nome, len(cursadas)) == ("NITAE005", "CALCULO I", 2)

    codigo, _, cursadas = _resolver_disciplina("ec01013", notas)
    assert codigo == "EC01013" and len(cursadas) == 1

    codigo, nome, cursadas = _resolver_disciplina("Física Quântica", notas)
    assert (codigo, nome, cursadas) == ("", "Física Quântica", [])
