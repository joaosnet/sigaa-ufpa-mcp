# FastMCP Apps, Tools, Prompts & Resources

[← Back to README](../README.md) · [Português](pt-BR.md) · [Español](es.md)

## Interactive FastMCP Apps (`@app.ui`)

Preview locally with `uv run fastmcp dev apps server.py` or open directly inside any MCP Apps host:

| App Provider | Entry Tool | Description |
| :--- | :--- | :--- |
| `AutenticacaoSigaaApp` | `abrir_login_sigaa` | Masked password sign-in (`app-only` callback hidden from LLMs), multi-vínculo selector, cookie persistence toggle, and logout. Returned automatically when a protected tool is called while signed out. |
| `PainelAcademicoApp` | `abrir_painel_academico` | Tabbed student dashboard with academic indices (`CRG`, `MC`, `IEA`), enrolled classes, filterable grade/attendance tables, notices, and one-click PDF generation. |
| `ExploradorTurmasApp` | `abrir_explorador_turmas` | Searches UFPA course offerings across shifts (`M`/`T`/`N`), highlights timetable collisions against your current classes, and exports your schedule as CSV. |
| `PerfilDiscenteApp` | `abrir_estudio_perfil` | Validates, simulates (`dry_run=True`), or applies a new profile picture (local file, HTTPS URL, or Google Drive ID) and bio. |

## 10 Model-Facing Tools

Every tool returns a dual `ToolResult`: structured UTF-8 JSON in `content[0].text` for the model and an interactive `Prefab` UI view in `structured_content`.

| Tool | Safety | Description |
| :--- | :---: | :--- |
| `baixar_historico_escolar(enviar_drive=False)` | Read-only | Downloads the official *Histórico Escolar* PDF and extracts `CRG`, `MC`, `IEA`, credit hours, and pending mandatory courses. |
| `emitir_atestado_matricula(enviar_drive=False)` | Read-only | Emits the *Atestado de Matrícula* (with automatic supplemental-period fallback), saves the PDF via CDP, and parses enrolled classes + verification code. |
| `consultar_notas_frequencia(semestre=None)` | Read-only | Extracts UFPA grades/concepts (`E`, `B`, `R`, `I`, `S`), unit evaluations, absences, and status across all or selected semesters. |
| `listar_atividades_pendentes(incluir_concluidas=False)` | Read-only | Scans the student portal and each enrolled virtual classroom (*AVA*) for tasks, quizzes, and exams. |
| `exportar_horarios_csv(enviar_drive=False)` | Read-only | Decodes UFPA schedule strings into 50-minute weekly slots, checks for overlaps, and writes a UTF-8 CSV to `./downloads`. |
| `listar_avisos_turmas(disciplina_filtro=None, limite_por_turma=5)` | Read-only | Collects professor announcements from the portal ticker and AVA news boards. |
| `listar_disciplinas_ofertadas(curso, turno=None, ano=None, periodo=None)` | Read-only | Searches offered classes by course or institute and flags conflicts against your enrolled timetable. |
| `trocar_imagem_perfil(drive_file_id=None, caminho_ou_url=None, descricao=None, dry_run=False)` | Write | Updates (or simulates when `dry_run=True`) your SIGAA profile picture and description, reading confirmation fields in RAM only. |
| `reiniciar_sessao()` | Idempotent | Restarts the Playwright browser context, clears cached responses, and re-validates the active session. |
| `encerrar_sessao()` | Destructive | Logs out of SIGAA, wipes credentials from RAM, deletes `.sigaa_state/storage_state.json`, and clears the cache. |

## 3 Academic Prompts

- `planejar_matricula_semestre(curso, turno_preferido="")` — Cross-references pending mandatory courses from your transcript with conflict-free offered classes.
- `briefing_semana_academica()` — Summarizes upcoming tasks, professor announcements, and attendance counts ordered by deadline.
- `auditar_integralizacao_curricular()` — Reviews completed vs. required credit hours and remaining graduation requirements.

## 4 MCP Resources

- `resource://status-init` — Current authentication state, active vínculo, persistence mode, and Google Drive status.
- `resource://drive-images` — Lists image files inside the optional Google Drive folder.
- `resource://downloads` — Lists generated PDFs and CSVs inside `./downloads`.
- `resource://downloads/{filename}` — Reads a generated CSV (UTF-8 text) or PDF (base64 + metadata) with path-traversal protection.

## UFPA Schedule Code Reference

UFPA formats class schedules as `<Weekdays><Shift><Slots>`, such as `24M56` (Monday & Wednesday, Morning slots 5 and 6 -> `11:10–12:50`):

- **Weekdays:** `2` = Mon, `3` = Tue, `4` = Wed, `5` = Thu, `6` = Fri, `7` = Sat
- **Morning (`M`):** `1` (07:30–08:20), `2` (08:20–09:10), `3` (09:20–10:10), `4` (10:10–11:00), `5` (11:10–12:00), `6` (12:00–12:50)
- **Afternoon (`T`):** `1` (13:00–13:50), `2` (13:50–14:40), `3` (14:50–15:40), `4` (15:40–16:30), `5` (16:40–17:30), `6` (17:30–18:20)
- **Evening (`N`):** `1` (18:30–19:20), `2` (19:20–20:10), `3` (20:10–21:00), `4` (21:00–21:50)
