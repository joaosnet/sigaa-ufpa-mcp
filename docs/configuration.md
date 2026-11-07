# Configuration & Optional Integrations

[← Back to README](../README.md) · [Português](pt-BR.md) · [Español](es.md)

## Optional Environment Variables (`.env`)

No `.env` file is required when signing in through `abrir_login_sigaa` or `http://localhost:8003/login`. Copy `.env.example` to `.env` only if you want unattended auto-login or Google Drive integration:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SIGAA_USERNAME` | *(empty)* | Optional SIGAA login (leave empty to use Visual Login) |
| `SIGAA_PASSWORD` | *(empty)* | Optional SIGAA password (leave empty to use Visual Login) |
| `SIGAA_MATRICULA` | *(empty)* | Preferred registration number when the account has multiple vínculos |
| `MCP_TRANSPORT` | `stdio` | `stdio` (desktop clients) or `http` (Docker / URL clients) |
| `MCP_SERVER_HOST` | `0.0.0.0` | Bind address in HTTP mode |
| `MCP_SERVER_PORT` | `8003` | HTTP port for `/mcp`, `/login`, and `/health` |
| `CHROME_HEADLESS` | `true` (`false` in Docker) | Headless locally or visible inside Docker's Xvfb/noVNC |
| `BROWSER_TIMEOUT_MS` | `45000` | Playwright navigation timeout in milliseconds |
| `VNC_PASSWORD` | `sigaa` | Password for noVNC (`:6080`) and x11vnc (`:5900`) inside Docker |
| `DOWNLOAD_PATH` | `./downloads` | Output folder for generated PDFs and CSVs |
| `STORAGE_STATE_PATH` | `.sigaa_state/storage_state.json` | Optional cookie file (`0600`) when *"Keep session active"* is checked |
| `DRIVE_FOLDER_ID` | *(empty)* | Optional Google Drive folder ID for uploads and profile images |
| `DRIVE_CLIENT_SECRETS_PATH` | `client_secrets.json` | Path to Google OAuth 2.0 client secrets JSON |
| `DRIVE_TOKEN_PATH` | `token.json` | Path to cached Google OAuth 2.0 user token |

## Docker Ports & Volumes

When running `docker compose up -d --build`:

- **`8003`** — Streamable HTTP MCP endpoint (`/mcp`), Visual Login portal (`/login`), and healthcheck (`/health`).
- **`6080`** — Live browser view via noVNC (`http://localhost:6080/vnc.html?autoconnect=1&password=sigaa`).
- **`5900`** — Raw VNC port (`x11vnc`).
- **`./downloads`** — Mounted to `/app/downloads` so generated PDFs and CSVs appear directly on your host machine.
- **`./.sigaa_state`** — Mounted to `/app/.sigaa_state` for optional browser cookie persistence across container restarts.

## Optional Google Drive Integration

1. Create an OAuth 2.0 Desktop Client in Google Cloud Console with the **Google Drive API** enabled and save the JSON as `client_secrets.json` in the project root.
2. Set `DRIVE_FOLDER_ID` in `.env` to the target Google Drive folder ID.
3. Pass `enviar_drive=True` to `baixar_historico_escolar`, `emitir_atestado_matricula`, or `exportar_horarios_csv`, or browse Drive images via `resource://drive-images` and `abrir_estudio_perfil`.

All credential and session files (`.env`, `client_secrets.json`, `token.json`, `.sigaa_state/`) are excluded by both `.gitignore` and `.dockerignore`.
