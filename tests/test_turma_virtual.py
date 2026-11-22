"""Turma Virtual (AVA) parsers and turma selection via 'Todas as Turmas'."""

from __future__ import annotations

from sigaa_mcp.flows.turma_virtual import consolidar_atividades, consolidar_avisos, selecionar_turmas
from sigaa_mcp.parsers_ava import (
    ava_secao_vazia,
    parse_ava_arquivos_html,
    parse_ava_noticia_view_html,
    parse_ava_referencias_html,
    parse_ava_topicos_html,
    parse_ava_ultima_noticia_html,
)
from sigaa_mcp.schemas import AtividadePendente, AvisoTurma, ConteudoTurmaVirtual, TurmaHistorica

PRINCIPAL_HTML = """
<div id="conteudo"><div id="formMenu"><a>Notícias</a></div>
<form id="formAva">
<div class="descricaoOperacao" id="ultimaNoticia">
  <h4> Última Notícia <br/>Adiamento da prova - 10/11/2026 16:26 </h4>
  <p>Discentes,</p><p>A prova foi adiada para 23.11.2026.</p>
  <small> Cadastrado por: <i>DOCENTE</i></small>
</div>
<div class="topico-aula">
  <div class="titulo">Apresentação do Curso (24/08/2026 - 24/08/2026) <small><i></i></small></div>
  <div class="conteudotopico"><p><strong>Objetivo:</strong> Apresentar o plano de ensino.</p>
    <div class="drgind_fly drag_indicator"></div>
    <div class="item"><img src="/sigaa/img/porta_arquivos/icones/pdf.png"/>
      <span><a href="#">Plano de Ensino</a></span><div class="descricao-item"><span>Versão 1</span></div></div>
    <div class="item"><img src="/sigaa/img/porta_arquivos/icones/link.png"/>
      <span><a href="#">Simulador</a></span><div class="descricao-item"></div></div>
  </div>
</div>
<div class="topico-aula">
  <div class="titulo">Sinais (26/08/2026 - 09/09/2026)</div>
  <div class="conteudotopico"><p>Capítulo 1.</p></div>
</div>
</form></div>
"""

ARQUIVOS_HTML = """
<div id="conteudo"><table class="listing">
<tr><th>Título</th><th>Descrição</th><th>Tópico de Aula</th><th></th></tr>
<tr class="linhaPar"><td>Plano de Ensino</td><td></td><td>Apresentação do Curso</td><td><a href="#"></a></td></tr>
<tr class="linhaImpar"><td>Lista 1</td><td>Exercícios</td><td>Sinais</td><td><a href="#"></a></td></tr>
</table></div>
"""

REFERENCIAS_HTML = """
<div id="conteudo"><table class="listing">
<tr><th>Nome</th><th>Tipo</th><th>URL</th><th>Tópico de Aula</th><th></th></tr>
<tr class="even"><td class="first">Lathi, Sinais e Sistemas</td><td><p>Livro</p></td>
  <td><a href="http://" target="_blank"></a></td><td><p></p></td><td></td></tr>
<tr class="odd"><td class="first">Animação de convolução</td><td><p>Site</p></td>
  <td><a href="https://example.org/conv" target="_blank">link</a></td><td><p>Convolução</p></td><td></td></tr>
</table></div>
"""

NOTICIA_VIEW_HTML = """
<div id="conteudo"><h3>Visualização de Notícia</h3>
<div>Título: Convolução</div><div>Data: 30/10/2026 10:01</div>
<table><tr><th>Texto: </th><td><div><p>Usem a animação.</p><p>Cordialmente</p></div></td></tr></table>
</div>
"""

VAZIO_HTML = '<div id="conteudo"><h3>Tarefas</h3> Nenhum item foi encontrado</div>'


def _t(sem: str, cod: str, nome: str) -> TurmaHistorica:
    return TurmaHistorica(semestre=sem, codigo=cod, disciplina=nome, front_end_id=f"{cod}{sem}")


TURMAS = [
    _t("2022.2", "EC01014", "CIRCUITOS ELETRICOS"),
    _t("2024.4", "EC01014", "CIRCUITOS ELETRICOS"),
    _t("2026.2", "EC01035", "COMUNICACOES DIGITAIS I"),
    _t("2026.4", "EC01020", "SINAIS E SISTEMAS"),
    _t("2026.4", "EC01099", "TCC"),
]


def test_parse_topicos_com_materiais():
    topicos = parse_ava_topicos_html(PRINCIPAL_HTML)
    assert [t.titulo for t in topicos] == ["Apresentação do Curso", "Sinais"]
    assert topicos[0].periodo == "24/08/2026 - 24/08/2026"
    assert topicos[0].conteudo == "Objetivo: Apresentar o plano de ensino."
    assert [(m.nome, m.tipo, m.descricao) for m in topicos[0].materiais] == [
        ("Plano de Ensino", "pdf", "Versão 1"),
        ("Simulador", "link", ""),
    ]
    assert topicos[1].materiais == []


def test_parse_ultima_noticia():
    n = parse_ava_ultima_noticia_html(PRINCIPAL_HTML, disciplina="SS", semestre="2026.4")
    assert n is not None
    assert (n.titulo, n.data) == ("Adiamento da prova", "10/11/2026 16:26")
    assert n.conteudo == "Discentes, A prova foi adiada para 23.11.2026."
    assert n.origem == "ava_ultima_noticia"


def test_parse_arquivos_e_referencias():
    arquivos = parse_ava_arquivos_html(ARQUIVOS_HTML)
    assert [(a.titulo, a.descricao, a.topico) for a in arquivos] == [
        ("Plano de Ensino", "", "Apresentação do Curso"),
        ("Lista 1", "Exercícios", "Sinais"),
    ]
    refs = parse_ava_referencias_html(REFERENCIAS_HTML)
    assert [(r.nome, r.tipo, r.url, r.topico) for r in refs] == [
        ("Lathi, Sinais e Sistemas", "Livro", "", ""),
        ("Animação de convolução", "Site", "https://example.org/conv", "Convolução"),
    ]


def test_parse_noticia_view():
    assert parse_ava_noticia_view_html(NOTICIA_VIEW_HTML) == (
        "Convolução",
        "30/10/2026 10:01",
        "Usem a animação. Cordialmente",
    )


def test_secao_vazia():
    assert ava_secao_vazia(VAZIO_HTML)
    assert not ava_secao_vazia(ARQUIVOS_HTML)


def test_selecionar_turmas_padrao_semestre_mais_recente():
    assert [t.codigo for t in selecionar_turmas(TURMAS)] == ["EC01020", "EC01099"]


def test_selecionar_turmas_por_disciplina_e_semestre():
    assert [t.semestre for t in selecionar_turmas(TURMAS, "circuitos")] == ["2024.4"]
    assert [t.semestre for t in selecionar_turmas(TURMAS, "EC01014", "todos")] == ["2022.2", "2024.4"]
    assert [t.codigo for t in selecionar_turmas(TURMAS, None, "2026.2")] == ["EC01035"]
    assert selecionar_turmas(TURMAS, "inexistente") == []


def test_consolidar_avisos_e_atividades():
    portal = [AvisoTurma(disciplina="SS", titulo="Prova", data="10/11/2026")]
    c1 = ConteudoTurmaVirtual(
        disciplina="SS",
        noticias=[
            AvisoTurma(disciplina="SS", titulo="Prova", data="10/11/2026 16:26"),
            AvisoTurma(disciplina="SS", titulo="Convolução", data="30/10/2026"),
        ],
    )
    c2 = ConteudoTurmaVirtual(
        disciplina="TCC", ultima_noticia=AvisoTurma(disciplina="TCC", titulo="Banca", data="01/12/2026")
    )
    avisos = consolidar_avisos(portal, [c1, c2])
    assert [a.titulo for a in avisos] == ["Prova", "Convolução", "Banca"]

    tarefa = AtividadePendente(disciplina="SS", tipo="Tarefa", titulo="Lista 1")
    c1.tarefas = [tarefa]
    c1.avaliacoes = [AtividadePendente(disciplina="SS", tipo="Avaliação", titulo="P2")]
    atividades = consolidar_atividades([tarefa], [c1])
    assert [(a.tipo, a.titulo) for a in atividades] == [("Tarefa", "Lista 1"), ("Avaliação", "P2")]
