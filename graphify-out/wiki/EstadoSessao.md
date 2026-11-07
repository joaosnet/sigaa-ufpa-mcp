# EstadoSessao

> God node · 19 connections · `sigaa_mcp/schemas.py`

**Community:** [Portal Web Local de Login Visual (/login)](Portal_Web_Local_de_Login_Visual_-login.md)

## Connections by Relation

### calls
- fake_auth() `EXTRACTED`
- fake_logout() `EXTRACTED`

### contains
- schemas.py `EXTRACTED`

### imports
- ui_components.py `EXTRACTED`
- auth.py `EXTRACTED`
- session.py `EXTRACTED`
- web_login.py `EXTRACTED`
- test_web_login.py `EXTRACTED`

### inherits
- BaseModel `EXTRACTED`

### rationale_for
- Estado atual da sessão autenticada no SIGAA UFPA. `EXTRACTED`

### references
- .get_estado_sessao() `EXTRACTED`

### uses
- [SigaaSessionManager](SigaaSessionManager.md) `INFERRED`
- authenticate_with_credentials() `INFERRED`
- select_vinculo() `INFERRED`
- build_auth_prefab_app() `INFERRED`
- logout_sigaa() `INFERRED`
- restart_sigaa_session() `INFERRED`
- test_login_and_logout_post_with_csrf() `INFERRED`
- _render_login_html() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*