"""PainelAcademicoApp — Unified Multi-Tab Student Dashboard (FastMCPApp)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCPApp
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from prefab_ui.actions import SetState, ShowToast
from prefab_ui.actions.mcp import CallTool
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    ERROR,
    RESULT,
    STATE,
    Alert,
    AlertDescription,
    Badge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    Column,
    DataTable,
    DataTableColumn,
    Grid,
    If,
    Input,
    Metric,
    Row,
    Tab,
    Tabs,
)

from sigaa_mcp.apps.auth_app import build_login_required_tool_result
from sigaa_mcp.flows.academico import (
    baixar_historico_escolar_flow,
    consultar_notas_frequencia_flow,
    emitir_atestado_matricula_flow,
    obter_resumo_portal_flow,
)
from sigaa_mcp.session import AuthenticationRequiredError
from sigaa_mcp.ui_components import build_dual_tool_result

PAINEL_APP_NAME = "sigaa-painel"
painel_app = FastMCPApp(PAINEL_APP_NAME)


@painel_app.tool(
    name="emitir_historico_ui",
    description="Gera e baixa o PDF oficial do Histórico Escolar a partir do Painel Acadêmico.",
    model=False,
    timeout=90.0,
)
async def emitir_historico_ui(enviar_drive: bool = False) -> dict[str, Any]:
    res = await baixar_historico_escolar_flow(enviar_drive=enviar_drive)
    return {
        "mensagem": f"Histórico Escolar salvo em {res.arquivo_pdf} (CRG {res.crg or '-'}).",
        "resumo": res.model_dump(mode="json"),
    }


@painel_app.tool(
    name="emitir_atestado_ui",
    description="Emite o PDF oficial do Atestado de Matrícula a partir do Painel Acadêmico.",
    model=False,
    timeout=90.0,
)
async def emitir_atestado_ui(enviar_drive: bool = False) -> dict[str, Any]:
    res = await emitir_atestado_matricula_flow(enviar_drive=enviar_drive)
    return {
        "mensagem": f"Atestado emitido ({res.semestre}) — Código {res.codigo_verificacao} — salvo em {res.arquivo_pdf}.",
        "resumo": res.model_dump(mode="json"),
    }


@painel_app.tool(
    name="filtrar_notas_ui",
    description="Atualiza a tabela de notas e frequência filtrada por período letivo.",
    model=False,
    timeout=60.0,
)
async def filtrar_notas_ui(semestre: str = "") -> dict[str, Any]:
    notas = await consultar_notas_frequencia_flow(semestre=semestre or None)
    return {
        "rows": [
            {
                "semestre": n.semestre,
                "codigo": n.codigo,
                "disciplina": n.disciplina,
                "resultado": n.resultado,
                "faltas": n.faltas,
                "situacao": n.situacao,
            }
            for n in notas
        ],
        "mensagem": f"{len(notas)} registros carregados.",
    }


@painel_app.ui(
    name="abrir_painel_academico",
    title="Painel Acadêmico SIGAA UFPA",
    description=(
        "Abre o Painel Acadêmico interativo completo do discente (índices CRG/MC/IEA, turmas do semestre, "
        "boletim de notas e faltas, avisos/atividades e emissão com 1 clique de Histórico e Atestado)."
    ),
    tags={"academico", "painel", "app"},
    annotations=ToolAnnotations(
        title="Painel Acadêmico SIGAA UFPA",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    timeout=90.0,
)
async def abrir_painel_academico(ctx: Context = CurrentContext()) -> ToolResult:
    try:
        perfil, turmas, avisos, atividades = await obter_resumo_portal_flow(ctx=ctx)
        notas = await consultar_notas_frequencia_flow(ctx=ctx)
    except AuthenticationRequiredError as exc:
        return build_login_required_tool_result(str(exc))

    notas_rows = [
        {
            "semestre": n.semestre,
            "codigo": n.codigo,
            "disciplina": n.disciplina,
            "resultado": n.resultado,
            "faltas": n.faltas,
            "situacao": n.situacao,
        }
        for n in notas
    ]
    turmas_rows = [
        {
            "disciplina": f"{t.codigo} {t.disciplina}".strip(),
            "local": t.local or "-",
            "horario": t.horario_bruto or "-",
            "semestre": t.semestre or perfil.semestre_atual,
        }
        for t in turmas
    ]
    avisos_rows = [
        {"data": a.data or "-", "disciplina": a.disciplina, "titulo": a.titulo}
        for a in avisos
    ]

    state = {
        "semestre_filtro": "",
        "notas_rows": notas_rows,
        "ultimo_documento": "",
    }

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle(perfil.nome or "Portal do Discente — UFPA")
                    Badge(label=perfil.status or "ATIVO", variant="success")
                    if perfil.semestre_atual:
                        Badge(label=f"Período {perfil.semestre_atual}", variant="outline")
                CardDescription(f"Matrícula {perfil.matricula} • {perfil.curso}")
            with CardContent():
                with Grid(columns=4, gap=3):
                    Metric(label="CRG", value=perfil.indices.get("CRG", "-"))
                    Metric(label="MC", value=perfil.indices.get("MC", "-"))
                    Metric(label="IEA", value=perfil.indices.get("IEA", "-"))
                    Metric(label="Turmas Atuais", value=str(len(turmas)))

        with If(STATE.ultimo_documento):
            with Alert(variant="success"):
                AlertDescription(STATE.ultimo_documento)

        with Tabs(value="turmas"):
            with Tab(title="Turmas do Semestre", value="turmas"):
                DataTable(
                    columns=[
                        DataTableColumn(key="disciplina", header="Componente Curricular", sortable=True),
                        DataTableColumn(key="local", header="Local"),
                        DataTableColumn(key="horario", header="Horário SIGAA"),
                        DataTableColumn(key="semestre", header="Período"),
                    ],
                    rows=turmas_rows,
                    search=True,
                )

            with Tab(title="Notas e Frequência", value="notas"):
                with Column(gap=3):
                    with Row(gap=2):
                        Input(
                            name="semestre_filtro",
                            value=STATE.semestre_filtro,
                            placeholder="Filtrar período (ex.: 2026.4 ou vazio p/ todos)",
                        )
                        Button(
                            label="Filtrar Boletim",
                            on_click=CallTool(
                                tool=filtrar_notas_ui,
                                arguments={"semestre": STATE.semestre_filtro},
                                on_success=[
                                    SetState(key="notas_rows", value=RESULT.rows),
                                    ShowToast(message=RESULT.mensagem, variant="success"),
                                ],
                                on_error=ShowToast(message=ERROR, variant="error"),
                            ),
                        )
                    DataTable(
                        columns=[
                            DataTableColumn(key="semestre", header="Período", sortable=True),
                            DataTableColumn(key="codigo", header="Código", sortable=True),
                            DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                            DataTableColumn(key="resultado", header="Conceito", sortable=True),
                            DataTableColumn(key="faltas", header="Faltas", sortable=True),
                            DataTableColumn(key="situacao", header="Situação", sortable=True),
                        ],
                        rows=STATE.notas_rows,
                        search=True,
                        paginated=True,
                        page_size=10,
                    )

            with Tab(title="Avisos Recentes", value="avisos"):
                DataTable(
                    columns=[
                        DataTableColumn(key="data", header="Data", sortable=True),
                        DataTableColumn(key="disciplina", header="Turma", sortable=True),
                        DataTableColumn(key="titulo", header="Comunicado", sortable=True),
                    ],
                    rows=avisos_rows,
                    search=True,
                )

            with Tab(title="Documentos Oficiais (PDF)", value="docs"):
                with Row(gap=3):
                    Button(
                        label="Baixar Histórico Escolar (PDF)",
                        variant="default",
                        on_click=CallTool(
                            tool=emitir_historico_ui,
                            arguments={"enviar_drive": False},
                            on_success=[
                                SetState(key="ultimo_documento", value=RESULT.mensagem),
                                ShowToast(message=RESULT.mensagem, variant="success"),
                            ],
                            on_error=ShowToast(message=ERROR, variant="error"),
                        ),
                    )
                    Button(
                        label="Emitir Atestado de Matrícula (PDF)",
                        variant="outline",
                        on_click=CallTool(
                            tool=emitir_atestado_ui,
                            arguments={"enviar_drive": False},
                            on_success=[
                                SetState(key="ultimo_documento", value=RESULT.mensagem),
                                ShowToast(message=RESULT.mensagem, variant="success"),
                            ],
                            on_error=ShowToast(message=ERROR, variant="error"),
                        ),
                    )

    summary = {
        "perfil": perfil.model_dump(mode="json"),
        "turmas_matriculadas": [t.model_dump(mode="json") for t in turmas],
        "total_registros_notas": len(notas),
        "avisos_recentes": [a.model_dump(mode="json") for a in avisos[:10]],
        "atividades_portal": [at.model_dump(mode="json") for at in atividades],
    }
    prefab = PrefabApp(title="Painel Acadêmico SIGAA UFPA", state=state, view=view)
    return build_dual_tool_result(summary, prefab, fastmcp_app_name=PAINEL_APP_NAME)
