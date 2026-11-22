# Login SIGAA e Portal Web

> 54 nodes

## Key Concepts

- **auth.py** (37 connections) — `sigaa_mcp/auth.py`
- **ensure_authenticated_portal()** (32 connections) — `sigaa_mcp/auth.py`
- **web_login.py** (22 connections) — `sigaa_mcp/web_login.py`
- **EstadoSessao** (19 connections) — `sigaa_mcp/schemas.py`
- **invoke_portal_menu()** (16 connections) — `sigaa_mcp/auth.py`
- **_resolve_vinculo_if_needed()** (15 connections) — `sigaa_mcp/auth.py`
- **authenticate_with_credentials()** (14 connections) — `sigaa_mcp/auth.py`
- **select_vinculo()** (14 connections) — `sigaa_mcp/auth.py`
- **register_web_routes()** (12 connections) — `sigaa_mcp/web_login.py`
- **_bypass_intermediate_screens()** (11 connections) — `sigaa_mcp/auth.py`
- **_refresh_portal_snapshot_unlocked()** (10 connections) — `sigaa_mcp/auth.py`
- **test_web_login.py** (10 connections) — `tests/test_web_login.py`
- **parse_vinculos_html()** (9 connections) — `sigaa_mcp/parsers.py`
- **_verify_csrf()** (6 connections) — `sigaa_mcp/web_login.py`
- **test_login_and_logout_post_with_csrf()** (6 connections) — `tests/test_web_login.py`
- **Page** (6 connections)
- **login_route()** (5 connections) — `sigaa_mcp/web_login.py`
- **login_vinculo_route()** (5 connections) — `sigaa_mcp/web_login.py`
- **_click_vinculo_on_page()** (5 connections) — `sigaa_mcp/auth.py`
- **_is_portal_discente_ready()** (5 connections) — `sigaa_mcp/auth.py`
- **_is_vinculo_screen()** (5 connections) — `sigaa_mcp/auth.py`
- **_parse_form_urlencoded()** (5 connections) — `sigaa_mcp/web_login.py`
- **_render_login_html()** (5 connections) — `sigaa_mcp/web_login.py`
- **_extract_login_error()** (4 connections) — `sigaa_mcp/auth.py`
- **_is_login_screen()** (4 connections) — `sigaa_mcp/auth.py`
- *... and 29 more nodes in this community*

## Relationships

- [Fluxos Acadêmicos e Parsers](Fluxos_Acadêmicos_e_Parsers.md) (32 shared connections)
- [Ciclo de Vida Ocioso do Navegador](Ciclo_de_Vida_Ocioso_do_Navegador.md) (15 shared connections)
- [Apps MCP e UI de Autenticação](Apps_MCP_e_UI_de_Autenticação.md) (14 shared connections)
- [Frequência e Comparativo entre Semestres](Frequência_e_Comparativo_entre_Semestres.md) (12 shared connections)
- [Erros de Sessão e Reinício](Erros_de_Sessão_e_Reinício.md) (9 shared connections)
- [Servidor e Middlewares](Servidor_e_Middlewares.md) (7 shared connections)
- [Atualização de Foto de Perfil](Atualização_de_Foto_de_Perfil.md) (4 shared connections)
- [Configuração e Logging em Stderr](Configuração_e_Logging_em_Stderr.md) (2 shared connections)
- [Helpers de Configuração do Drive](Helpers_de_Configuração_do_Drive.md) (1 shared connections)

## Source Files

- `sigaa_mcp/auth.py`
- `sigaa_mcp/parsers.py`
- `sigaa_mcp/schemas.py`
- `sigaa_mcp/web_login.py`
- `tests/test_web_login.py`

## Audit Trail

- EXTRACTED: 190 (90%)
- INFERRED: 21 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*