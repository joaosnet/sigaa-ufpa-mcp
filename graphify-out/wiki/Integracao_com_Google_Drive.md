# Integra??o com Google Drive

> **Comunidade 2** ? 25 n?s ? Coes?o: 0.10 ? Fonte prim?ria: `drive_service.py`

## Vis?o Geral
M?dulo respons?vel pela ponte entre o ecossistema de arquivos em nuvem (Google Drive) e as ferramentas do SIGAA, permitindo ler e persistir anexos, documentos e fotos de perfil acad?micas sem depender de armazenamento local fixo no host.

---

## ??? Recursos e M?todos do `GoogleDriveService`

### `listar_arquivos_na_pasta(folder_id=None)`
* Lista todos os metadados dos arquivos localizados na pasta remota configurada (`DRIVE_FOLDER_ID`), incluindo `id`, `name` e `mimeType`.
* Alimenta diretamente o endpoint FastMCP `resource://drive-images`.

### `download_em_base64(file_id)`
* Efetua o download do conte?do bin?rio de um arquivo a partir da API Google Drive e codifica em formato Base64.
* Permite transportar a imagem de forma segura em mem?ria ou serializada em JSON para que o `server.py` gere o arquivo tempor?rio local utilizado no upload do SIGAA.

### `upload_arquivo(...)` & `deletar_arquivo(...)`
* Permite enviar novos arquivos ou descartar itens na pasta mapeada do Drive.

---

## ?? Vari?veis e Arquivos de Configura??o
* `DRIVE_CLIENT_SECRETS_PATH`: Caminho padr?o para `client_secrets.json` (OAuth2 client creds).
* `DRIVE_TOKEN_PATH`: Caminho padr?o para `token.json` (armazena tokens de acesso e refresh).
* `DRIVE_FOLDER_ID`: Identificador ?nico da pasta no Google Drive destinada a armazenar fotos e arquivos.

## ?? Rela??es
* Conecta-se ? comunidade [Configura??o de Autentica??o do Google Drive](Configuracao_de_Autenticacao_do_Google_Drive.md) e ao servi?o discente [Servi?os do Portal Discente SIGAA](Servicos_do_Portal_Discente_SIGAA.md).
