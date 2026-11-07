# Gerenciador de Sessão Playwright & Cofre RAM

> 54 nodes · cohesion 0.07

## Key Concepts

- **SigaaSessionManager** (43 connections) — `sigaa_mcp/session.py`
- **auth.py** (36 connections) — `sigaa_mcp/auth.py`
- **ensure_authenticated_portal()** (29 connections) — `sigaa_mcp/auth.py`
- **_resolve_vinculo_if_needed()** (15 connections) — `sigaa_mcp/auth.py`
- **authenticate_with_credentials()** (14 connections) — `sigaa_mcp/auth.py`
- **select_vinculo()** (14 connections) — `sigaa_mcp/auth.py`
- **_bypass_intermediate_screens()** (11 connections) — `sigaa_mcp/auth.py`
- **_refresh_portal_snapshot_unlocked()** (10 connections) — `sigaa_mcp/auth.py`
- **parse_vinculos_html()** (9 connections) — `sigaa_mcp/parsers.py`
- **Page** (6 connections)
- **_click_vinculo_on_page()** (5 connections) — `sigaa_mcp/auth.py`
- **_is_portal_discente_ready()** (5 connections) — `sigaa_mcp/auth.py`
- **_is_vinculo_screen()** (5 connections) — `sigaa_mcp/auth.py`
- **_extract_login_error()** (4 connections) — `sigaa_mcp/auth.py`
- **_is_login_screen()** (4 connections) — `sigaa_mcp/auth.py`
- **.ensure_browser_page()** (4 connections) — `sigaa_mcp/session.py`
- **.get_estado_sessao()** (4 connections) — `sigaa_mcp/session.py`
- **playwright_async_api** (3 connections)
- **Any** (3 connections)
- **._close_browser_unlocked()** (3 connections) — `sigaa_mcp/session.py`
- **.get_password_for_form()** (3 connections) — `sigaa_mcp/session.py`
- **.preferred_matricula()** (3 connections) — `sigaa_mcp/session.py`
- **.print_current_page_to_pdf()** (3 connections) — `sigaa_mcp/session.py`
- **.save_storage_state_if_enabled()** (3 connections) — `sigaa_mcp/session.py`
- **.set_ram_credentials()** (3 connections) — `sigaa_mcp/session.py`
- *... and 29 more nodes in this community*

## Relationships

- [Parsers, Horários UFPA & Schemas Acadêmicos](Parsers,_Horários_UFPA_&_Schemas_Acadêmicos.md) (46 shared connections)
- [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md) (14 shared connections)
- [Portal Web Local de Login Visual (/login)](Portal_Web_Local_de_Login_Visual_-login.md) (12 shared connections)
- [Fluxo de Troca e Simulação de Perfil](Fluxo_de_Troca_e_Simulação_de_Perfil.md) (5 shared connections)
- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (4 shared connections)
- [Servidor FastMCP, Middlewares & Cache](Servidor_FastMCP,_Middlewares_&_Cache.md) (3 shared connections)
- [Logging Puro em Stderr](Logging_Puro_em_Stderr.md) (1 shared connections)

## Source Files

- `sigaa_mcp/auth.py`
- `sigaa_mcp/parsers.py`
- `sigaa_mcp/session.py`

## Audit Trail

- EXTRACTED: 154 (85%)
- INFERRED: 27 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*