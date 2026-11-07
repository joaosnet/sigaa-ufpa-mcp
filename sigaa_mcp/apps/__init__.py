"""Composable FastMCP 4.1 Apps (Prefab UI) for SIGAA UFPA."""

from sigaa_mcp.apps.auth_app import auth_app, build_login_required_tool_result
from sigaa_mcp.apps.painel_app import painel_app
from sigaa_mcp.apps.perfil_app import perfil_app
from sigaa_mcp.apps.turmas_app import turmas_app

__all__ = [
    "auth_app",
    "painel_app",
    "turmas_app",
    "perfil_app",
    "build_login_required_tool_result",
]
