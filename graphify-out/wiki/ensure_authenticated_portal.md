# ensure_authenticated_portal()

> God node · 29 connections · `sigaa_mcp/auth.py`

**Community:** [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md)

## Connections by Relation

### calls
- [parse_portal_discente()](parse_portal_discente.md) `EXTRACTED`
- [listar_disciplinas_ofertadas_flow()](listar_disciplinas_ofertadas_flow.md) `EXTRACTED`
- exportar_horarios_csv_flow() `EXTRACTED`
- baixar_historico_escolar_flow() `EXTRACTED`
- emitir_atestado_matricula_flow() `EXTRACTED`
- _resolve_vinculo_if_needed() `EXTRACTED`
- consultar_notas_frequencia_flow() `EXTRACTED`
- obter_resumo_portal_flow() `EXTRACTED`
- trocar_imagem_perfil_flow() `EXTRACTED`
- AuthenticationRequiredError `EXTRACTED`
- invoke_portal_menu() `EXTRACTED`
- listar_atividades_pendentes_flow() `EXTRACTED`
- listar_avisos_turmas_flow() `EXTRACTED`
- _bypass_intermediate_screens() `EXTRACTED`
- _refresh_portal_snapshot_unlocked() `EXTRACTED`
- restart_sigaa_session() `EXTRACTED`
- _is_portal_discente_ready() `EXTRACTED`
- _background_http_warmup() `EXTRACTED`
- _is_login_screen() `EXTRACTED`
- _extract_login_error() `EXTRACTED`

### contains
- auth.py `EXTRACTED`

### imports
- server.py `EXTRACTED`
- turmas.py `EXTRACTED`
- academico.py `EXTRACTED`
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