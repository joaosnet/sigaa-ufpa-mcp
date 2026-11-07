# Graph Report - sigaa-ufpa-mcp  (2026-11-07)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 182 nodes · 233 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e9b3c08`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- server.py
- sigaa-ufpa
- GoogleDriveService
- README.md
- trocar_imagem_perfil
- sigaa-mcp-server
- watch
- fastmcp.json
- Servidor MCP SIGAA UFPA
- sigaa-ufpa-mcp
- Servidor MCP SIGAA UFPA

## God Nodes (most connected - your core abstractions)
1. `sigaa-ufpa` - 17 edges
2. `GoogleDriveService` - 14 edges
3. `trocar_imagem_perfil()` - 10 edges
4. `full_login_procedure_discente()` - 9 edges
5. `sigaa-mcp-server` - 9 edges
6. `Herramientas MCP Disponibles` - 8 edges
7. `Ferramentas MCP Dispon?veis` - 8 edges
8. `baixar_historico_escolar()` - 7 edges
9. `exportar_horarios_csv()` - 7 edges
10. `listar_avisos_turmas()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Herramientas MCP Disponibles` --references--> `baixar_historico_escolar()`  [INFERRED]
  README.es.md → server.py
- `Ferramentas MCP Dispon?veis` --references--> `baixar_historico_escolar()`  [INFERRED]
  README.pt-BR.md → server.py
- `Herramientas MCP Disponibles` --references--> `exportar_horarios_csv()`  [INFERRED]
  README.es.md → server.py
- `Ferramentas MCP Dispon?veis` --references--> `exportar_horarios_csv()`  [INFERRED]
  README.pt-BR.md → server.py
- `Herramientas MCP Disponibles` --references--> `listar_avisos_turmas()`  [INFERRED]
  README.es.md → server.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **MCP Tools for SIGAA** — server_py_reiniciar_sessao, server_py_baixar_historico_escolar, server_py_listar_disciplinas_ofertadas, server_py_exportar_horarios_csv, server_py_listar_avisos_turmas [EXTRACTED 1.00]

## Communities (11 total, 1 thin omitted)

### Community 0 - "server.py"
Cohesion: 0.07
Nodes (8): get_drive_config(), is_drive_configured(), InterceptHandler, baixar_historico_escolar, exportar_horarios_csv, listar_avisos_turmas, listar_disciplinas_ofertadas, reiniciar_sessao

### Community 1 - "sigaa-ufpa"
Cohesion: 0.07
Nodes (29): description, displayName, category, license, owner, tags, name, registry (+21 more)

### Community 2 - "GoogleDriveService"
Cohesion: 0.10
Nodes (3): GoogleDriveService, get_drive_images(), get_status_login()

### Community 3 - "README.md"
Cohesion: 0.20
Nodes (8): Browser-Use, Dockerfile, .env.exemple, mcp.json, Model Context Protocol (MCP), pyproject.toml, SIGAA UFPA, uv.lock

### Community 4 - "trocar_imagem_perfil"
Cohesion: 0.21
Nodes (12): Herramientas MCP Disponibles, Recursos (`resource://`), Ferramentas MCP Dispon?veis, Recursos (`resource://`), baixar_historico_escolar(), exportar_horarios_csv(), full_login_procedure_discente(), lifespan_manager() (+4 more)

### Community 5 - "sigaa-mcp-server"
Cohesion: 0.12
Nodes (15): networks, sigaa-network, services, sigaa-mcp-server, driver, build, container_name, environment (+7 more)

### Community 6 - "watch"
Cohesion: 0.12
Nodes (10): watch, develop, action, ignore, path, target, esperar_elemento(), esperar_extracao_dados() (+2 more)

### Community 7 - "fastmcp.json"
Cohesion: 0.22
Nodes (8): deployment, log_level, transport, $schema, source, entrypoint, path, type

### Community 8 - "Servidor MCP SIGAA UFPA"
Cohesion: 0.18
Nodes (11): 1. Modo Servicio Web (Docker Compose), 2. Modo Entrada/Salida Est?ndar (Claude Desktop / CLI), Arquitectura del Sistema y Grafo de Conocimiento, Configuraci?n del Cliente MCP (HTTP), Desarrollo Local, Diagn?stico y Registros, Modos de Ejecuci?n, Puertos de Red (+3 more)

### Community 10 - "Servidor MCP SIGAA UFPA"
Cohesion: 0.18
Nodes (11): 1. Modo Servi?o Web (Docker Compose), 2. Modo Entrada/Sa?da Padr?o (Claude Desktop / CLI), Arquitetura do Sistema e Grafo de Conhecimento, Configura??o do Cliente MCP (HTTP), Desenvolvimento Local, Modos de Execu??o, Portas de Rede, Servidor MCP SIGAA UFPA (+3 more)

## Knowledge Gaps
- **13 isolated node(s):** `sigaa-ufpa-mcp`, `baixar_historico_escolar`, `exportar_horarios_csv`, `listar_avisos_turmas`, `listar_disciplinas_ofertadas` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 110 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GoogleDriveService` connect `GoogleDriveService` to `server.py`, `trocar_imagem_perfil`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `trocar_imagem_perfil()` (e.g. with `Herramientas MCP Disponibles` and `Ferramentas MCP Dispon?veis`) actually correct?**
  _`trocar_imagem_perfil()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sigaa-ufpa-mcp`, `baixar_historico_escolar`, `exportar_horarios_csv` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07459677419354839 - nodes in this community are weakly interconnected._
- **Why does `trocar_imagem_perfil()` connect `trocar_imagem_perfil` to `server.py`, `GoogleDriveService`, `watch`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Should `sigaa-ufpa` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Why does `Servidor MCP SIGAA UFPA` connect `Servidor MCP SIGAA UFPA` to `README.md`, `trocar_imagem_perfil`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._