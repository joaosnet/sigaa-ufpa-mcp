"""Reusable Prefab UI components and dual ToolResult (UI + LLM JSON) serializer."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from fastmcp.tools import ToolResult
from fastmcp.tools.base import _prefab_to_json
from mcp.types import TextContent
from prefab_ui.actions import OpenLink, SetState, ShowToast
from prefab_ui.actions.mcp import CallTool
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
     ERROR,
    ITEM,
    RESULT,
    STATE,
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    Checkbox,
    Column,
    DataTable,
    DataTableColumn,
    Else,
    ForEach,
    Grid,
    Heading,
    If,
    Input,
    Metric,
    Muted,
    Progress,
    Row,
    Separator,
    Text,
)
from pydantic import BaseModel

from sigaa_mcp.schemas import (
    AtestadoResumo,
    AtividadePendente,
    AvisoTurma,
    DisciplinaOfertada,
    EstadoSessao,
    HistoricoResumo,
    HorariosExportadosResumo,
    NotaDisciplina,
    ResultadoTrocaPerfil,
)


def serialize_summary_json(payload: Any) -> str:
    """Serialize Pydantic models, lists of models, or dicts into clean UTF-8 JSON for LLMs."""
    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        data = [x.model_dump(mode="json") if isinstance(x, BaseModel) else x for x in payload]
    else:
        data = payload
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_dual_tool_result(
    summary_payload: Any,
    prefab_app: PrefabApp,
    fastmcp_app_name: Optional[str] = None,
) -> ToolResult:
    """Return BOTH LLM-readable JSON in content[0].text AND interactive Prefab UI in structured_content."""
    json_text = serialize_summary_json(summary_payload)
    structured = _prefab_to_json(prefab_app, fastmcp_app_name=fastmcp_app_name)
    return ToolResult(
        content=[TextContent(type="text", text=json_text)],
        structured_content=structured,
    )


def build_auth_prefab_app(
    estado: EstadoSessao,
    login_tool_ref: str | Callable[..., Any],
    vinculo_tool_ref: str | Callable[..., Any],
    logout_tool_ref: str | Callable[..., Any],
    aviso_contexto: str = "",
) -> PrefabApp:
    """Build the interactive Visual Login, Multi-Vínculo selector, and Session Management card."""
    initial_state = {
        "usuario": estado.usuario or "",
        "senha": "",
        "manter_sessao": estado.tem_sessao_salva_disco,
        "matricula_preferida": estado.matricula_ativa or "",
        "vinculo_escolhido": estado.matricula_ativa or "",
        "status": estado.model_dump(mode="json"),
        "aviso_contexto": aviso_contexto,
    }

    with Column(gap=4) as view:
        with If(STATE.aviso_contexto):
            with Alert(variant="warning"):
                AlertTitle("Autenticação Necessária no SIGAA UFPA")
                AlertDescription(STATE.aviso_contexto)

        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle("Acesso Institucional — SIGAA UFPA")
                    with If(STATE.status.autenticado):
                        Badge(label="Sessão Ativa", variant="success")
                    with Else():
                        Badge(label="Desconectado", variant="secondary")
                CardDescription(
                    "Suas credenciais trafegam diretamente entre esta interface e o navegador local em memória RAM, sem passar pelo chat ou modelo de IA."
                )

            with CardContent():
                with Column(gap=4):
                    with Alert(variant="info"):
                        AlertDescription(STATE.status.mensagem)

                    # Active session summary
                    with If(STATE.status.autenticado):
                        with Grid(columns=2, gap=3):
                            Metric(label="Discente", value=STATE.status.nome_discente)
                            Metric(label="Matrícula", value=STATE.status.matricula_ativa)
                            Metric(label="Curso", value=STATE.status.curso_ativo)
                            Metric(label="Período Letivo", value=STATE.status.semestre_atual)

                    # Multi-vínculo selector when multiple vínculos exist or awaiting selection
                    with If(STATE.status.aguardando_escolha_vinculo):
                        with Card():
                            with CardHeader():
                                CardTitle("Selecione o Vínculo Institucional")
                                CardDescription("Sua conta possui múltiplos vínculos cadastrados no SIGAA.")
                            with CardContent():
                                with Column(gap=2):
                                    with ForEach(STATE.status.vinculos):
                                        with Row(gap=2):
                                            Badge(label=ITEM.situacao, variant="outline")
                                            Text(ITEM.matricula)
                                            Muted(ITEM.curso)
                                            Button(
                                                label="Usar este vínculo",
                                                size="sm",
                                                on_click=CallTool(
                                                    tool=vinculo_tool_ref,
                                                    arguments={"identificador_ou_matricula": ITEM.matricula},
                                                    on_success=[
                                                        SetState(key="status", value=RESULT),
                                                        ShowToast(
                                                            message="Vínculo selecionado com sucesso!",
                                                            variant="success",
                                                        ),
                                                    ],
                                                    on_error=ShowToast(message=ERROR, variant="error"),
                                                ),
                                            )

                    # Login / Switch Account form
                    with Column(gap=3):
                        Heading("Entrar ou Trocar Conta", level=4)
                        Input(
                            name="usuario",
                            value=STATE.usuario,
                            placeholder="Usuário do SIGAA (ex.: joao.silva)",
                            aria_label="Usuário do SIGAA UFPA",
                            required=True,
                        )
                        Input(
                            name="senha",
                            input_type="password",
                            value=STATE.senha,
                            placeholder="Senha do SIGAA UFPA (mascarada)",
                            aria_label="Senha do SIGAA UFPA",
                            required=True,
                        )
                        Input(
                            name="matricula_preferida",
                            value=STATE.matricula_preferida,
                            placeholder="Matrícula específica (opcional para múltiplos vínculos)",
                            aria_label="Matrícula opcional",
                        )
                        Checkbox(
                            name="manter_sessao",
                            value=bool(estado.tem_sessao_salva_disco),
                            label="Manter sessão ativa (salva apenas cookies locais; nunca salva a senha em disco)",
                        )

            with CardFooter():
                with Row(gap=2):
                    Button(
                        label="Autenticar no SIGAA",
                        variant="default",
                        on_click=CallTool(
                            tool=login_tool_ref,
                            arguments={
                                "usuario": STATE.usuario,
                                "senha": STATE.senha,
                                "manter_sessao": STATE.manter_sessao,
                                "matricula_preferida": STATE.matricula_preferida,
                            },
                            on_success=[
                                SetState(key="status", value=RESULT),
                                SetState(key="senha", value=""),
                                SetState(key="aviso_contexto", value=""),
                                ShowToast(
                                    message="Resposta recebida do SIGAA UFPA.",
                                    variant="success",
                                ),
                            ],
                            on_error=ShowToast(message=ERROR, variant="error"),
                        ),
                    )
                    with If(STATE.status.autenticado):
                        Button(
                            label="Encerrar Sessão / Logout",
                            variant="destructive",
                            on_click=CallTool(
                                tool=logout_tool_ref,
                                arguments={},
                                on_success=[
                                    SetState(key="status", value=RESULT),
                                    SetState(key="senha", value=""),
                                    ShowToast(
                                        message="Sessão encerrada e credenciais limpas.",
                                        variant="info",
                                    ),
                                ],
                                on_error=ShowToast(message=ERROR, variant="error"),
                            ),
                        )
                    Button(
                        label="Abrir Portal Local (/login)",
                        variant="outline",
                        on_click=OpenLink(url=estado.login_url),
                    )

    return PrefabApp(title="Autenticação SIGAA UFPA", state=initial_state, view=view)


def build_historico_prefab_app(resumo: HistoricoResumo) -> PrefabApp:
    ch = resumo.carga_horaria_total
    pct = round((ch.integralizado / ch.exigido) * 100, 1) if ch.exigido > 0 else 0.0

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle("Histórico Escolar Oficial — UFPA")
                    Badge(label=resumo.status or "ATIVO", variant="success")
                CardDescription(f"{resumo.nome} • Matrícula {resumo.matricula} • {resumo.curso}")
            with CardContent():
                with Column(gap=4):
                    with Grid(columns=4, gap=3):
                        Metric(label="CRG", value=resumo.crg or "-")
                        Metric(label="MC", value=resumo.mc or "-")
                        Metric(label="IEA", value=resumo.iea or "-")
                        Metric(
                            label="Obrigatórias Pendentes",
                            value=str(resumo.obrigatorias_pendentes_qtd),
                        )
                    if ch.exigido > 0:
                        Separator()
                        Text(
                            f"Integralização Curricular: {ch.integralizado}h / {ch.exigido}h ({pct}%) — Pendente: {ch.pendente}h"
                        )
                        Progress(value=pct, min=0, max=100)
                    Separator()
                    Muted(f"PDF salvo em: {resumo.arquivo_pdf}")
                    if resumo.obrigatorias_pendentes_amostra:
                        Heading("Componentes Obrigatórios Pendentes", level=4)
                        for item in resumo.obrigatorias_pendentes_amostra[:8]:
                            Text(f"• {item}")

    return PrefabApp(title="Histórico Escolar SIGAA", view=view)


def build_atestado_prefab_app(resumo: AtestadoResumo) -> PrefabApp:
    rows = [
        {
            "codigo": t.codigo,
            "disciplina": t.disciplina,
            "turma": t.turma or "-",
            "docente": t.docente or "-",
            "horario": t.horario_bruto or "-",
        }
        for t in resumo.turmas
    ]
    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle(f"Atestado de Matrícula — {resumo.semestre or 'Vigente'}")
                    if resumo.codigo_verificacao:
                        Badge(label=f"Verificação: {resumo.codigo_verificacao}", variant="outline")
                CardDescription(f"{resumo.nome} • Matrícula {resumo.matricula} • {resumo.curso}")
            with CardContent():
                with Column(gap=3):
                    DataTable(
                        columns=[
                            DataTableColumn(key="codigo", header="Código", sortable=True),
                            DataTableColumn(key="disciplina", header="Componente Curricular", sortable=True),
                            DataTableColumn(key="turma", header="Turma"),
                            DataTableColumn(key="docente", header="Docente"),
                            DataTableColumn(key="horario", header="Horário SIGAA"),
                        ],
                        rows=rows,
                        search=True,
                        search_placeholder="Filtrar componente...",
                    )
                    Muted(f"PDF oficial gerado em: {resumo.arquivo_pdf}")

    return PrefabApp(title="Atestado de Matrícula SIGAA", view=view)


def build_notas_prefab_app(
    notas: list[NotaDisciplina], semestre_filtro: Optional[str] = None
) -> PrefabApp:
    rows = [
        {
            "semestre": n.semestre,
            "codigo": n.codigo,
            "disciplina": n.disciplina,
            "u1": n.unidade_1,
            "u2": n.unidade_2,
            "resultado": n.resultado,
            "faltas": n.faltas,
            "situacao": n.situacao,
        }
        for n in notas
    ]
    aprovadas = sum(1 for n in notas if "APROVAD" in n.situacao.upper())
    matriculadas = sum(1 for n in notas if "MATRICULAD" in n.situacao.upper())

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                CardTitle(
                    f"Boletim Acadêmico e Frequência {f'({semestre_filtro})' if semestre_filtro else '(Todos os Períodos)'}"
                )
                CardDescription("Conceitos oficiais UFPA (E, B, R, I, S) e controle de faltas por componente.")
            with CardContent():
                with Column(gap=4):
                    with Grid(columns=3, gap=3):
                        Metric(label="Registros", value=str(len(notas)))
                        Metric(label="Aprovações", value=str(aprovadas))
                        Metric(label="Em Curso", value=str(matriculadas))
                    DataTable(
                        columns=[
                            DataTableColumn(key="semestre", header="Período", sortable=True),
                            DataTableColumn(key="codigo", header="Código", sortable=True),
                            DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                            DataTableColumn(key="u1", header="Unid. 1"),
                            DataTableColumn(key="u2", header="Unid. 2"),
                            DataTableColumn(key="resultado", header="Conceito/Média", sortable=True),
                            DataTableColumn(key="faltas", header="Faltas", sortable=True),
                            DataTableColumn(key="situacao", header="Situação", sortable=True),
                        ],
                        rows=rows,
                        search=True,
                        search_placeholder="Buscar disciplina, código ou período...",
                        paginated=True,
                        page_size=12,
                    )

    return PrefabApp(title="Notas e Frequência SIGAA", view=view)


def build_horarios_prefab_app(resumo: HorariosExportadosResumo) -> PrefabApp:
    rows = []
    for turma in resumo.turmas:
        if not turma.slots_decodificados:
            rows.append(
                {
                    "dia": "Sem horário fixo",
                    "faixa": "-",
                    "turno": "-",
                    "disciplina": f"{turma.codigo} {turma.disciplina}".strip(),
                    "local": turma.local or "-",
                    "sigaa": turma.horario_bruto or "-",
                }
            )
        else:
            for s in turma.slots_decodificados:
                rows.append(
                    {
                        "dia": s.dia_nome,
                        "faixa": f"{s.hora_inicio} - {s.hora_fim}",
                        "turno": f"{s.turno_nome} ({s.turno_codigo}{s.slot_numero})",
                        "disciplina": f"{turma.codigo} {turma.disciplina}".strip(),
                        "local": turma.local or "-",
                        "sigaa": s.codigo_original,
                    }
                )

    with Column(gap=4) as view:
        if resumo.choques_horario:
            with Alert(variant="destructive"):
                AlertTitle(f"{len(resumo.choques_horario)} Choque(s) de Horário Detectado(s)")
                AlertDescription(
                    " | ".join(
                        f"{c.dia_nome} {c.faixa_horaria}: {', '.join(c.disciplinas)}"
                        for c in resumo.choques_horario
                    )
                )
        with Card():
            with CardHeader():
                CardTitle(f"Grade Horária Semanal — {resumo.semestre}")
                CardDescription(f"Arquivo CSV exportado em: {resumo.arquivo_csv}")
            with CardContent():
                DataTable(
                    columns=[
                        DataTableColumn(key="dia", header="Dia da Semana", sortable=True),
                        DataTableColumn(key="faixa", header="Horário", sortable=True),
                        DataTableColumn(key="turno", header="Bloco UFPA"),
                        DataTableColumn(key="disciplina", header="Componente Curricular", sortable=True),
                        DataTableColumn(key="local", header="Local"),
                        DataTableColumn(key="sigaa", header="Código"),
                    ],
                    rows=rows,
                    search=True,
                )

    return PrefabApp(title="Grade Horária UFPA", view=view)


def build_avisos_prefab_app(avisos: list[AvisoTurma]) -> PrefabApp:
    rows = [
        {
            "data": a.data or "-",
            "disciplina": a.disciplina,
            "titulo": a.titulo,
            "origem": a.origem,
        }
        for a in avisos
    ]
    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                CardTitle(f"Avisos e Notícias das Turmas ({len(avisos)})")
                CardDescription("Comunicados publicados no Portal do Discente e Turmas Virtuais (AVA).")
            with CardContent():
                DataTable(
                    columns=[
                        DataTableColumn(key="data", header="Data", sortable=True),
                        DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                        DataTableColumn(key="titulo", header="Notícia / Comunicado", sortable=True),
                        DataTableColumn(key="origem", header="Origem"),
                    ],
                    rows=rows,
                    search=True,
                    search_placeholder="Filtrar avisos...",
                )
    return PrefabApp(title="Avisos das Turmas SIGAA", view=view)


def build_atividades_prefab_app(atividades: list[AtividadePendente]) -> PrefabApp:
    rows = [
        {
            "prazo": a.prazo or "-",
            "tipo": a.tipo,
            "disciplina": a.disciplina,
            "titulo": a.titulo,
            "situacao": a.situacao,
        }
        for a in atividades
    ]
    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                CardTitle(f"Atividades, Questionários e Avaliações ({len(atividades)})")
                CardDescription(" Monitoramento consolidado do Portal do Discente e salas virtuais (AVA).")
            with CardContent():
                if not rows:
                    with Alert(variant="success"):
                        AlertTitle("Nenhuma pendência aberta encontrada")
                        AlertDescription("Não há tarefas ou questionários pendentes nas turmas matriculadas.")
                else:
                    DataTable(
                        columns=[
                            DataTableColumn(key="prazo", header="Prazo / Período", sortable=True),
                            DataTableColumn(key="tipo", header="Tipo", sortable=True),
                            DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                            DataTableColumn(key="titulo", header="Atividade", sortable=True),
                            DataTableColumn(key="situacao", header="Status"),
                        ],
                        rows=rows,
                        search=True,
                    )
    return PrefabApp(title="Atividades Pendentes SIGAA", view=view)


def build_ofertadas_prefab_app(
    ofertadas: list[DisciplinaOfertada], termo_busca: str
) -> PrefabApp:
    rows = [
        {
            "codigo": o.codigo,
            "disciplina": o.disciplina,
            "turma": o.turma,
            "docente": o.docente or "-",
            "horario": o.horario_bruto or "-",
            "vagas": f"{o.vagas_ocupadas}/{o.vagas_ofertadas}" if o.vagas_ofertadas else "-",
            "conflito": "CHOQUE: " + "; ".join(o.detalhes_choque) if o.tem_choque_com_grade else "Livre",
        }
        for o in ofertadas
    ]
    livres = sum(1 for o in ofertadas if not o.tem_choque_com_grade)
    choques = sum(1 for o in ofertadas if o.tem_choque_com_grade)

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                CardTitle(f"Oferta de Turmas UFPA — {termo_busca}")
                CardDescription(f"{len(ofertadas)} turmas localizadas ({livres} sem choque com sua grade, {choques} com conflito).")
            with CardContent():
                DataTable(
                    columns=[
                        DataTableColumn(key="codigo", header="Código", sortable=True),
                        DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                        DataTableColumn(key="turma", header="Turma"),
                        DataTableColumn(key="docente", header="Docente", sortable=True),
                        DataTableColumn(key="horario", header="Horário", sortable=True),
                        DataTableColumn(key="vagas", header="Ocup./Vagas"),
                        DataTableColumn(key="conflito", header="Compatibilidade", sortable=True),
                    ],
                    rows=rows,
                    search=True,
                    search_placeholder="Filtrar por disciplina, docente ou horário...",
                    paginated=True,
                    page_size=15,
                )
    return PrefabApp(title="Explorador de Ofertas UFPA", view=view)


def build_perfil_result_prefab_app(resultado: ResultadoTrocaPerfil) -> PrefabApp:
    with Column(gap=3) as view:
        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle("Atualização de Perfil Discente — SIGAA UFPA")
                    Badge(
                        label="Simulação (dry_run)" if resultado.modo_simulacao else ("Sucesso" if resultado.sucesso else "Erro"),
                        variant="info" if resultado.modo_simulacao else ("success" if resultado.sucesso else "destructive"),
                    )
                CardDescription(resultado.mensagem)
            with CardContent():
                with Grid(columns=2, gap=3):
                    Metric(label="Arquivo Validado", value=resultado.arquivo_validado or "-")
                    Metric(label="Origem", value=resultado.origem_imagem or "-")
    return PrefabApp(title="Estúdio de Perfil SIGAA", view=view)
