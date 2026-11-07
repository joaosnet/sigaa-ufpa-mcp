"""Model-facing FastMCP 4.1 tools with Safety Annotations, Dual UI+JSON ToolResult, and Login Auto-Card."""

from __future__ import annotations

from typing import Optional

from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations

from sigaa_mcp.apps.auth_app import (
    AUTH_APP_NAME,
    autenticar_credenciais_ui,
    build_login_required_tool_result,
    encerrar_sessao_ui,
    selecionar_vinculo_ui,
)
from sigaa_mcp.auth import logout_sigaa, restart_sigaa_session
from sigaa_mcp.flows.academico import (
    baixar_historico_escolar_flow,
    consultar_notas_frequencia_flow,
    emitir_atestado_matricula_flow,
)
from sigaa_mcp.flows.perfil import trocar_imagem_perfil_flow
from sigaa_mcp.flows.turmas import (
    exportar_horarios_csv_flow,
    listar_atividades_pendentes_flow,
    listar_avisos_turmas_flow,
    listar_disciplinas_ofertadas_flow,
)
from sigaa_mcp.session import AuthenticationRequiredError
from sigaa_mcp.ui_components import (
    build_atestado_prefab_app,
    build_atividades_prefab_app,
    build_auth_prefab_app,
    build_avisos_prefab_app,
    build_dual_tool_result,
    build_historico_prefab_app,
    build_horarios_prefab_app,
    build_notas_prefab_app,
    build_ofertadas_prefab_app,
    build_perfil_result_prefab_app,
)


def register_tools(mcp: FastMCP) -> None:
    """Register all 10 model-facing SIGAA UFPA tools on the FastMCP server."""

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"academico", "documentos"},
        annotations=ToolAnnotations(
            title="Baixar Histórico Escolar (PDF + Resumo)",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=90.0,
    )
    async def baixar_historico_escolar(
        enviar_drive: bool = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Gera e baixa o PDF oficial do Histórico Escolar no SIGAA UFPA, extraindo CRG, MC, IEA, carga horária e disciplinas pendentes."""
        try:
            resumo = await baixar_historico_escolar_flow(enviar_drive=enviar_drive, ctx=ctx)
            return build_dual_tool_result(resumo, build_historico_prefab_app(resumo))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"academico", "documentos"},
        annotations=ToolAnnotations(
            title="Emitir Atestado de Matrícula (PDF + Grade)",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=90.0,
    )
    async def emitir_atestado_matricula(
        enviar_drive: bool = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Emite o Atestado de Matrícula oficial do período vigente (ou suplementar) em PDF, retornando código de verificação e turmas."""
        try:
            resumo = await emitir_atestado_matricula_flow(enviar_drive=enviar_drive, ctx=ctx)
            return build_dual_tool_result(resumo, build_atestado_prefab_app(resumo))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"academico", "notas"},
        annotations=ToolAnnotations(
            title="Consultar Notas e Frequência",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=60.0,
    )
    async def consultar_notas_frequencia(
        semestre: Optional[str] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Consulta o boletim oficial 'Minhas Notas' com conceitos (E, B, R, I, S), avaliações parciais, faltas e situação por semestre."""
        try:
            notas = await consultar_notas_frequencia_flow(semestre=semestre, ctx=ctx)
            payload = {
                "semestre_filtro": semestre or "TODOS",
                "total_disciplinas": len(notas),
                "disciplinas": [n.model_dump(mode="json") for n in notas],
            }
            return build_dual_tool_result(payload, build_notas_prefab_app(notas, semestre))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"turmas", "ava"},
        annotations=ToolAnnotations(
            title="Listar Atividades, Questionários e Avaliações",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=90.0,
    )
    async def listar_atividades_pendentes(
        incluir_concluidas: bool = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Lista tarefas, questionários e avaliações agendadas no Portal do Discente e nas salas virtuais (AVA) das turmas matriculadas."""
        try:
            atividades = await listar_atividades_pendentes_flow(
                incluir_concluidas=incluir_concluidas, ctx=ctx
            )
            payload = {
                "incluir_concluidas": incluir_concluidas,
                "total_atividades": len(atividades),
                "atividades": [a.model_dump(mode="json") for a in atividades],
            }
            return build_dual_tool_result(payload, build_atividades_prefab_app(atividades))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"turmas", "horarios"},
        annotations=ToolAnnotations(
            title="Exportar Grade Horária Semanal (CSV)",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=60.0,
    )
    async def exportar_horarios_csv(
        enviar_drive: bool = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Decodifica os códigos de horário da UFPA (ex.: 24M56) em dias e faixas de 50 min, detecta choques e exporta arquivo CSV UTF-8."""
        try:
            resumo = await exportar_horarios_csv_flow(enviar_drive=enviar_drive, ctx=ctx)
            return build_dual_tool_result(resumo, build_horarios_prefab_app(resumo))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"turmas", "ava"},
        annotations=ToolAnnotations(
            title="Listar Avisos e Notícias das Turmas",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=90.0,
    )
    async def listar_avisos_turmas(
        disciplina_filtro: Optional[str] = None,
        limite_por_turma: int = 5,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Busca comunicados e notícias recentes publicados pelos professores no Portal do Discente e no AVA de cada turma."""
        try:
            avisos = await listar_avisos_turmas_flow(
                disciplina_filtro=disciplina_filtro,
                limite_por_turma=limite_por_turma,
                ctx=ctx,
            )
            payload = {
                "disciplina_filtro": disciplina_filtro or "TODAS",
                "total_avisos": len(avisos),
                "avisos": [a.model_dump(mode="json") for a in avisos],
            }
            return build_dual_tool_result(payload, build_avisos_prefab_app(avisos))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"turmas", "oferta"},
        annotations=ToolAnnotations(
            title="Listar Disciplinas Ofertadas e Conflitos",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=75.0,
    )
    async def listar_disciplinas_ofertadas(
        curso: str,
        turno: Optional[str] = None,
        ano: Optional[int] = None,
        periodo: Optional[int] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Pesquisa disciplinas e turmas ofertadas por curso ou instituto na UFPA, apontando automaticamente choques de horário com sua grade."""
        ofertadas = await listar_disciplinas_ofertadas_flow(
            curso_ou_unidade=curso,
            turno=turno,
            ano=ano,
            periodo=periodo,
            ctx=ctx,
        )
        payload = {
            "curso": curso,
            "turno": turno or "TODOS",
            "total_turmas": len(ofertadas),
            "turmas_sem_choque": sum(1 for o in ofertadas if not o.tem_choque_com_grade),
            "turmas": [o.model_dump(mode="json") for o in ofertadas],
        }
        return build_dual_tool_result(payload, build_ofertadas_prefab_app(ofertadas, curso))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"perfil", "escrita"},
        annotations=ToolAnnotations(
            title="Trocar Foto e Descrição de Perfil no SIGAA",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
        timeout=75.0,
    )
    async def trocar_imagem_perfil(
        drive_file_id: Optional[str] = None,
        caminho_ou_url: Optional[str] = None,
        descricao: Optional[str] = None,
        dry_run: bool = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Atualiza (ou simula com dry_run=True) a foto e descrição do perfil discente via arquivo local, URL HTTPS, data URI ou Google Drive."""
        try:
            res = await trocar_imagem_perfil_flow(
                drive_file_id=drive_file_id,
                caminho_ou_url=caminho_ou_url,
                descricao=descricao,
                dry_run=dry_run,
                ctx=ctx,
            )
            return build_dual_tool_result(res, build_perfil_result_prefab_app(res))
        except AuthenticationRequiredError as exc:
            return build_login_required_tool_result(str(exc))

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"sessao"},
        annotations=ToolAnnotations(
            title="Reiniciar Sessão do Navegador SIGAA",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=60.0,
    )
    async def reiniciar_sessao() -> ToolResult:
        """Reinicia o contexto Chromium do Playwright, invalida o cache temporário e reautentica a sessão ativa se disponível."""
        estado = await restart_sigaa_session()
        prefab = build_auth_prefab_app(
            estado=estado,
            login_tool_ref=autenticar_credenciais_ui,
            vinculo_tool_ref=selecionar_vinculo_ui,
            logout_tool_ref=encerrar_sessao_ui,
        )
        return build_dual_tool_result(estado, prefab, fastmcp_app_name=AUTH_APP_NAME)

    @mcp.tool(
        app=True,
        output_schema=None,
        tags={"sessao"},
        annotations=ToolAnnotations(
            title="Encerrar Sessão / Logout Seguro do SIGAA",
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
        timeout=45.0,
    )
    async def encerrar_sessao() -> ToolResult:
        """Faz logoff no SIGAA UFPA, apaga credenciais da memória RAM, remove storage_state.json salvo e invalida todo o cache."""
        estado = await logout_sigaa()
        prefab = build_auth_prefab_app(
            estado=estado,
            login_tool_ref=autenticar_credenciais_ui,
            vinculo_tool_ref=selecionar_vinculo_ui,
            logout_tool_ref=encerrar_sessao_ui,
        )
        return build_dual_tool_result(estado, prefab, fastmcp_app_name=AUTH_APP_NAME)
