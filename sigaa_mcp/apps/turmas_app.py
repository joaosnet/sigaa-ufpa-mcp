"""ExploradorTurmasApp — Interactive Course Explorer & UFPA Schedule Conflict Detector."""

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
    Button,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    Column,
    DataTable,
    DataTableColumn,
    If,
    Input,
    Row,
)

from sigaa_mcp.flows.turmas import (
    exportar_horarios_csv_flow,
    listar_disciplinas_ofertadas_flow,
)
from sigaa_mcp.session import session_manager
from sigaa_mcp.ui_components import build_dual_tool_result

TURMAS_APP_NAME = "sigaa-turmas"
turmas_app = FastMCPApp(TURMAS_APP_NAME)


def _format_oferta_rows(ofertadas: list[Any]) -> list[dict[str, str]]:
    return [
        {
            "codigo": o.codigo,
            "disciplina": o.disciplina,
            "turma": o.turma,
            "docente": o.docente or "-",
            "horario": o.horario_bruto or "-",
            "vagas": f"{o.vagas_ocupadas}/{o.vagas_ofertadas}" if o.vagas_ofertadas else "-",
            "compatibilidade": (
                "CHOQUE: " + "; ".join(o.detalhes_choque) if o.tem_choque_com_grade else "Livre"
            ),
        }
        for o in ofertadas
    ]


@turmas_app.tool(
    name="buscar_ofertas_ui",
    description="Callback da UI para buscar turmas ofertadas e cruzar horários com a grade do aluno.",
    model=False,
    timeout=75.0,
)
async def buscar_ofertas_ui(
    curso: str,
    turno: str = "",
    ano: str = "",
    periodo: str = "",
) -> dict[str, Any]:
    ano_int = int(ano.strip()) if ano.strip().isdigit() else None
    per_int = int(periodo.strip()) if periodo.strip().isdigit() else None
    ofertadas = await listar_disciplinas_ofertadas_flow(
        curso_ou_unidade=curso,
        turno=turno or None,
        ano=ano_int,
        periodo=per_int,
    )
    livres = sum(1 for o in ofertadas if not o.tem_choque_com_grade)
    return {
        "rows": _format_oferta_rows(ofertadas),
        "resumo_texto": f"{len(ofertadas)} turmas encontradas para '{curso}' ({livres} compatíveis sem choque de horário).",
    }


@turmas_app.tool(
    name="exportar_csv_ui",
    description="Callback da UI para exportar a grade horária atual do discente em CSV.",
    model=False,
    timeout=45.0,
)
async def exportar_csv_ui() -> dict[str, Any]:
    res = await exportar_horarios_csv_flow(enviar_drive=False)
    return {
        "mensagem": f"Grade horária ({res.semestre}) exportada para {res.arquivo_csv}.",
    }


@turmas_app.ui(
    name="abrir_explorador_turmas",
    title="Explorador de Turmas e Conflitos UFPA",
    description=(
        "Abre o Explorador Interativo de Turmas Ofertadas da UFPA com detector automático de choque "
        "de horário contra a matrícula atual do estudante."
    ),
    tags={"turmas", "horarios", "app"},
    annotations=ToolAnnotations(
        title="Explorador de Turmas e Conflitos UFPA",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    timeout=75.0,
)
async def abrir_explorador_turmas(
    curso: str = "",
    turno: str = "",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    termo_inicial = curso.strip() or (session_manager.perfil_atual.curso.split("/")[0].strip() if session_manager.perfil_atual.curso else "")
    ofertadas_iniciais = []
    aviso_inicial = "Digite o nome do curso ou faculdade e clique em Pesquisar Ofertas."

    if termo_inicial:
        try:
            ofertadas_iniciais = await listar_disciplinas_ofertadas_flow(
                curso_ou_unidade=termo_inicial,
                turno=turno or None,
                ctx=ctx,
            )
            livres = sum(1 for o in ofertadas_iniciais if not o.tem_choque_com_grade)
            aviso_inicial = f"{len(ofertadas_iniciais)} turmas carregadas para '{termo_inicial}' ({livres} sem choque de horário)."
        except Exception as exc:
            aviso_inicial = f"Pronto para busca manual ({exc})."

    state = {
        "curso": termo_inicial or "Engenharia da Computação",
        "turno": turno,
        "ano": "",
        "periodo": "",
        "rows": _format_oferta_rows(ofertadas_iniciais),
        "status_msg": aviso_inicial,
    }

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                CardTitle("Explorador de Ofertas e Simulador de Grade — UFPA")
                CardDescription(
                    "Pesquise disciplinas ofertadas por curso/instituto e identifique instantaneamente choques nos blocos M/T/N."
                )
            with CardContent():
                with Column(gap=3):
                    with Row(gap=2):
                        Input(
                            name="curso",
                            value=STATE.curso,
                            placeholder="Curso ou Instituto (ex.: Engenharia da Computação, Ciência da Computação)",
                        )
                        Input(
                            name="turno",
                            value=STATE.turno,
                            placeholder="Turno opcional (M, T, N)",
                        )
                    with Row(gap=2):
                        Button(
                            label="Pesquisar Ofertas",
                            variant="default",
                            on_click=CallTool(
                                tool=buscar_ofertas_ui,
                                arguments={
                                    "curso": STATE.curso,
                                    "turno": STATE.turno,
                                    "ano": STATE.ano,
                                    "periodo": STATE.periodo,
                                },
                                on_success=[
                                    SetState(key="rows", value=RESULT.rows),
                                    SetState(key="status_msg", value=RESULT.resumo_texto),
                                    ShowToast(message=RESULT.resumo_texto, variant="success"),
                                ],
                                on_error=ShowToast(message=ERROR, variant="error"),
                            ),
                        )
                        Button(
                            label="Exportar Minha Grade (CSV)",
                            variant="outline",
                            on_click=CallTool(
                                tool=exportar_csv_ui,
                                arguments={},
                                on_success=[
                                    SetState(key="status_msg", value=RESULT.mensagem),
                                    ShowToast(message=RESULT.mensagem, variant="success"),
                                ],
                                on_error=ShowToast(message=ERROR, variant="error"),
                            ),
                        )

                    with If(STATE.status_msg):
                        with Alert(variant="info"):
                            AlertDescription(STATE.status_msg)

                    DataTable(
                        columns=[
                            DataTableColumn(key="codigo", header="Código", sortable=True),
                            DataTableColumn(key="disciplina", header="Disciplina", sortable=True),
                            DataTableColumn(key="turma", header="Turma"),
                            DataTableColumn(key="docente", header="Docente", sortable=True),
                            DataTableColumn(key="horario", header="Horário", sortable=True),
                            DataTableColumn(key="vagas", header="Ocup./Vagas"),
                            DataTableColumn(key="compatibilidade", header="Conflito c/ Grade", sortable=True),
                        ],
                        rows=STATE.rows,
                        search=True,
                        search_placeholder="Filtrar resultados...",
                        paginated=True,
                        page_size=12,
                    )

    summary = {
        "curso_pesquisado": state["curso"],
        "turno": turno or "TODOS",
        "total_ofertadas": len(ofertadas_iniciais),
        "turmas": [o.model_dump(mode="json") for o in ofertadas_iniciais],
    }
    prefab = PrefabApp(title="Explorador de Turmas UFPA", state=state, view=view)
    return build_dual_tool_result(summary, prefab, fastmcp_app_name=TURMAS_APP_NAME)
