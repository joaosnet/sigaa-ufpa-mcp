# Serviço OAuth 2.0 Google Drive

> 15 nodes · cohesion 0.21

## Key Concepts

- **GoogleDriveService** (22 connections) — `sigaa_mcp/drive_service.py`
- **.listar_arquivos_na_pasta()** (4 connections) — `sigaa_mcp/drive_service.py`
- **.upload_arquivo()** (4 connections) — `sigaa_mcp/drive_service.py`
- **resource_drive_images()** (4 connections) — `sigaa_mcp/resources.py`
- **.download_bytes()** (3 connections) — `sigaa_mcp/drive_service.py`
- **.download_com_data_uri()** (3 connections) — `sigaa_mcp/drive_service.py`
- **.download_em_base64()** (3 connections) — `sigaa_mcp/drive_service.py`
- **._initialize_service()** (3 connections) — `sigaa_mcp/drive_service.py`
- **Any** (3 connections)
- **._get_oauth_credentials()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.__init__()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.obter_mime_type()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.upload_bytes()** (2 connections) — `sigaa_mcp/drive_service.py`
- **Path** (1 connections)
- **Google Drive v3 client authenticated via OAuth 2.0 (100% optional).** (1 connections) — `sigaa_mcp/drive_service.py`

## Relationships

- [Resources MCP & Templates de Downloads](Resources_MCP_&_Templates_de_Downloads.md) (4 shared connections)
- [Parsers, Horários UFPA & Schemas Acadêmicos](Parsers,_Horários_UFPA_&_Schemas_Acadêmicos.md) (3 shared connections)
- [Fluxo de Troca e Simulação de Perfil](Fluxo_de_Troca_e_Simulação_de_Perfil.md) (3 shared connections)
- [Módulos de Recursos e Sessão](Módulos_de_Recursos_e_Sessão.md) (2 shared connections)
- [PerfilDiscenteApp (FastMCPApp)](PerfilDiscenteApp_FastMCPApp.md) (2 shared connections)
- [Tools FastMCP 4.1, Prefab UI & Autenticação](Tools_FastMCP_4.1,_Prefab_UI_&_Autenticação.md) (1 shared connections)

## Source Files

- `sigaa_mcp/drive_service.py`
- `sigaa_mcp/resources.py`

## Audit Trail

- EXTRACTED: 32 (86%)
- INFERRED: 5 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*