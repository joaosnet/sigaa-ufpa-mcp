# Serviço Google Drive

> 15 nodes

## Key Concepts

- **GoogleDriveService** (20 connections) — `sigaa_mcp/drive_service.py`
- **.upload_arquivo()** (4 connections) — `sigaa_mcp/drive_service.py`
- **resource_drive_images()** (4 connections) — `sigaa_mcp/resources.py`
- **.download_bytes()** (3 connections) — `sigaa_mcp/drive_service.py`
- **.download_com_data_uri()** (3 connections) — `sigaa_mcp/drive_service.py`
- **.download_em_base64()** (3 connections) — `sigaa_mcp/drive_service.py`
- **._initialize_service()** (3 connections) — `sigaa_mcp/drive_service.py`
- **.listar_arquivos_na_pasta()** (3 connections) — `sigaa_mcp/drive_service.py`
- **Any** (3 connections)
- **._get_oauth_credentials()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.__init__()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.obter_mime_type()** (2 connections) — `sigaa_mcp/drive_service.py`
- **.upload_bytes()** (2 connections) — `sigaa_mcp/drive_service.py`
- **Path** (1 connections)
- **Google Drive v3 client authenticated via OAuth 2.0 (100% optional).** (1 connections) — `sigaa_mcp/drive_service.py`

## Relationships

- [Fluxos Acadêmicos e Parsers](Fluxos_Acadêmicos_e_Parsers.md) (3 shared connections)
- [Atualização de Foto de Perfil](Atualização_de_Foto_de_Perfil.md) (3 shared connections)
- [Recursos MCP](Recursos_MCP.md) (3 shared connections)
- [Helpers de Configuração do Drive](Helpers_de_Configuração_do_Drive.md) (3 shared connections)

## Source Files

- `sigaa_mcp/drive_service.py`
- `sigaa_mcp/resources.py`

## Audit Trail

- EXTRACTED: 31 (91%)
- INFERRED: 3 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*