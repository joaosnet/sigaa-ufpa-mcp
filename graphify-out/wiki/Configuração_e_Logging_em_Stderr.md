# Configuração e Logging em Stderr

> 17 nodes

## Key Concepts

- **config.py** (26 connections) — `sigaa_mcp/config.py`
- **os** (8 connections)
- **configure_stderr_logging()** (6 connections) — `sigaa_mcp/config.py`
- **_InterceptHandler** (4 connections) — `sigaa_mcp/config.py`
- **_resolve_download_dir()** (3 connections) — `sigaa_mcp/config.py`
- **logging** (3 connections)
- **_env_bool()** (2 connections) — `sigaa_mcp/config.py`
- **.emit()** (2 connections) — `sigaa_mcp/config.py`
- **_parse_timeout_ms()** (2 connections) — `sigaa_mcp/config.py`
- **LogRecord** (1 connections)
- **Path** (1 connections)
- **Centralized typed configuration and runtime settings for SIGAA UFPA MCP.** (1 connections) — `sigaa_mcp/config.py`
- **Redirect standard library logging into Loguru on stderr (never stdout).** (1 connections) — `sigaa_mcp/config.py`
- **Ensure 100% of logs go exclusively to sys.stderr to keep stdio JSON-RPC pure.** (1 connections) — `sigaa_mcp/config.py`
- **dataclasses** (1 connections)
- **dotenv** (1 connections)
- **sys** (1 connections)

## Relationships

- [Servidor e Middlewares](Servidor_e_Middlewares.md) (4 shared connections)
- [Helpers de Configuração do Drive](Helpers_de_Configuração_do_Drive.md) (4 shared connections)
- [Login SIGAA e Portal Web](Login_SIGAA_e_Portal_Web.md) (2 shared connections)
- [Recursos MCP](Recursos_MCP.md) (2 shared connections)
- [Fluxos Acadêmicos e Parsers](Fluxos_Acadêmicos_e_Parsers.md) (2 shared connections)
- [Erros de Sessão e Reinício](Erros_de_Sessão_e_Reinício.md) (2 shared connections)
- [Frequência e Comparativo entre Semestres](Frequência_e_Comparativo_entre_Semestres.md) (1 shared connections)
- [Atualização de Foto de Perfil](Atualização_de_Foto_de_Perfil.md) (1 shared connections)
- [Ciclo de Vida Ocioso do Navegador](Ciclo_de_Vida_Ocioso_do_Navegador.md) (1 shared connections)
- [Configurações de Runtime](Configurações_de_Runtime.md) (1 shared connections)

## Source Files

- `sigaa_mcp/config.py`

## Audit Trail

- EXTRACTED: 42 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*