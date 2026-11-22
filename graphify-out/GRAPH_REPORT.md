# Graph Report - sigaa-ufpa-mcp  (2026-11-22)

## Corpus Check
- Corpus is ~26,726 words - fits in a single context window. You may not need a graph.

## Summary
- 560 nodes · 1375 edges · 28 communities (15 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 103 edges (avg confidence: 0.91)
- Token cost: 14,461 input · 2,034 output

## Community Hubs (Navigation)
- Fluxos Acadêmicos e Parsers
- Erros de Sessão e Reinício
- Configurações de Runtime
- Frequência e Comparativo entre Semestres
- Login SIGAA e Portal Web
- Ciclo de Vida Ocioso do Navegador
- Servidor e Middlewares
- Configuração e Logging em Stderr
- Serviço Google Drive
- Apps MCP e UI de Autenticação
- Atualização de Foto de Perfil
- App Painel Acadêmico
- App Explorador de Turmas
- Helpers de Configuração do Drive
- Recursos MCP
- Configuração de Deploy FastMCP
- Configuração do Cliente MCP Local
- Metadados do Projeto
- Catálogo Docker MCP
- Serviço Docker Compose
- Documentação e Visão Geral
- Documentação Técnica em Espanhol
- Documentação Técnica em Português

## God Nodes (most connected - your core abstractions)
1. `SigaaSessionManager` - 56 edges
2. `register_tools()` - 38 edges
3. `ensure_authenticated_portal()` - 32 edges
4. `build_dual_tool_result()` - 27 edges
5. `clean_ws()` - 23 edges
6. `parse_portal_discente()` - 22 edges
7. `GoogleDriveService` - 20 edges
8. `listar_disciplinas_ofertadas_flow()` - 20 edges
9. `normalize_text()` - 20 edges
10. `EstadoSessao` - 19 edges

## Surprising Connections (you probably didn't know these)
- `fake_auth()` --calls--> `EstadoSessao`  [EXTRACTED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `fake_logout()` --calls--> `EstadoSessao`  [EXTRACTED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `test_login_and_logout_post_with_csrf()` --uses--> `EstadoSessao`  [INFERRED]
  tests/test_web_login.py → sigaa_mcp/schemas.py
- `create_mcp_server()` --calls--> `register_tools()`  [EXTRACTED]
  server.py → sigaa_mcp/tools.py
- `create_mcp_server()` --calls--> `register_resources()`  [EXTRACTED]
  server.py → sigaa_mcp/resources.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SIGAA UFPA MCP Interactive Apps** — sigaa_mcp_apps_autenticacaosigaaapp, sigaa_mcp_apps_painelacademicoapp, sigaa_mcp_apps_exploradorturmasapp, sigaa_mcp_apps_perfildiscenteapp [EXTRACTED 1.00]

## Communities (28 total, 13 thin omitted)

### Community 0 - "Fluxos Acadêmicos e Parsers"
Cohesion: 0.06
Nodes (38): AtestadoResumo, AtividadePendente, AvisoTurma, HistoricoResumo, PerfilDiscenteResumo, TurmaMatriculada, emitir_atestado_matricula_flow(), parse_atestado_html() (+30 more)

### Community 2 - "Frequência e Comparativo entre Semestres"
Cohesion: 0.07
Nodes (29): CargaHorariaItem, ChoqueHorario, ComparativoDisciplina, DisciplinaOfertada, FrequenciaTurma, HorariosExportadosResumo, IndiceAcademico, NotaDisciplina (+21 more)

### Community 3 - "Login SIGAA e Portal Web"
Cohesion: 0.08
Nodes (26): EstadoSessao, authenticate_with_credentials(), select_vinculo(), login_route(), login_vinculo_route(), ensure_authenticated_portal(), _bypass_intermediate_screens(), _click_vinculo_on_page() (+18 more)

### Community 4 - "Ciclo de Vida Ocioso do Navegador"
Cohesion: 0.06
Nodes (6): _ActivityLock, SigaaSessionManager, short_idle(), test_activity_postpones_shutdown(), test_browser_closes_when_idle_and_reopens(), test_idle_disabled()

### Community 5 - "Servidor e Middlewares"
Cohesion: 0.06
Nodes (10): AppOnlyVisibilityMiddleware, create_mcp_server(), _background_http_warmup(), invalidate_response_cache(), server_lifespan(), register_prompts(), test_cache_invalidation_on_session_change(), test_mcp_surface_and_zero_password_exposure() (+2 more)

### Community 8 - "Configuração e Logging em Stderr"
Cohesion: 0.16
Nodes (5): _InterceptHandler, _resolve_download_dir(), configure_stderr_logging(), _env_bool(), _parse_timeout_ms()

### Community 1 - "Apps MCP e UI de Autenticação"
Cohesion: 0.07
Nodes (32): logout_sigaa(), build_atestado_prefab_app(), build_atividades_prefab_app(), build_auth_prefab_app(), build_avisos_prefab_app(), build_historico_prefab_app(), build_horarios_prefab_app(), build_notas_prefab_app() (+24 more)

### Community 10 - "Atualização de Foto de Perfil"
Cohesion: 0.24
Nodes (3): trocar_imagem_perfil_flow(), _detect_image_extension(), _resolve_profile_image()

### Community 16 - "App Painel Acadêmico"
Cohesion: 0.33
Nodes (4): abrir_painel_academico(), emitir_atestado_ui(), emitir_historico_ui(), filtrar_notas_ui()

### Community 17 - "App Explorador de Turmas"
Cohesion: 0.33
Nodes (4): abrir_explorador_turmas(), buscar_ofertas_ui(), exportar_csv_ui(), _format_oferta_rows()

### Community 12 - "Helpers de Configuração do Drive"
Cohesion: 0.24
Nodes (3): get_drive_config(), is_drive_configured(), resource_status_init()

### Community 13 - "Configuração de Deploy FastMCP"
Cohesion: 0.18
Nodes (10): deployment, host, log_level, port, transport, $schema, source, entrypoint (+2 more)

### Community 6 - "Catálogo Docker MCP"
Cohesion: 0.06
Nodes (30): description, displayName, category, license, owner, tags, name, registry (+22 more)

### Community 7 - "Serviço Docker Compose"
Cohesion: 0.09
Nodes (21): context, dockerfile, interval, retries, start_period, test, timeout, networks (+13 more)

### Community 14 - "Documentação e Visão Geral"
Cohesion: 0.29
Nodes (4): Architecture, Security & Testing, Configuration & Optional Integrations, FastMCP Apps, Tools, Prompts & Resources, SIGAA UFPA MCP Demo

## Knowledge Gaps
- **6 isolated node(s):** `uv`, `sigaa-ufpa-mcp`, `Configuration & Optional Integrations`, `SIGAA UFPA MCP Demo`, `Documentación Técnica — SIGAA UFPA MCP` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 253 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SigaaSessionManager` connect `Ciclo de Vida Ocioso do Navegador` to `Fluxos Acadêmicos e Parsers`, `Apps MCP e UI de Autenticação`, `Frequência e Comparativo entre Semestres`, `Login SIGAA e Portal Web`, `Atualização de Foto de Perfil`, `Erros de Sessão e Reinício`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `SigaaSessionManager` (e.g. with `authenticate_with_credentials()` and `ensure_authenticated_portal()`) actually correct?**
  _`SigaaSessionManager` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `uv`, `sigaa-ufpa-mcp`, `Configuration & Optional Integrations` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Fluxos Acadêmicos e Parsers` be split into smaller, more focused modules?**
  _Cohesion score 0.05877742946708464 - nodes in this community are weakly interconnected._
- **Why does `GoogleDriveService` connect `Serviço Google Drive` to `Fluxos Acadêmicos e Parsers`, `Atualização de Foto de Perfil`, `Helpers de Configuração do Drive`, `Recursos MCP`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `Frequência e Comparativo entre Semestres` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Why does `register_tools()` connect `Apps MCP e UI de Autenticação` to `Fluxos Acadêmicos e Parsers`, `Frequência e Comparativo entre Semestres`, `Erros de Sessão e Reinício`, `Servidor e Middlewares`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._