# Servidor FastMCP, Middlewares & Cache

> 46 nodes · cohesion 0.06

## Key Concepts

- **server.py** (42 connections) — `server.py`
- **test_mcp_server.py** (13 connections) — `tests/test_mcp_server.py`
- **create_mcp_server()** (9 connections) — `server.py`
- **register_prompts()** (8 connections) — `sigaa_mcp/prompts.py`
- **AppOnlyVisibilityMiddleware** (5 connections) — `server.py`
- **.on_list_tools()** (4 connections) — `server.py`
- **_background_http_warmup()** (4 connections) — `server.py`
- **invalidate_response_cache()** (4 connections) — `server.py`
- **server_lifespan()** (4 connections) — `server.py`
- **prompts.py** (4 connections) — `sigaa_mcp/prompts.py`
- **asyncio** (4 connections)
- **test_resources_and_path_traversal_guard()** (4 connections) — `tests/test_mcp_server.py`
- **test_visual_login_auto_card_when_logged_out()** (4 connections) — `tests/test_mcp_server.py`
- **FastMCP** (3 connections)
- **asyncio** (2 connections)
- **fastmcp_tools_base** (2 connections)
- **FastMCP** (2 connections)
- **MonkeyPatch** (2 connections)
- **test_cache_invalidation_on_session_change()** (2 connections) — `tests/test_mcp_server.py`
- **test_mcp_surface_and_zero_password_exposure()** (2 connections) — `tests/test_mcp_server.py`
- **CallNext** (1 connections)
- **contextlib** (1 connections)
- **fastmcp_apps** (1 connections)
- **fastmcp_apps_config** (1 connections)
- **fastmcp_server_middleware** (1 connections)
- *... and 21 more nodes in this community*

## Relationships

- [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md) (12 shared connections)
- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (6 shared connections)
- [Portal Web Local de Login Visual (/login)](Portal_Web_Local_de_Login_Visual_-login.md) (5 shared connections)
- [Logging Puro em Stderr](Logging_Puro_em_Stderr.md) (4 shared connections)
- [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md) (3 shared connections)
- [Resources MCP & Templates de Downloads](Resources_MCP_&_Templates_de_Downloads.md) (2 shared connections)

## Source Files

- `server.py`
- `sigaa_mcp/prompts.py`
- `tests/test_mcp_server.py`

## Audit Trail

- EXTRACTED: 90 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*