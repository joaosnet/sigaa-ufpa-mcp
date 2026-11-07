"""Optional Google Drive OAuth 2.0 integration for SIGAA UFPA MCP."""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from sigaa_mcp.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_config() -> tuple[str, str]:
    """Return (client_secrets_path, folder_id) from runtime settings."""
    client_secrets = os.getenv("DRIVE_CLIENT_SECRETS_PATH") or str(settings.drive_client_secrets_path)
    folder_id = os.getenv("DRIVE_FOLDER_ID") or settings.drive_folder_id
    return client_secrets, folder_id


def is_drive_configured() -> bool:
    """Return True only when client_secrets.json exists on disk and DRIVE_FOLDER_ID is set."""
    client_secrets, folder_id = get_drive_config()
    if not client_secrets or not folder_id:
        return False
    return Path(client_secrets).is_file()


class GoogleDriveService:
    """Google Drive v3 client authenticated via OAuth 2.0 (100% optional)."""

    def __init__(
        self,
        client_secrets_path: Optional[str] = None,
        token_path: Optional[str] = None,
        folder_id: Optional[str] = None,
        interactive_auth: bool = False,
    ) -> None:
        self.client_secrets_path = Path(
            client_secrets_path
            or os.getenv("DRIVE_CLIENT_SECRETS_PATH")
            or settings.drive_client_secrets_path
        )
        self.token_path = Path(
            token_path
            or os.getenv("DRIVE_TOKEN_PATH")
            or settings.drive_token_path
        )
        self.folder_id = (
            folder_id
            or os.getenv("DRIVE_FOLDER_ID")
            or settings.drive_folder_id
        )
        self.interactive_auth = interactive_auth

        if not self.client_secrets_path.is_file():
            raise ValueError(
                f"Google Drive não configurado: arquivo '{self.client_secrets_path}' não encontrado."
            )
        if not self.folder_id:
            raise ValueError("Google Drive não configurado: DRIVE_FOLDER_ID vazio.")

        self.service: Any = None
        self._initialize_service()

    def _initialize_service(self) -> None:
        from googleapiclient.discovery import build

        creds = self._get_oauth_credentials()
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)
        logger.debug("Google Drive service inicializado com sucesso.")

    def _get_oauth_credentials(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if self.token_path.is_file():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif self.interactive_auth:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            else:
                raise RuntimeError(
                    f"Token OAuth do Google Drive ausente ou expirado em '{self.token_path}'. "
                    "Gere o token OAuth localmente antes de usar em modo headless/Docker."
                )

            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def listar_arquivos_na_pasta(self, folder_id: Optional[str] = None) -> list[dict[str, Any]]:
        target_folder = folder_id or self.folder_id
        query = f"'{target_folder}' in parents and trashed=false"
        try:
            resultados = (
                self.service.files()
                .list(q=query, fields="files(id, name, mimeType, size, modifiedTime)")
                .execute()
            )
            return resultados.get("files", [])
        except Exception as exc:
            logger.error(f"Erro ao listar arquivos no Google Drive: {exc}")
            return []

    def download_bytes(self, file_id: str) -> Optional[bytes]:
        from googleapiclient.http import MediaIoBaseDownload

        try:
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue()
        except Exception as exc:
            logger.error(f"Erro ao baixar arquivo {file_id} do Google Drive: {exc}")
            return None

    def download_em_base64(self, file_id: str) -> Optional[str]:
        raw = self.download_bytes(file_id)
        if raw is None:
            return None
        return base64.b64encode(raw).decode("utf-8")

    def obter_mime_type(self, file_id: str) -> Optional[str]:
        try:
            info = self.service.files().get(fileId=file_id, fields="mimeType").execute()
            return info.get("mimeType")
        except Exception as exc:
            logger.error(f"Erro ao obter MIME type de {file_id}: {exc}")
            return None

    def download_com_data_uri(self, file_id: str) -> Optional[str]:
        mime = self.obter_mime_type(file_id)
        if not mime:
            return None
        b64 = self.download_em_base64(file_id)
        if not b64:
            return None
        return f"data:{mime};base64,{b64}"

    def upload_bytes(
        self,
        data: bytes,
        nome_no_drive: str,
        pasta_destino_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
    ) -> Optional[dict[str, Any]]:
        from googleapiclient.http import MediaIoBaseUpload

        try:
            target_parent = pasta_destino_id or self.folder_id
            metadata: dict[str, Any] = {"name": nome_no_drive}
            if target_parent:
                metadata["parents"] = [target_parent]
            media = MediaIoBaseUpload(
                io.BytesIO(data), mimetype=mime_type, resumable=True
            )
            arquivo = (
                self.service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, mimeType, webViewLink",
                )
                .execute()
            )
            arquivo.setdefault(
                "drive_link", f"https://drive.google.com/file/d/{arquivo['id']}/view"
            )
            return arquivo
        except Exception as exc:
            logger.error(f"Erro no upload_bytes para o Google Drive ({nome_no_drive}): {exc}")
            return None

    def upload_arquivo(
        self,
        caminho_local: str | Path,
        nome_no_drive: Optional[str] = None,
        pasta_destino_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        from googleapiclient.http import MediaFileUpload

        local_path = Path(caminho_local)
        if not local_path.is_file():
            logger.error(f"Arquivo local não encontrado para upload: {local_path}")
            return None

        try:
            target_name = nome_no_drive or local_path.name
            target_parent = pasta_destino_id or self.folder_id
            metadata: dict[str, Any] = {"name": target_name}
            if target_parent:
                metadata["parents"] = [target_parent]

            media = MediaFileUpload(
                filename=str(local_path), mimetype=mime_type, resumable=True
            )
            arquivo = (
                self.service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, mimeType, webViewLink",
                )
                .execute()
            )
            arquivo.setdefault(
                "drive_link", f"https://drive.google.com/file/d/{arquivo['id']}/view"
            )
            logger.info(f"Upload concluído no Google Drive: {target_name} ({arquivo['id']})")
            return arquivo
        except Exception as exc:
            logger.error(f"Erro no upload para o Google Drive ({local_path}): {exc}")
            return None
