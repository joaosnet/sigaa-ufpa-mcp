# SigaaSessionManager

> God node · 43 connections · `sigaa_mcp/session.py`

**Community:** [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md)

## Connections by Relation

### contains
- session.py `EXTRACTED`

### imports
- turmas.py `EXTRACTED`
- academico.py `EXTRACTED`
- auth.py `EXTRACTED`
- perfil.py `EXTRACTED`

### method
- .ensure_browser_page() `EXTRACTED`
- .get_estado_sessao() `EXTRACTED`
- .save_storage_state_if_enabled() `EXTRACTED`
- .print_current_page_to_pdf() `EXTRACTED`
- ._close_browser_unlocked() `EXTRACTED`
- .preferred_matricula() `EXTRACTED`
- .set_ram_credentials() `EXTRACTED`
- .get_password_for_form() `EXTRACTED`
- .remove_saved_storage_state() `EXTRACTED`
- .close() `EXTRACTED`
- .__init__() `EXTRACTED`
- .lock() `EXTRACTED`
- .username() `EXTRACTED`
- .clear_ram_credentials() `EXTRACTED`
- .has_credentials() `EXTRACTED`
- .register_change_listener() `EXTRACTED`
- .notify_session_changed() `EXTRACTED`

### rationale_for
- Thread/task-safe singleton managing Playwright Chromium and SIGAA session state. `EXTRACTED`

### uses
- [ensure_authenticated_portal()](ensure_authenticated_portal.md) `INFERRED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `INFERRED`
- exportar_horarios_csv_flow() `INFERRED`
- [EstadoSessao](EstadoSessao.md) `INFERRED`
- baixar_historico_escolar_flow() `INFERRED`
- emitir_atestado_matricula_flow() `INFERRED`
- consultar_notas_frequencia_flow() `INFERRED`
- obter_resumo_portal_flow() `INFERRED`
- trocar_imagem_perfil_flow() `INFERRED`
- _resolve_vinculo_if_needed() `INFERRED`
- authenticate_with_credentials() `INFERRED`
- invoke_portal_menu() `INFERRED`
- select_vinculo() `INFERRED`
- listar_atividades_pendentes_flow() `INFERRED`
- listar_avisos_turmas_flow() `INFERRED`
- logout_sigaa() `INFERRED`
- PerfilDiscenteResumo `INFERRED`
- _refresh_portal_snapshot_unlocked() `INFERRED`
- restart_sigaa_session() `INFERRED`
- VinculoItem `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*