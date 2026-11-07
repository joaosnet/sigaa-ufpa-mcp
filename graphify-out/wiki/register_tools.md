# register_tools()

> God node · 37 connections · `sigaa_mcp/tools.py`

**Community:** [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md)

## Connections by Relation

### calls
- [build_dual_tool_result()](build_dual_tool_result.md) `EXTRACTED`
- [build_login_required_tool_result()](build_login_required_tool_result.md) `EXTRACTED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `EXTRACTED`
- exportar_horarios_csv_flow() `EXTRACTED`
- baixar_historico_escolar_flow() `EXTRACTED`
- emitir_atestado_matricula_flow() `EXTRACTED`
- consultar_notas_frequencia_flow() `EXTRACTED`
- trocar_imagem_perfil_flow() `EXTRACTED`
- listar_atividades_pendentes_flow() `EXTRACTED`
- listar_avisos_turmas_flow() `EXTRACTED`
- build_auth_prefab_app() `EXTRACTED`
- logout_sigaa() `EXTRACTED`
- create_mcp_server() `EXTRACTED`
- restart_sigaa_session() `EXTRACTED`
- build_notas_prefab_app() `EXTRACTED`
- build_atividades_prefab_app() `EXTRACTED`
- build_horarios_prefab_app() `EXTRACTED`
- build_avisos_prefab_app() `EXTRACTED`
- build_ofertadas_prefab_app() `EXTRACTED`
- build_perfil_result_prefab_app() `EXTRACTED`
- *…and 2 more `calls` connection(s) not listed (lowest-degree first to go)*

### contains
- tools.py `EXTRACTED`
- reiniciar_sessao() `EXTRACTED`
- encerrar_sessao() `EXTRACTED`
- consultar_notas_frequencia() `EXTRACTED`
- listar_atividades_pendentes() `EXTRACTED`
- exportar_horarios_csv() `EXTRACTED`
- listar_avisos_turmas() `EXTRACTED`
- trocar_imagem_perfil() `EXTRACTED`
- baixar_historico_escolar() `EXTRACTED`
- emitir_atestado_matricula() `EXTRACTED`
- listar_disciplinas_ofertadas() `EXTRACTED`

### imports
- server.py `EXTRACTED`

### rationale_for
- Register all 10 model-facing SIGAA UFPA tools on the FastMCP server. `EXTRACTED`

### references
- FastMCP `EXTRACTED`

### uses
- AuthenticationRequiredError `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*