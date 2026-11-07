# build_login_required_tool_result()

> God node · 22 connections · `sigaa_mcp/apps/auth_app.py`

**Community:** [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md)

## Connections by Relation

### calls
- [register_tools()](register_tools.md) `EXTRACTED`
- [build_dual_tool_result()](build_dual_tool_result.md) `EXTRACTED`
- build_auth_prefab_app() `EXTRACTED`
- abrir_painel_academico() `EXTRACTED`
- abrir_estudio_perfil() `EXTRACTED`
- baixar_historico_escolar() `EXTRACTED`
- consultar_notas_frequencia() `EXTRACTED`
- emitir_atestado_matricula() `EXTRACTED`
- exportar_horarios_csv() `EXTRACTED`
- listar_atividades_pendentes() `EXTRACTED`
- listar_avisos_turmas() `EXTRACTED`
- trocar_imagem_perfil() `EXTRACTED`

### contains
- auth_app.py `EXTRACTED`

### imports
- tools.py `EXTRACTED`
- painel_app.py `EXTRACTED`
- perfil_app.py `EXTRACTED`
- apps/__init__.py `EXTRACTED`

### indirect_call
- autenticar_credenciais_ui() `INFERRED`
- selecionar_vinculo_ui() `INFERRED`
- encerrar_sessao_ui() `INFERRED`

### rationale_for
- Build a dual ToolResult rendering the visual login card + fallback URL when… `EXTRACTED`

### references
- ToolResult `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*