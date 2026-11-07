# GoogleDriveService

> **God Node** ? 14 conex?es ? Fonte: `drive_service.py`
> **Comunidade:** [Integra??o com Google Drive](Integracao_com_Google_Drive.md)

## Descri??o Arquitetural
Classe central respons?vel pela comunica??o com o Google Drive API v3. Gerencia o ciclo de vida dos tokens OAuth2, renova??o de credenciais e opera??es de I/O em mem?ria para download e upload de imagens e documentos.

## M?todos Chave
* `download_em_base64(file_id)`: Recupera o payload bin?rio do arquivo especificado e o retorna codificado em Base64, evitando escrita desnecess?ria em disco at? o momento exato de uso.
* `listar_arquivos_na_pasta(folder_id)`: Consulta todos os arquivos contidos na pasta de trabalho definida pelo `DRIVE_FOLDER_ID`.
* `upload_arquivo(caminho_local, nome_arquivo, folder_id)`: Realiza upload com suporte a chunking para arquivos grandes.

## Depend?ncias e Consumidores
* Consumido diretamente por [`trocar_imagem_perfil()`](trocar_imagem_perfil.md) em `server.py`.
* Alimenta o recurso `get_drive_images()` exposto em `resource://drive-images`.

---
*Parte da Wiki de Conhecimento do Graphify. Veja o [?ndice](index.md).*
