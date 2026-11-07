# Graph Report - sigaa-ufpa-mcp  (2026-11-07)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 482 nodes · 1203 edges · 22 communities (13 shown, 9 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 88 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ea03672b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos
- Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação
- Comunidade 2 — Gerenciador de Sessão Playwright & Cofre RAM
- Comunidade 3 — Servidor FastMCP, Middlewares & Cache
- Comunidade 4 — Catálogo Docker MCP UFPA
- Comunidade 5 — Portal Web Local de Login Visual (/login)
- Comunidade 6 — Infraestrutura Docker Compose & noVNC
- Comunidade 7 — Serviço OAuth 2.0 Google Drive
- Comunidade 8 — Logging Puro em Stderr
- Comunidade 9 — Fluxo de Troca e Simulação de Perfil
- Comunidade 11 — Resources MCP & Templates de Downloads
- Comunidade 12 — Manifesto de Deploy FastMCP
- Comunidade 13 — PainelAcadêmicoApp (FastMCPApp)
- Comunidade 14 — ExploradorTurmasApp (FastMCPApp)
- Comunidade 15 — PerfilDiscenteApp (FastMCPApp)
- Comunidade 16 — Configurações Tipadas de Runtime
- Comunidade 17 — Configuração Cliente MCP Local
- Comunidade 21 — Metadados do Projeto Python

## God Nodes (most connected - your core abstractions)
1. `SigaaSessionManager` - 43 edges
2. `register_tools()` - 37 edges
3. `ensure_authenticated_portal()` - 29 edges
4. `build_dual_tool_result()` - 27 edges
5. `GoogleDriveService` - 22 edges
6. `build_login_required_tool_result()` - 22 edges
7. `parse_portal_discente()` - 22 edges
8. `listar_disciplinas_ofertadas_flow()` - 21 edges
9. `clean_ws()` - 21 edges
10. `EstadoSessao` - 19 edges

## Surprising Connections (you probably didn't know these)
- `test_login_and_logout_post_with_csrf()` --uses--> `EstadoSessao`  [INFERRED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `fake_auth()` --calls--> `EstadoSessao`  [EXTRACTED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `fake_logout()` --calls--> `EstadoSessao`  [EXTRACTED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `create_mcp_server()` --calls--> `register_resources()`  [EXTRACTED]
  server.py → sigaa_mcp/resources.py
- `create_mcp_server()` --calls--> `register_tools()`  [EXTRACTED]
  server.py → sigaa_mcp/tools.py

## Import Cycles
- None detected.

## Communities (22 total, 9 thin omitted)

### Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos - "Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos"
Cohesion: 0.05
Nodes (46): invoke_portal_menu(), baixar_historico_escolar_flow(), consultar_notas_frequencia_flow(), emitir_atestado_matricula_flow(), _maybe_upload_to_drive(), obter_resumo_portal_flow(), _report(), _click_ava_menu_item() (+38 more)

### Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação - "Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação"
Cohesion: 0.08
Nodes (30): abrir_login_sigaa(), autenticar_credenciais_ui(), build_login_required_tool_result(), encerrar_sessao_ui(), selecionar_vinculo_ui(), logout_sigaa(), restart_sigaa_session(), AuthenticationRequiredError (+22 more)

### Comunidade 2 — Gerenciador de Sessão Playwright & Cofre RAM - "Comunidade 2 — Gerenciador de Sessão Playwright & Cofre RAM"
Cohesion: 0.07
Nodes (13): authenticate_with_credentials(), _bypass_intermediate_screens(), _click_vinculo_on_page(), ensure_authenticated_portal(), _extract_login_error(), _is_login_screen(), _is_portal_discente_ready(), _is_vinculo_screen() (+5 more)

### Comunidade 3 — Servidor FastMCP, Middlewares & Cache - "Comunidade 3 — Servidor FastMCP, Middlewares & Cache"
Cohesion: 0.06
Nodes (10): AppOnlyVisibilityMiddleware, _background_http_warmup(), create_mcp_server(), invalidate_response_cache(), server_lifespan(), register_prompts(), test_cache_invalidation_on_session_change(), test_mcp_surface_and_zero_password_exposure() (+2 more)

### Comunidade 4 — Catálogo Docker MCP UFPA - "Comunidade 4 — Catálogo Docker MCP UFPA"
Cohesion: 0.06
Nodes (30): description, displayName, category, license, owner, tags, name, registry (+22 more)

### Comunidade 5 — Portal Web Local de Login Visual (/login) - "Comunidade 5 — Portal Web Local de Login Visual (/login)"
Cohesion: 0.11
Nodes (13): EstadoSessao, _esc(), _parse_form_urlencoded(), register_web_routes(), login_route(), login_vinculo_route(), logout_route(), _render_login_html() (+5 more)

### Comunidade 6 — Infraestrutura Docker Compose & noVNC - "Comunidade 6 — Infraestrutura Docker Compose & noVNC"
Cohesion: 0.09
Nodes (21): context, dockerfile, interval, retries, start_period, test, timeout, networks (+13 more)

### Comunidade 8 — Logging Puro em Stderr - "Comunidade 8 — Logging Puro em Stderr"
Cohesion: 0.19
Nodes (3): configure_stderr_logging(), _env_bool(), _InterceptHandler

### Comunidade 9 — Fluxo de Troca e Simulação de Perfil - "Comunidade 9 — Fluxo de Troca e Simulação de Perfil"
Cohesion: 0.22
Nodes (4): _detect_image_extension(), _resolve_profile_image(), trocar_imagem_perfil_flow(), ResultadoTrocaPerfil

### Comunidade 11 — Resources MCP & Templates de Downloads - "Comunidade 11 — Resources MCP & Templates de Downloads"
Cohesion: 0.20
Nodes (4): get_drive_config(), is_drive_configured(), register_resources(), resource_status_init()

### Comunidade 12 — Manifesto de Deploy FastMCP - "Comunidade 12 — Manifesto de Deploy FastMCP"
Cohesion: 0.18
Nodes (10): deployment, host, log_level, port, transport, $schema, source, entrypoint (+2 more)

### Comunidade 13 — PainelAcadêmicoApp (FastMCPApp) - "Comunidade 13 — PainelAcadêmicoApp (FastMCPApp)"
Cohesion: 0.33
Nodes (4): abrir_painel_academico(), emitir_atestado_ui(), emitir_historico_ui(), filtrar_notas_ui()

### Comunidade 14 — ExploradorTurmasApp (FastMCPApp) - "Comunidade 14 — ExploradorTurmasApp (FastMCPApp)"
Cohesion: 0.33
Nodes (4): abrir_explorador_turmas(), buscar_ofertas_ui(), exportar_csv_ui(), _format_oferta_rows()

## Knowledge Gaps
- **2 isolated node(s):** `uv`, `sigaa-ufpa-mcp`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 226 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SigaaSessionManager` connect `Comunidade 2 — Gerenciador de Sessão Playwright & Cofre RAM` to `Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos`, `Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação`, `Comunidade 5 — Portal Web Local de Login Visual (/login)`, `Comunidade 9 — Fluxo de Troca e Simulação de Perfil`, `Comunidade 10 — Módulos de Recursos e Sessão`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `SigaaSessionManager` (e.g. with `authenticate_with_credentials()` and `ensure_authenticated_portal()`) actually correct?**
  _`SigaaSessionManager` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `uv`, `sigaa-ufpa-mcp` to the rest of the system?**
  _2 weakly-connected nodes found - possible missing edges._
- **Should `Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos` be split into smaller, more focused modules?**
  _Cohesion score 0.0514018691588785 - nodes in this community are weakly interconnected._
- **Why does `GoogleDriveService` connect `Comunidade 7 — Serviço OAuth 2.0 Google Drive` to `Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos`, `Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação`, `Comunidade 9 — Fluxo de Troca e Simulação de Perfil`, `Comunidade 10 — Módulos de Recursos e Sessão`, `Comunidade 11 — Resources MCP & Templates de Downloads`, `Comunidade 15 — PerfilDiscenteApp (FastMCPApp)`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Should `Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Why does `register_tools()` connect `Comunidade 1 — Tools FastMCP 4.1, Prefab UI & Autenticação` to `Comunidade 0 — Parsers, Horários UFPA & Schemas Acadêmicos`, `Comunidade 9 — Fluxo de Troca e Simulação de Perfil`, `Comunidade 3 — Servidor FastMCP, Middlewares & Cache`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._