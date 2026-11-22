# Servidor e Middlewares

> 45 nodes

## Key Concepts

- **server.py** (42 connections) — `server.py`
- **test_mcp_server.py** (12 connections) — `tests/test_mcp_server.py`
- **create_mcp_server()** (9 connections) — `server.py`
- **register_prompts()** (8 connections) — `sigaa_mcp/prompts.py`
- **asyncio** (7 connections)
- **AppOnlyVisibilityMiddleware** (5 connections) — `server.py`
- **.on_list_tools()** (4 connections) — `server.py`
- **_background_http_warmup()** (4 connections) — `server.py`
- **server_lifespan()** (4 connections) — `server.py`
- **test_resources_and_path_traversal_guard()** (4 connections) — `tests/test_mcp_server.py`
- **prompts.py** (4 connections) — `sigaa_mcp/prompts.py`
- **test_visual_login_auto_card_when_logged_out()** (3 connections) — `tests/test_mcp_server.py`
- **FastMCP** (3 connections)
- **invalidate_response_cache()** (2 connections) — `server.py`
- **test_cache_invalidation_on_session_change()** (2 connections) — `tests/test_mcp_server.py`
- **test_mcp_surface_and_zero_password_exposure()** (2 connections) — `tests/test_mcp_server.py`
- **MonkeyPatch** (2 connections)
- **FastMCP** (2 connections)
- **fastmcp_tools_base** (2 connections)
- **main()** (1 connections) — `server.py`
- **auditar_integralizacao_curricular()** (1 connections) — `sigaa_mcp/prompts.py`
- **briefing_semana_academica()** (1 connections) — `sigaa_mcp/prompts.py`
- **planejar_matricula_semestre()** (1 connections) — `sigaa_mcp/prompts.py`
- **CallNext** (1 connections)
- **Middleware** (1 connections)
- *... and 20 more nodes in this community*

## Relationships

- [Apps MCP e UI de Autenticação](Apps_MCP_e_UI_de_Autenticação.md) (12 shared connections)
- [Login SIGAA e Portal Web](Login_SIGAA_e_Portal_Web.md) (7 shared connections)
- [Recursos MCP](Recursos_MCP.md) (4 shared connections)
- [Configuração e Logging em Stderr](Configuração_e_Logging_em_Stderr.md) (4 shared connections)
- [Erros de Sessão e Reinício](Erros_de_Sessão_e_Reinício.md) (3 shared connections)
- [Ciclo de Vida Ocioso do Navegador](Ciclo_de_Vida_Ocioso_do_Navegador.md) (2 shared connections)
- [Helpers de Configuração do Drive](Helpers_de_Configuração_do_Drive.md) (1 shared connections)

## Source Files

- `server.py`
- `sigaa_mcp/prompts.py`
- `tests/test_mcp_server.py`

## Audit Trail

- EXTRACTED: 89 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*