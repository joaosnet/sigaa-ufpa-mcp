# Ciclo de Vida Ocioso do Navegador

> 50 nodes

## Key Concepts

- **SigaaSessionManager** (56 connections) — `sigaa_mcp/session.py`
- **_ActivityLock** (10 connections) — `sigaa_mcp/session.py`
- **test_idle_shutdown.py** (10 connections) — `tests/test_idle_shutdown.py`
- **.ensure_browser_page()** (7 connections) — `sigaa_mcp/session.py`
- **.close()** (6 connections) — `sigaa_mcp/session.py`
- **test_activity_postpones_shutdown()** (6 connections) — `tests/test_idle_shutdown.py`
- **test_browser_closes_when_idle_and_reopens()** (6 connections) — `tests/test_idle_shutdown.py`
- **test_idle_disabled()** (6 connections) — `tests/test_idle_shutdown.py`
- **.lock()** (5 connections) — `sigaa_mcp/session.py`
- **.browser_running()** (4 connections) — `sigaa_mcp/session.py`
- **.get_estado_sessao()** (4 connections) — `sigaa_mcp/session.py`
- **._arm_idle_timer()** (4 connections) — `sigaa_mcp/session.py`
- **._cancel_idle_timer()** (4 connections) — `sigaa_mcp/session.py`
- **._close_browser_unlocked()** (4 connections) — `sigaa_mcp/session.py`
- **.save_storage_state_if_enabled()** (4 connections) — `sigaa_mcp/session.py`
- **._shutdown_idle_browser_unlocked()** (4 connections) — `sigaa_mcp/session.py`
- **.preferred_matricula()** (3 connections) — `sigaa_mcp/session.py`
- **.print_current_page_to_pdf()** (3 connections) — `sigaa_mcp/session.py`
- **.acquire()** (3 connections) — `sigaa_mcp/session.py`
- **.release()** (3 connections) — `sigaa_mcp/session.py`
- **.get_password_for_form()** (3 connections) — `sigaa_mcp/session.py`
- **._idle_watchdog()** (3 connections) — `sigaa_mcp/session.py`
- **.__init__()** (3 connections) — `sigaa_mcp/session.py`
- **.set_ram_credentials()** (3 connections) — `sigaa_mcp/session.py`
- **pytest** (3 connections)
- *... and 25 more nodes in this community*

## Relationships

- [Login SIGAA e Portal Web](Login_SIGAA_e_Portal_Web.md) (15 shared connections)
- [Fluxos Acadêmicos e Parsers](Fluxos_Acadêmicos_e_Parsers.md) (12 shared connections)
- [Frequência e Comparativo entre Semestres](Frequência_e_Comparativo_entre_Semestres.md) (5 shared connections)
- [Erros de Sessão e Reinício](Erros_de_Sessão_e_Reinício.md) (4 shared connections)
- [Atualização de Foto de Perfil](Atualização_de_Foto_de_Perfil.md) (2 shared connections)
- [Servidor e Middlewares](Servidor_e_Middlewares.md) (2 shared connections)
- [Apps MCP e UI de Autenticação](Apps_MCP_e_UI_de_Autenticação.md) (1 shared connections)
- [Configuração e Logging em Stderr](Configuração_e_Logging_em_Stderr.md) (1 shared connections)

## Source Files

- `sigaa_mcp/session.py`
- `tests/test_idle_shutdown.py`

## Audit Trail

- EXTRACTED: 78 (65%)
- INFERRED: 42 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*