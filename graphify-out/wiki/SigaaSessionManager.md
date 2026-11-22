# SigaaSessionManager

> God node · 56 connections · `sigaa_mcp/session.py`

**Community:** [Ciclo de Vida Ocioso do Navegador](Ciclo_de_Vida_Ocioso_do_Navegador.md)

## Connections by Relation

### calls
- test_activity_postpones_shutdown() `EXTRACTED`
- test_browser_closes_when_idle_and_reopens() `EXTRACTED`
- test_idle_disabled() `EXTRACTED`

### contains
- session.py `EXTRACTED`

### imports
- academico.py `EXTRACTED`
- turmas.py `EXTRACTED`
- auth.py `EXTRACTED`
- frequencia.py `EXTRACTED`
- perfil.py `EXTRACTED`
- test_idle_shutdown.py `EXTRACTED`

### method
- .ensure_browser_page() `EXTRACTED`
- .close() `EXTRACTED`
- .lock() `EXTRACTED`
- ._shutdown_idle_browser_unlocked() `EXTRACTED`
- .save_storage_state_if_enabled() `EXTRACTED`
- .get_estado_sessao() `EXTRACTED`
- ._close_browser_unlocked() `EXTRACTED`
- .browser_running() `EXTRACTED`
- ._cancel_idle_timer() `EXTRACTED`
- ._arm_idle_timer() `EXTRACTED`
- ._idle_watchdog() `EXTRACTED`
- .preferred_matricula() `EXTRACTED`
- .set_ram_credentials() `EXTRACTED`
- .get_password_for_form() `EXTRACTED`
- .print_current_page_to_pdf() `EXTRACTED`
- .__init__() `EXTRACTED`
- .username() `EXTRACTED`
- .clear_ram_credentials() `EXTRACTED`
- .remove_saved_storage_state() `EXTRACTED`
- .has_credentials() `EXTRACTED`
- *…and 2 more `method` connection(s) not listed (lowest-degree first to go)*

### rationale_for
- Thread/task-safe singleton managing Playwright Chromium and SIGAA session state. `EXTRACTED`

### uses
- [ensure_authenticated_portal()](ensure_authenticated_portal.md) `INFERRED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `INFERRED`
- [EstadoSessao](EstadoSessao.md) `INFERRED`
- exportar_horarios_csv_flow() `INFERRED`
- invoke_portal_menu() `INFERRED`
- comparar_disciplina_semestres_flow() `INFERRED`
- _resolve_vinculo_if_needed() `INFERRED`
- authenticate_with_credentials() `INFERRED`
- select_vinculo() `INFERRED`
- baixar_historico_escolar_flow() `INFERRED`
- emitir_atestado_matricula_flow() `INFERRED`
- consultar_frequencia_turmas_flow() `INFERRED`
- obter_resumo_portal_flow() `INFERRED`
- listar_atividades_pendentes_flow() `INFERRED`
- listar_avisos_turmas_flow() `INFERRED`
- logout_sigaa() `INFERRED`
- consultar_notas_frequencia_flow() `INFERRED`
- PerfilDiscenteResumo `INFERRED`
- trocar_imagem_perfil_flow() `INFERRED`
- _refresh_portal_snapshot_unlocked() `INFERRED`
- *…and 3 more `uses` connection(s) not listed (lowest-degree first to go)*

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*