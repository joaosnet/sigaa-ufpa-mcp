# SIGAA UFPA MCP

<p align="center">
  <strong>Servidor MCP y Aplicaciones Interactivas para el Portal SIGAA de la UFPA</strong><br/>
  FastMCP 4.1 · Prefab UI · Playwright · Cero Consumo de Tokens Externos de IA
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.pt-BR.md">Português (Brasil)</a> ·
  <a href="README.es.md"><strong>Español</strong></a>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="Demostración de SIGAA UFPA MCP con Login Visual, FastMCP Apps y noVNC" width="100%" />
</p>

Conecta clientes MCP (**Google Antigravity**, **Claude Desktop**, **Cursor**, **VS Code**) directamente con [sigaa.ufpa.br](https://sigaa.ufpa.br) mediante automatización determinista con Playwright, paneles interactivos `prefab-ui` e Inicio de Sesión Visual aislado en memoria RAM.

---

## Instalación Rápida (Docker Compose)

No se requiere archivo `.env`. Desde la raíz del proyecto, ejecute:

```bash
docker compose up -d --build
```

- **Endpoint MCP HTTP:** `http://localhost:8003/mcp`
- **Portal de Login Visual:** `http://localhost:8003/login` *(o invoque `abrir_login_sigaa` desde el chat)*
- **Navegador en Vivo (noVNC):** `http://localhost:6080` *(contraseña por defecto: `sigaa`)*

### Configurar el Cliente MCP (`mcp_config.json`)

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

## Instalación Local (Sin Docker)

Requiere **Python 3.12+** y [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
uv run playwright install chromium

# Opción A: Servidor HTTP en http://localhost:8003/mcp
MCP_TRANSPORT=http uv run server.py

# Opción B: Servidor stdio para clientes de escritorio
uv run server.py
```

<details>
<summary><strong>Configuración local vía <code>stdio</code> (Claude Desktop / Cursor)</strong></summary>

```json
{
  "mcpServers": {
    "sigaa-ufpa": {
      "command": "uv",
      "args": ["--directory", "/ruta/absoluta/a/sigaa-ufpa-mcp", "run", "server.py"],
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

## Documentación Completa

La referencia técnica detallada, catálogo de herramientas, códigos de horario UFPA y variables opcionales están en [`docs/`](docs/README.md):

- [Guía Técnica Completa en Español](docs/es.md)
- [Architecture & Security (EN)](docs/architecture.md) · [Apps, Tools & Prompts (EN)](docs/tools-and-apps.md) · [Configuration & Drive (EN)](docs/configuration.md)

## Licencia

[MIT](pyproject.toml)
