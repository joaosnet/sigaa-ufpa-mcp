"""AutenticacaoSigaaApp — Visual Login, Multi-Vínculo Selector, and Session Control."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCPApp
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations

from sigaa_mcp.auth import authenticate_with_credentials, logout_sigaa, select_vinculo
from sigaa_mcp.session import session_manager
from sigaa_mcp.ui_components import build_auth_prefab_app, build_dual_tool_result

AUTH_APP_NAME = "sigaa-auth"
auth_app = FastMCPApp(AUTH_APP_NAME)


@auth_app.tool(
    name="autenticar_credenciais_ui",
    description="Callback exclusivo da UI para autenticar usuário e senha diretamente em RAM.",
    model=False,
    timeout=60.0,
)
async def autenticar_credenciais_ui(
    usuario: str,
    senha: str,
    manter_sessao: bool = False,
    matricula_preferida: str = "",
) -> dict[str, Any]:
    estado = await authenticate_with_credentials(
        username=usuario,
        password=senha,
        manter_sessao=manter_sessao,
        matricula_preferida=matricula_preferida or None,
        allow_pause_for_visual_choice=True,
    )
    return estado.model_dump(mode="json")


@auth_app.tool(
    name="selecionar_vinculo_ui",
    description="Callback exclusivo da UI para escolher vínculo institucional no SIGAA.",
    model=False,
    timeout=45.0,
)
async def selecionar_vinculo_ui(identificador_ou_matricula: str) -> dict[str, Any]:
    estado = await select_vinculo(identificador_ou_matricula)
    return estado.model_dump(mode="json")


@auth_app.tool(
    name="encerrar_sessao_ui",
    description="Callback exclusivo da UI para encerrar sessão e limpar credenciais.",
    model=False,
    timeout=30.0,
)
async def encerrar_sessao_ui() -> dict[str, Any]:
    estado = await logout_sigaa()
    return estado.model_dump(mode="json")


def build_login_required_tool_result(aviso: str = "") -> ToolResult:
    """Build a dual ToolResult rendering the visual login card + fallback URL when unauthenticated."""
    estado = session_manager.get_estado_sessao(
        aviso
        or "Autenticação necessária no SIGAA UFPA. Use o formulário visual abaixo ou abra o portal local /login."
    )
    prefab = build_auth_prefab_app(
        estado=estado,
        login_tool_ref=autenticar_credenciais_ui,
        vinculo_tool_ref=selecionar_vinculo_ui,
        logout_tool_ref=encerrar_sessao_ui,
        aviso_contexto=aviso,
    )
    return build_dual_tool_result(estado, prefab, fastmcp_app_name=AUTH_APP_NAME)


@auth_app.ui(
    name="abrir_login_sigaa",
    title="Login Visual SIGAA UFPA",
    description=(
        "Abre a janela interativa de Login Visual do SIGAA UFPA (com senha mascarada que não passa pelo chat/IA, "
        "seleção de múltiplos vínculos, opção de manter sessão por cookies e botão de logout). "
        "Também informa a URL local http://localhost:8003/login para clientes sem suporte a MCP Apps."
    ),
    tags={"sessao", "login", "app"},
    annotations=ToolAnnotations(
        title="Login Visual SIGAA UFPA",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    timeout=30.0,
)
async def abrir_login_sigaa() -> ToolResult:
    estado = session_manager.get_estado_sessao()
    prefab = build_auth_prefab_app(
        estado=estado,
        login_tool_ref=autenticar_credenciais_ui,
        vinculo_tool_ref=selecionar_vinculo_ui,
        logout_tool_ref=encerrar_sessao_ui,
    )
    return build_dual_tool_result(estado, prefab, fastmcp_app_name=AUTH_APP_NAME)
