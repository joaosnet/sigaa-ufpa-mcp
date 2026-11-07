# Portal Web Local de Login Visual (/login)

> 31 nodes · cohesion 0.11

## Key Concepts

- **web_login.py** (22 connections) — `sigaa_mcp/web_login.py`
- **EstadoSessao** (19 connections) — `sigaa_mcp/schemas.py`
- **register_web_routes()** (12 connections) — `sigaa_mcp/web_login.py`
- **test_web_login.py** (10 connections) — `tests/test_web_login.py`
- **_verify_csrf()** (6 connections) — `sigaa_mcp/web_login.py`
- **test_login_and_logout_post_with_csrf()** (6 connections) — `tests/test_web_login.py`
- **_parse_form_urlencoded()** (5 connections) — `sigaa_mcp/web_login.py`
- **login_route()** (5 connections) — `sigaa_mcp/web_login.py`
- **login_vinculo_route()** (5 connections) — `sigaa_mcp/web_login.py`
- **_render_login_html()** (5 connections) — `sigaa_mcp/web_login.py`
- **logout_route()** (4 connections) — `sigaa_mcp/web_login.py`
- **httpx** (3 connections)
- **_esc()** (3 connections) — `sigaa_mcp/web_login.py`
- **html** (2 connections)
- **pytest** (2 connections)
- **Request** (2 connections)
- **secrets** (2 connections)
- **FastMCP** (2 connections)
- **asyncio** (2 connections)
- **test_health_and_login_portal_modern_web_compliance()** (2 connections) — `tests/test_web_login.py`
- **fake_auth()** (2 connections) — `tests/test_web_login.py`
- **fake_logout()** (2 connections) — `tests/test_web_login.py`
- **Estado atual da sessão autenticada no SIGAA UFPA.** (1 connections) — `sigaa_mcp/schemas.py`
- **Local HTTP visual login portal (/login, /login/vinculo, /logout, /health) for…** (1 connections) — `sigaa_mcp/web_login.py`
- **Register /login, /login/vinculo, /logout, and /health on the FastMCP HTTP app.** (1 connections) — `sigaa_mcp/web_login.py`
- *... and 6 more nodes in this community*

## Relationships

- [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md) (12 shared connections)
- [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md) (7 shared connections)
- [Servidor FastMCP, Middlewares & Cache](Servidor_FastMCP,_Middlewares_&_Cache.md) (5 shared connections)
- [Parsers, Horários UFPA & Schemas Acadêmicos](Parsers,_Horários_UFPA_&_Schemas_Acadêmicos.md) (5 shared connections)
- [Fluxo de Troca e Simulação de Perfil](Fluxo_de_Troca_e_Simulação_de_Perfil.md) (2 shared connections)
- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (2 shared connections)
- [Logging Puro em Stderr](Logging_Puro_em_Stderr.md) (1 shared connections)

## Source Files

- `sigaa_mcp/schemas.py`
- `sigaa_mcp/web_login.py`
- `tests/test_web_login.py`

## Audit Trail

- EXTRACTED: 73 (88%)
- INFERRED: 10 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*