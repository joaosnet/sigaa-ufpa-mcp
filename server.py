"""SIGAA UFPA MCP Server — FastMCP 4.1 + FastMCP Apps + Visual Login + Zero External AI Tokens."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP
from fastmcp.apps import UI_EXTENSION_ID
from fastmcp.apps.config import is_model_visible
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.server.middleware.caching import CallToolSettings, ResponseCachingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.tools.base import Tool
from key_value.aio.stores.memory import MemoryStore
from loguru import logger

from sigaa_mcp.apps import auth_app, painel_app, perfil_app, turmas_app
from sigaa_mcp.auth import ensure_authenticated_portal
from sigaa_mcp.config import configure_stderr_logging, settings
from sigaa_mcp.prompts import register_prompts
from sigaa_mcp.resources import register_resources
from sigaa_mcp.session import session_manager
from sigaa_mcp.tools import register_tools
from sigaa_mcp.web_login import register_web_routes

# Guarantee 100% stderr logging before any MCP transport or middleware initializes
configure_stderr_logging(settings.log_level)
_stdlib_logger = logging.getLogger("sigaa_ufpa_mcp")

cache_store = MemoryStore()


async def invalidate_response_cache() -> None:
    """Purge all cached tool responses whenever login, vínculo switch, logout, or session reset happens."""
    cache_dict = getattr(cache_store, "_cache", {})
    for col in list(cache_dict.keys()):
        keys = await cache_store.keys(collection=col)
        if keys:
            await cache_store.delete_many(keys, collection=col)
    logger.debug("Cache de respostas do FastMCP invalidado.")


session_manager.register_change_listener(invalidate_response_cache)


async def _background_http_warmup() -> None:
    """Optional non-blocking session warmup in HTTP/Docker mode when credentials or cookies exist."""
    if not (session_manager.has_credentials or settings.storage_state_path.is_file()):
        logger.info(
            f"Servidor pronto em modo Zero-Env. Faça Login Visual no chat ou acesse {settings.public_login_url}"
        )
        return
    try:
        async with session_manager.lock:
            await ensure_authenticated_portal(session=session_manager)
        logger.info("Warmup em background da sessão SIGAA concluído.")
    except Exception as exc:
        logger.warning(f"Warmup opcional em background adiado até o primeiro uso: {exc}")


_HTTP_SERVER_MODE = False


@asynccontextmanager
async def server_lifespan(_server: FastMCP) -> AsyncIterator[dict[str, object]]:
    warmup_task: asyncio.Task[None] | None = None
    if _HTTP_SERVER_MODE and settings.mcp_transport in {"http", "streamable-http", "sse"}:
        warmup_task = asyncio.create_task(_background_http_warmup())
    try:
        yield {"session_manager": session_manager}
    finally:
        if warmup_task is not None and not warmup_task.done():
            warmup_task.cancel()
        await session_manager.close()


CACHED_READ_TOOLS = [
    "consultar_notas_frequencia",
    "listar_avisos_turmas",
    "listar_atividades_pendentes",
    "listar_disciplinas_ofertadas",
]


class AppOnlyVisibilityMiddleware(Middleware):
    """Enforce SEP-1865 app-only tool hiding even for legacy MCP clients without UI_EXTENSION_ID."""

    async def on_list_tools(
        self,
        context: MiddlewareContext[object],
        call_next: CallNext[object, list[Tool]],
    ) -> list[Tool]:
        tools = await call_next(context)
        ctx = context.fastmcp_context
        if ctx is not None and ctx.client_supports_extension(UI_EXTENSION_ID):
            return tools
        return [t for t in tools if is_model_visible(t)]


def create_mcp_server() -> FastMCP:
    """Construct and wire the complete FastMCP 4.1 server instance."""
    server = FastMCP(
        name="SIGAA UFPA Automator",
        version="2.0.0",
        instructions=(
            "Servidor MCP determinístico (zero tokens de IA externa) para o SIGAA da Universidade Federal do Pará (UFPA). "
            "Suporta Login Visual seguro (`abrir_login_sigaa` ou portal local `/login`) sem expor senha ao chat/LLM, "
            "4 aplicativos interativos (`abrir_login_sigaa`, `abrir_painel_academico`, `abrir_explorador_turmas`, "
            "`abrir_estudio_perfil`), emissão de documentos oficiais em PDF (Histórico e Atestado), boletim de notas/faltas, "
            "grade horária em CSV com detecção de choque de horários e atualização opcional de perfil."
        ),
        lifespan=server_lifespan,
        middleware=[
            ErrorHandlingMiddleware(logger=_stdlib_logger, include_traceback=False),
            TimingMiddleware(logger=_stdlib_logger),
            AppOnlyVisibilityMiddleware(),
            ResponseCachingMiddleware(
                cache_storage=cache_store,
                call_tool_settings=CallToolSettings(
                    enabled=True,
                    ttl=180,
                    included_tools=CACHED_READ_TOOLS,
                ),
            ),
            ResponseLimitingMiddleware(max_size=900_000),
        ],
    )

    # Mount the 4 interactive FastMCPApp providers
    server.add_provider(auth_app)
    server.add_provider(painel_app)
    server.add_provider(turmas_app)
    server.add_provider(perfil_app)

    # Register tools, prompts, resources, and local HTTP visual login fallback
    register_tools(server)
    register_prompts(server)
    register_resources(server)
    register_web_routes(server)

    return server


mcp = create_mcp_server()


def main() -> None:
    global _HTTP_SERVER_MODE
    transport = settings.mcp_transport
    if transport in {"http", "streamable-http", "sse"}:
        _HTTP_SERVER_MODE = True
        actual_transport = "sse" if transport == "sse" else "http"
        logger.info(
            f"Iniciando SIGAA UFPA MCP v2.0 ({actual_transport}) em http://{settings.mcp_host}:{settings.mcp_port}/mcp "
            f"| Login Visual: {settings.public_login_url}"
        )
        mcp.run(
            transport=actual_transport,
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        logger.info("Iniciando SIGAA UFPA MCP v2.0 em transporte stdio (Lazy Login ativo).")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
