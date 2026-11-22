# Fluxos Acadêmicos e Parsers

> 88 nodes

## Key Concepts

- **parsers.py** (50 connections) — `sigaa_mcp/parsers.py`
- **academico.py** (40 connections) — `sigaa_mcp/flows/academico.py`
- **turmas.py** (39 connections) — `sigaa_mcp/flows/turmas.py`
- **clean_ws()** (23 connections) — `sigaa_mcp/parsers.py`
- **parse_portal_discente()** (22 connections) — `sigaa_mcp/parsers.py`
- **listar_disciplinas_ofertadas_flow()** (20 connections) — `sigaa_mcp/flows/turmas.py`
- **normalize_text()** (20 connections) — `sigaa_mcp/parsers.py`
- **test_parsers.py** (19 connections) — `tests/test_parsers.py`
- **TurmaMatriculada** (17 connections) — `sigaa_mcp/schemas.py`
- **exportar_horarios_csv_flow()** (17 connections) — `sigaa_mcp/flows/turmas.py`
- **emitir_atestado_matricula_flow()** (14 connections) — `sigaa_mcp/flows/academico.py`
- **baixar_historico_escolar_flow()** (14 connections) — `sigaa_mcp/flows/academico.py`
- **parse_turmas_ofertadas_html()** (14 connections) — `sigaa_mcp/parsers.py`
- **parse_atestado_html()** (13 connections) — `sigaa_mcp/parsers.py`
- **obter_resumo_portal_flow()** (13 connections) — `sigaa_mcp/flows/academico.py`
- **listar_atividades_pendentes_flow()** (13 connections) — `sigaa_mcp/flows/turmas.py`
- **listar_avisos_turmas_flow()** (13 connections) — `sigaa_mcp/flows/turmas.py`
- **decode_ufpa_schedule()** (13 connections) — `sigaa_mcp/parsers.py`
- **AtividadePendente** (12 connections) — `sigaa_mcp/schemas.py`
- **AvisoTurma** (12 connections) — `sigaa_mcp/schemas.py`
- **consultar_notas_frequencia_flow()** (12 connections) — `sigaa_mcp/flows/academico.py`
- **PerfilDiscenteResumo** (11 connections) — `sigaa_mcp/schemas.py`
- **detect_schedule_conflicts()** (11 connections) — `sigaa_mcp/parsers.py`
- **parse_minhas_notas_html()** (11 connections) — `sigaa_mcp/parsers.py`
- **re** (11 connections)
- *... and 63 more nodes in this community*

## Relationships

- [Frequência e Comparativo entre Semestres](Frequência_e_Comparativo_entre_Semestres.md) (59 shared connections)
- [Apps MCP e UI de Autenticação](Apps_MCP_e_UI_de_Autenticação.md) (34 shared connections)
- [Login SIGAA e Portal Web](Login_SIGAA_e_Portal_Web.md) (32 shared connections)
- [Ciclo de Vida Ocioso do Navegador](Ciclo_de_Vida_Ocioso_do_Navegador.md) (12 shared connections)
- [Atualização de Foto de Perfil](Atualização_de_Foto_de_Perfil.md) (9 shared connections)
- [Erros de Sessão e Reinício](Erros_de_Sessão_e_Reinício.md) (6 shared connections)
- [Helpers de Configuração do Drive](Helpers_de_Configuração_do_Drive.md) (6 shared connections)
- [App Painel Acadêmico](App_Painel_Acadêmico.md) (5 shared connections)
- [App Explorador de Turmas](App_Explorador_de_Turmas.md) (3 shared connections)
- [Serviço Google Drive](Serviço_Google_Drive.md) (3 shared connections)
- [Configuração e Logging em Stderr](Configuração_e_Logging_em_Stderr.md) (2 shared connections)
- [Recursos MCP](Recursos_MCP.md) (1 shared connections)

## Source Files

- `sigaa_mcp/flows/academico.py`
- `sigaa_mcp/flows/turmas.py`
- `sigaa_mcp/parsers.py`
- `sigaa_mcp/schemas.py`
- `tests/test_parsers.py`

## Audit Trail

- EXTRACTED: 365 (92%)
- INFERRED: 32 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*