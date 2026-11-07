# listar_disciplinas_ofertadas_flow()

> God node · 21 connections · `sigaa_mcp/flows/turmas.py`

**Community:** [Parsers, Horários UFPA & Schemas Acadêmicos](Parsers,_Horários_UFPA_&_Schemas_Acadêmicos.md)

## Connections by Relation

### calls
- [register_tools()](register_tools.md) `EXTRACTED`
- [ensure_authenticated_portal()](ensure_authenticated_portal.md) `EXTRACTED`
- [parse_portal_discente()](parse_portal_discente.md) `EXTRACTED`
- invoke_portal_menu() `EXTRACTED`
- normalize_text() `EXTRACTED`
- _report() `EXTRACTED`
- parse_turmas_ofertadas_html() `EXTRACTED`
- abrir_explorador_turmas() `EXTRACTED`
- re `EXTRACTED`
- buscar_ofertas_ui() `EXTRACTED`
- _match_select_option() `EXTRACTED`
- listar_disciplinas_ofertadas() `EXTRACTED`

### contains
- turmas.py `EXTRACTED`

### imports
- tools.py `EXTRACTED`
- turmas_app.py `EXTRACTED`

### rationale_for
- Search offered classes in SIGAA UFPA and automatically detect schedule… `EXTRACTED`

### references
- Any `EXTRACTED`

### uses
- [SigaaSessionManager](SigaaSessionManager.md) `INFERRED`
- TurmaMatriculada `INFERRED`
- AuthenticationRequiredError `INFERRED`
- DisciplinaOfertada `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*