# Parsers, Horários UFPA & Schemas Acadêmicos

> 108 nodes · cohesion 0.05

## Key Concepts

- **parsers.py** (42 connections) — `sigaa_mcp/parsers.py`
- **turmas.py** (40 connections) — `sigaa_mcp/flows/turmas.py`
- **academico.py** (39 connections) — `sigaa_mcp/flows/academico.py`
- **schemas.py** (29 connections) — `sigaa_mcp/schemas.py`
- **parse_portal_discente()** (22 connections) — `sigaa_mcp/parsers.py`
- **listar_disciplinas_ofertadas_flow()** (21 connections) — `sigaa_mcp/flows/turmas.py`
- **clean_ws()** (21 connections) — `sigaa_mcp/parsers.py`
- **exportar_horarios_csv_flow()** (19 connections) — `sigaa_mcp/flows/turmas.py`
- **test_parsers.py** (19 connections) — `tests/test_parsers.py`
- **baixar_historico_escolar_flow()** (17 connections) — `sigaa_mcp/flows/academico.py`
- **emitir_atestado_matricula_flow()** (17 connections) — `sigaa_mcp/flows/academico.py`
- **TurmaMatriculada** (17 connections) — `sigaa_mcp/schemas.py`
- **BaseModel** (16 connections)
- **consultar_notas_frequencia_flow()** (15 connections) — `sigaa_mcp/flows/academico.py`
- **obter_resumo_portal_flow()** (15 connections) — `sigaa_mcp/flows/academico.py`
- **invoke_portal_menu()** (14 connections) — `sigaa_mcp/auth.py`
- **listar_atividades_pendentes_flow()** (14 connections) — `sigaa_mcp/flows/turmas.py`
- **listar_avisos_turmas_flow()** (14 connections) — `sigaa_mcp/flows/turmas.py`
- **_report()** (13 connections) — `sigaa_mcp/flows/academico.py`
- **decode_ufpa_schedule()** (13 connections) — `sigaa_mcp/parsers.py`
- **normalize_text()** (13 connections) — `sigaa_mcp/parsers.py`
- **parse_atestado_html()** (13 connections) — `sigaa_mcp/parsers.py`
- **parse_turmas_ofertadas_html()** (12 connections) — `sigaa_mcp/parsers.py`
- **AtividadePendente** (12 connections) — `sigaa_mcp/schemas.py`
- **AvisoTurma** (12 connections) — `sigaa_mcp/schemas.py`
- *... and 83 more nodes in this community*

## Relationships

- [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md) (55 shared connections)
- [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md) (46 shared connections)
- [Fluxo de Troca e Simulação de Perfil](Fluxo_de_Troca_e_Simulação_de_Perfil.md) (12 shared connections)
- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (10 shared connections)
- [Portal Web Local de Login Visual (/login)](Portal_Web_Local_de_Login_Visual_-login.md) (5 shared connections)
- [PainelAcadêmicoApp (FastMCPApp)](PainelAcadêmicoApp_FastMCPApp.md) (5 shared connections)
- [Serviço OAuth 2.0 Google Drive](Serviço_OAuth_2.0_Google_Drive.md) (3 shared connections)
- [ExploradorTurmasApp (FastMCPApp)](ExploradorTurmasApp_FastMCPApp.md) (3 shared connections)
- [Resources MCP & Templates de Downloads](Resources_MCP_&_Templates_de_Downloads.md) (2 shared connections)
- [Logging Puro em Stderr](Logging_Puro_em_Stderr.md) (2 shared connections)
- [PerfilDiscenteApp (FastMCPApp)](PerfilDiscenteApp_FastMCPApp.md) (1 shared connections)

## Source Files

- `sigaa_mcp/auth.py`
- `sigaa_mcp/flows/academico.py`
- `sigaa_mcp/flows/turmas.py`
- `sigaa_mcp/parsers.py`
- `sigaa_mcp/schemas.py`
- `tests/test_parsers.py`

## Audit Trail

- EXTRACTED: 404 (92%)
- INFERRED: 37 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*