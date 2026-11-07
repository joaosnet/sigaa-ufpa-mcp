# Graph Report - sigaa-ufpa-mcp  (2026-11-07)

## Corpus Check
- Corpus is ~4,303 words - fits in a single context window. You may not need a graph.

## Summary
- 154 nodes · 192 edges · 10 communities (9 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.89)
- Token cost: 3,366 input · 2,732 output

## Community Hubs (Navigation)
- Google Drive Auth Config
- Docker Catalog Metadata
- Google Drive Integration
- Dockerized Browser Automation Setup
- Student Portal Services
- Docker Compose Configuration
- SIGAA Web Automation
- FastMCP Deployment Configuration
- Resource Metadata
- UFPA Academic Management System

## God Nodes (most connected - your core abstractions)
1. `sigaa-ufpa` - 17 edges
2. `GoogleDriveService` - 14 edges
3. `sigaa-mcp-server` - 9 edges
4. `full_login_procedure_discente()` - 9 edges
5. `trocar_imagem_perfil()` - 8 edges
6. `metadata` - 5 edges
7. `watch` - 5 edges
8. `esperar_elemento()` - 5 edges
9. `perform_login_discente()` - 5 edges
10. `reiniciar_sessao()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `trocar_imagem_perfil()` --calls--> `GoogleDriveService`  [EXTRACTED]
  server.py → drive_service.py
- `login_sigaa()` --references--> `action`  [EXTRACTED]
  server.py → docker-compose.yml
- `get_drive_images()` --calls--> `GoogleDriveService`  [EXTRACTED]
  server.py → drive_service.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **MCP Tools for SIGAA** — server_py_reiniciar_sessao, server_py_baixar_historico_escolar, server_py_listar_disciplinas_ofertadas, server_py_exportar_horarios_csv, server_py_listar_avisos_turmas [EXTRACTED 1.00]

## Communities (10 total, 1 thin omitted)

### Community 0 - "Google Drive Auth Config"
Cohesion: 0.07
Nodes (8): get_drive_config(), is_drive_configured(), InterceptHandler, baixar_historico_escolar, exportar_horarios_csv, listar_avisos_turmas, listar_disciplinas_ofertadas, reiniciar_sessao

### Community 1 - "Docker Catalog Metadata"
Cohesion: 0.08
Nodes (24): description, displayName, name, registry, sigaa-ufpa, env, example, name (+16 more)

### Community 2 - "Google Drive Integration"
Cohesion: 0.10
Nodes (3): GoogleDriveService, get_drive_images(), get_status_login()

### Community 3 - "Dockerized Browser Automation Setup"
Cohesion: 0.12
Nodes (15): Browser-Use, networks, sigaa-network, services, driver, driver, volumes, sigaa-data (+7 more)

### Community 4 - "Student Portal Services"
Cohesion: 0.21
Nodes (8): baixar_historico_escolar(), exportar_horarios_csv(), full_login_procedure_discente(), lifespan_manager(), listar_avisos_turmas(), listar_disciplinas_ofertadas(), reiniciar_sessao(), trocar_imagem_perfil()

### Community 5 - "Docker Compose Configuration"
Cohesion: 0.15
Nodes (13): watch, sigaa-mcp-server, build, container_name, develop, environment, networks, ports (+5 more)

### Community 6 - "SIGAA Web Automation"
Cohesion: 0.18
Nodes (5): action, esperar_elemento(), esperar_extracao_dados(), login_sigaa(), perform_login_discente()

### Community 7 - "FastMCP Deployment Configuration"
Cohesion: 0.22
Nodes (8): deployment, log_level, transport, $schema, source, entrypoint, path, type

### Community 8 - "Resource Metadata"
Cohesion: 0.40
Nodes (5): category, license, owner, tags, metadata

## Knowledge Gaps
- **13 isolated node(s):** `sigaa-ufpa-mcp`, `Dockerfile`, `pyproject.toml`, `uv.lock`, `.env.exemple` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 94 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GoogleDriveService` connect `Google Drive Integration` to `Google Drive Auth Config`, `Student Portal Services`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **What connects `sigaa-ufpa-mcp`, `Dockerfile`, `pyproject.toml` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Google Drive Auth Config` be split into smaller, more focused modules?**
  _Cohesion score 0.07459677419354839 - nodes in this community are weakly interconnected._
- **Why does `trocar_imagem_perfil()` connect `Student Portal Services` to `Google Drive Auth Config`, `Google Drive Integration`, `SIGAA Web Automation`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Should `Docker Catalog Metadata` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Why does `services` connect `Dockerized Browser Automation Setup` to `Docker Compose Configuration`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Should `Google Drive Integration` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._