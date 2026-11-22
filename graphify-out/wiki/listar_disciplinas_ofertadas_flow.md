# listar_disciplinas_ofertadas_flow()

> God node · 20 connections · `sigaa_mcp/flows/turmas.py`

**Community:** [Fluxos Acadêmicos e Parsers](Fluxos_Acadêmicos_e_Parsers.md)

## Connections by Relation

### calls
- [register_tools()](register_tools.md) `EXTRACTED`
- [ensure_authenticated_portal()](ensure_authenticated_portal.md) `EXTRACTED`
- [parse_portal_discente()](parse_portal_discente.md) `EXTRACTED`
- [normalize_text()](normalize_text.md) `EXTRACTED`
- invoke_portal_menu() `EXTRACTED`
- parse_turmas_ofertadas_html() `EXTRACTED`
- re `EXTRACTED`
- abrir_explorador_turmas() `EXTRACTED`
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