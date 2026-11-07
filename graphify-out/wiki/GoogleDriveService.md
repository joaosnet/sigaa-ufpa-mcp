# GoogleDriveService

> God node · 22 connections · `sigaa_mcp/drive_service.py`

**Community:** [Serviço OAuth 2.0 Google Drive](Serviço_OAuth_2.0_Google_Drive.md)

## Connections by Relation

### calls
- _resolve_profile_image() `EXTRACTED`
- register_resources() `EXTRACTED`
- _maybe_upload_to_drive() `EXTRACTED`
- resource_drive_images() `EXTRACTED`

### contains
- sigaa_mcp/drive_service.py `EXTRACTED`

### imports
- academico.py `EXTRACTED`
- perfil_app.py `EXTRACTED`
- perfil.py `EXTRACTED`
- resources.py `EXTRACTED`
- drive_service.py `EXTRACTED`

### method
- .listar_arquivos_na_pasta() `EXTRACTED`
- .upload_arquivo() `EXTRACTED`
- .download_bytes() `EXTRACTED`
- .download_em_base64() `EXTRACTED`
- .download_com_data_uri() `EXTRACTED`
- ._initialize_service() `EXTRACTED`
- .obter_mime_type() `EXTRACTED`
- .upload_bytes() `EXTRACTED`
- .__init__() `EXTRACTED`
- ._get_oauth_credentials() `EXTRACTED`

### rationale_for
- Google Drive v3 client authenticated via OAuth 2.0 (100% optional). `EXTRACTED`

### uses
- abrir_estudio_perfil() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*