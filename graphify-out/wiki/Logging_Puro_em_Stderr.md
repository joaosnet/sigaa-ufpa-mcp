# Logging Puro em Stderr

> 14 nodes · cohesion 0.19

## Key Concepts

- **config.py** (22 connections) — `sigaa_mcp/config.py`
- **os** (6 connections)
- **configure_stderr_logging()** (6 connections) — `sigaa_mcp/config.py`
- **_InterceptHandler** (4 connections) — `sigaa_mcp/config.py`
- **logging** (3 connections)
- **_env_bool()** (2 connections) — `sigaa_mcp/config.py`
- **.emit()** (2 connections) — `sigaa_mcp/config.py`
- **dataclasses** (1 connections)
- **dotenv** (1 connections)
- **LogRecord** (1 connections)
- **Centralized typed configuration and runtime settings for SIGAA UFPA MCP.** (1 connections) — `sigaa_mcp/config.py`
- **Redirect standard library logging into Loguru on stderr (never stdout).** (1 connections) — `sigaa_mcp/config.py`
- **Ensure 100% of logs go exclusively to sys.stderr to keep stdio JSON-RPC pure.** (1 connections) — `sigaa_mcp/config.py`
- **sys** (1 connections)

## Relationships

- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (7 shared connections)
- [Servidor FastMCP, Middlewares & Cache](Servidor_FastMCP,_Middlewares_&_Cache.md) (4 shared connections)
- [Parsers, Horários UFPA & Schemas Acadêmicos](Parsers,_Horários_UFPA_&_Schemas_Acadêmicos.md) (2 shared connections)
- [Resources MCP & Templates de Downloads](Resources_MCP_&_Templates_de_Downloads.md) (1 shared connections)
- [Gerenciador de Sessão Playwright & Cofre RAM](Gerenciador_de_Sessão_Playwright_&_Cofre_RAM.md) (1 shared connections)
- [Fluxo de Troca e Simulação de Perfil](Fluxo_de_Troca_e_Simulação_de_Perfil.md) (1 shared connections)
- [Portal Web Local de Login Visual (/login)](Portal_Web_Local_de_Login_Visual_-login.md) (1 shared connections)
- [Configurações Tipadas de Runtime](Configurações_Tipadas_de_Runtime.md) (1 shared connections)

## Source Files

- `sigaa_mcp/config.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*