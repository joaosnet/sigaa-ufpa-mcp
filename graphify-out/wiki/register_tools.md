# register_tools()

> God node · 38 connections · `sigaa_mcp/tools.py`

**Community:** [Apps MCP e UI de Autenticação](Apps_MCP_e_UI_de_Autenticação.md)

## Connections by Relation

### calls
- [build_dual_tool_result()](build_dual_tool_result.md) `EXTRACTED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `EXTRACTED`
- exportar_horarios_csv_flow() `EXTRACTED`
- comparar_disciplina_semestres_flow() `EXTRACTED`
- consultar_frequencia_turmas_flow() `EXTRACTED`
- listar_atividades_pendentes_flow() `EXTRACTED`
- listar_avisos_turmas_flow() `EXTRACTED`
- build_auth_prefab_app() `EXTRACTED`
- logout_sigaa() `EXTRACTED`
- anexar_frequencia_ao_boletim() `EXTRACTED`
- create_mcp_server() `EXTRACTED`
- serialize_summary_json() `EXTRACTED`
- restart_sigaa_session() `EXTRACTED`
- build_atestado_prefab_app() `EXTRACTED`
- build_notas_prefab_app() `EXTRACTED`
- build_atividades_prefab_app() `EXTRACTED`
- build_horarios_prefab_app() `EXTRACTED`
- build_avisos_prefab_app() `EXTRACTED`
- build_ofertadas_prefab_app() `EXTRACTED`
- build_perfil_result_prefab_app() `EXTRACTED`
- *…and 1 more `calls` connection(s) not listed (lowest-degree first to go)*

### contains
- tools.py `EXTRACTED`
- consultar_notas_frequencia() `EXTRACTED`
- listar_atividades_pendentes() `EXTRACTED`
- exportar_horarios_csv() `EXTRACTED`
- listar_avisos_turmas() `EXTRACTED`
- listar_disciplinas_ofertadas() `EXTRACTED`
- reiniciar_sessao() `EXTRACTED`
- encerrar_sessao() `EXTRACTED`
- consultar_frequencia_turmas() `EXTRACTED`
- comparar_disciplina_semestres() `EXTRACTED`
- trocar_imagem_perfil() `EXTRACTED`
- baixar_historico_escolar() `EXTRACTED`
- emitir_atestado_matricula() `EXTRACTED`

### imports
- server.py `EXTRACTED`

### rationale_for
- Register all 12 model-facing SIGAA UFPA tools on the FastMCP server. `EXTRACTED`

### references
- FastMCP `EXTRACTED`

### uses
- AuthenticationRequiredError `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*