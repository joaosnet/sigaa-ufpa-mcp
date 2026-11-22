# ensure_authenticated_portal()

> God node · 32 connections · `sigaa_mcp/auth.py`

**Community:** [Login SIGAA e Portal Web](Login_SIGAA_e_Portal_Web.md)

## Connections by Relation

### calls
- [parse_portal_discente()](parse_portal_discente.md) `EXTRACTED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `EXTRACTED`
- exportar_horarios_csv_flow() `EXTRACTED`
- invoke_portal_menu() `EXTRACTED`
- comparar_disciplina_semestres_flow() `EXTRACTED`
- _resolve_vinculo_if_needed() `EXTRACTED`
- AuthenticationRequiredError `EXTRACTED`
- baixar_historico_escolar_flow() `EXTRACTED`
- emitir_atestado_matricula_flow() `EXTRACTED`
- consultar_frequencia_turmas_flow() `EXTRACTED`
- obter_resumo_portal_flow() `EXTRACTED`
- listar_atividades_pendentes_flow() `EXTRACTED`
- listar_avisos_turmas_flow() `EXTRACTED`
- consultar_notas_frequencia_flow() `EXTRACTED`
- _bypass_intermediate_screens() `EXTRACTED`
- _refresh_portal_snapshot_unlocked() `EXTRACTED`
- trocar_imagem_perfil_flow() `EXTRACTED`
- restart_sigaa_session() `EXTRACTED`
- _is_portal_discente_ready() `EXTRACTED`
- _background_http_warmup() `EXTRACTED`
- *…and 2 more `calls` connection(s) not listed (lowest-degree first to go)*

### contains
- auth.py `EXTRACTED`

### imports
- server.py `EXTRACTED`
- academico.py `EXTRACTED`
- turmas.py `EXTRACTED`
- frequencia.py `EXTRACTED`
- perfil.py `EXTRACTED`

### rationale_for
- Guarantee the Playwright page is authenticated and positioned on Portal do… `EXTRACTED`

### references
- Page `EXTRACTED`
- Any `EXTRACTED`

### uses
- [SigaaSessionManager](SigaaSessionManager.md) `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*