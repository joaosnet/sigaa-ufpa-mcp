# Configura??o de Implanta??o FastMCP

> **Comunidade 7** ? 9 n?s ? Coes?o: 0.22 ? Fonte prim?ria: `fastmcp.json`, `server.py`

## Vis?o Geral
Define as especifica??es de transporte e ciclo de vida do servidor FastMCP.

---

## ?? Modos de Transporte

### 1. Modo `stdio` (Padr?o para Clientes Locais)
* Utilizado pelo Claude Desktop, Cursor e ambientes onde o cliente MCP gerencia o ciclo de vida do processo filho atrav?s de `stdin`/`stdout`.
* O login ? realizado sob demanda na primeira chamada de ferramenta.

### 2. Modo `http` (Streamable HTTP / SSE)
* Escuta na porta `8003`.
* Executa o `lifespan_manager` que inicializa o navegador e realiza o procedimento de login no startup (`full_login_procedure_discente()`).
* Mant?m o navegador aberto permanentemente com `keep_alive=True`.

---

## ?? Recursos Expostos (`resource://`)
* `resource://status-init`: Retorna se o login de inicializa??o foi bem-sucedido e a mensagem de status da sess?o.
* `resource://drive-images`: Retorna a lista de imagens dispon?veis na pasta do Google Drive configurada.
