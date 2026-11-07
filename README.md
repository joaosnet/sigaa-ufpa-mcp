# SIGAA UFPA MCP

<p align="center">
  <strong>MCP Server & Interactive Apps for UFPA's SIGAA Academic Portal</strong><br/>
  FastMCP 4.1 · Prefab UI · Playwright · Zero External AI Token Cost
</p>

<p align="center">
  <a href="README.md"><strong>English</strong></a> ·
  <a href="README.pt-BR.md">Português (Brasil)</a> ·
  <a href="README.es.md">Español</a>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="SIGAA UFPA MCP live demo with Visual Login, FastMCP Apps, and noVNC" width="100%" />
</p>

Connects MCP clients (**Google Antigravity**, **Claude Desktop**, **Cursor**, **VS Code**) directly to [sigaa.ufpa.br](https://sigaa.ufpa.br) using deterministic Playwright automation, interactive `prefab-ui` dashboards, and RAM-isolated Visual Login.

---

## Quick Start (Docker Compose)

No `.env` file is required. Run from the repository root:

```bash
docker compose up -d --build
```

- **MCP HTTP Endpoint:** `http://localhost:8003/mcp`
- **Visual Login Portal:** `http://localhost:8003/login` *(or run `abrir_login_sigaa` inside your chat)*
- **Live Browser (noVNC):** `http://localhost:6080` *(default password: `sigaa`)*

### Connect Your MCP Client (`mcp_config.json`)

```json
{
  "mcpServers": {
    "sigaa-ufpa": {
      "url": "http://localhost:8003/mcp"
    }
  }
}
```

---

## Local Installation (Without Docker)

Requires **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
uv run playwright install chromium

# Option A: HTTP server on http://localhost:8003/mcp
MCP_TRANSPORT=http uv run server.py

# Option B: stdio server for desktop clients
uv run server.py
```

<details>
<summary><strong>Local <code>stdio</code> Client Snippet (Claude Desktop / Cursor)</strong></summary>

```json
{
  "mcpServers": {
    "sigaa-ufpa": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/sigaa-ufpa-mcp", "run", "server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "CHROME_HEADLESS": "true"
      }
    }
  }
}
```
</details>

---

## Documentation

Full technical reference is available in [`docs/`](docs/README.md):

- [Architecture, Visual Login Security & Testing](docs/architecture.md)
- [FastMCP Apps, Tools, Prompts, Resources & UFPA Schedule Codes](docs/tools-and-apps.md)
- [Environment Variables, Session Persistence & Google Drive](docs/configuration.md)

## License

[MIT](pyproject.toml)
