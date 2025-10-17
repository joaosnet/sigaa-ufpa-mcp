import io
import base64
import logging
import os
from typing import List, Dict, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload

from dotenv import load_dotenv

load_dotenv()
# Configurações Google Drive via variáveis de ambiente
DRIVE_CLIENT_SECRETS_PATH = os.getenv(
    "DRIVE_CLIENT_SECRETS_PATH", "client_secrets.json"
)
DRIVE_TOKEN_PATH = os.getenv("DRIVE_TOKEN_PATH", "token.json")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", None)


def get_drive_config() -> tuple[str, str]:
    """
    Retorna as configurações do Google Drive das variáveis de ambiente.

    Returns:
        Tupla com (client_secrets_path, folder_id)
    """
    return DRIVE_CLIENT_SECRETS_PATH, DRIVE_FOLDER_ID


def is_drive_configured() -> bool:
    """
    Verifica se as configurações do Google Drive estão disponíveis.

    Returns:
        True se o client_secrets.json existe e folder_id está definido
    """
    client_secrets, folder = get_drive_config()
    return bool(client_secrets and folder and os.path.exists(client_secrets))


class GoogleDriveService:
    """
    Serviço para interagir com o Google Drive API usando OAuth 2.0.
    """

    def __init__(
        self,
        client_secrets_path: Optional[str] = None,
        token_path: Optional[str] = None,
        folder_id: Optional[str] = None,
    ):
        """
        Inicializa o serviço do Google Drive usando OAuth 2.0.

        Args:
            client_secrets_path: Caminho para client_secrets.json
                               (usa DRIVE_CLIENT_SECRETS_PATH se None)
            token_path: Caminho onde salvar token.json
                       (usa DRIVE_TOKEN_PATH se None)
            folder_id: ID da pasta no Drive onde salvar arquivos
                      (usa DRIVE_FOLDER_ID se None)
        """
        # Usa configurações do ambiente se não fornecidas
        self.client_secrets_path = client_secrets_path or DRIVE_CLIENT_SECRETS_PATH
        self.token_path = token_path or DRIVE_TOKEN_PATH
        self.folder_id = folder_id or DRIVE_FOLDER_ID

        if not self.client_secrets_path or not os.path.exists(self.client_secrets_path):
            raise ValueError(
                f"Arquivo client_secrets.json não encontrado: {self.client_secrets_path}"
            )
        if not self.folder_id:
            raise ValueError("DRIVE_FOLDER_ID não configurado")

        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Inicializa o serviço do Google Drive usando OAuth 2.0."""
        try:
            creds = self._get_oauth_credentials()
            self.service = build("drive", "v3", credentials=creds)
            logging.info("Google Drive service inicializado com sucesso (OAuth).")
        except Exception as e:
            logging.error(f"Erro ao inicializar Google Drive service: {e}")
            raise

    def _get_oauth_credentials(self):
        """Obtém credenciais OAuth 2.0."""
        creds = None

        # Verifica se já temos um token salvo
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(
                self.token_path, ["https://www.googleapis.com/auth/drive.file"]
            )

        # Se não há credenciais válidas, faz o login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_path,
                    ["https://www.googleapis.com/auth/drive.file"],
                )
                creds = flow.run_local_server(port=0)

            # Salva o token para uso futuro
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    def listar_arquivos_na_pasta(self, folder_id: Optional[str] = None) -> List[Dict]:
        """
        Lista arquivos em uma pasta específica.

        Args:
            folder_id: ID da pasta (usa self.folder_id se None)

        Returns:
            Lista de dicionários com id, name, mimeType dos arquivos
        """
        if folder_id is None:
            folder_id = self.folder_id

        query = f"'{folder_id}' in parents and trashed=false"
        try:
            resultados = (
                self.service.files()
                .list(q=query, fields="files(id, name, mimeType)")
                .execute()
            )
            return resultados.get("files", [])
        except Exception as e:
            logging.error(f"Erro ao listar arquivos: {e}")
            return []

    def download_em_base64(self, file_id: str) -> Optional[str]:
        """
        Faz download de um arquivo e retorna em base64.

        Args:
            file_id: ID do arquivo no Drive

        Returns:
            String base64 do arquivo ou None se erro
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buffer.seek(0)
            encoded = base64.b64encode(buffer.read()).decode("utf-8")
            return encoded
        except Exception as e:
            logging.error(f"Erro ao fazer download do arquivo {file_id}: {e}")
            return None

    def obter_mime_type(self, file_id: str) -> Optional[str]:
        """
        Obtém o MIME type de um arquivo.

        Args:
            file_id: ID do arquivo

        Returns:
            MIME type ou None se erro
        """
        try:
            info = self.service.files().get(fileId=file_id, fields="mimeType").execute()
            return info.get("mimeType")
        except Exception as e:
            logging.error(f"Erro ao obter MIME type: {e}")
            return None

    def download_com_data_uri(self, file_id: str) -> Optional[str]:
        """
        Faz download e retorna como data URI.

        Args:
            file_id: ID do arquivo

        Returns:
            String data URI ou None se erro
        """
        mime = self.obter_mime_type(file_id)
        if not mime:
            return None

        b64 = self.download_em_base64(file_id)
        if not b64:
            return None

        return f"data:{mime};base64,{b64}"

    def upload_arquivo(
        self,
        caminho_local: str,
        nome_no_drive: Optional[str] = None,
        pasta_destino_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Faz upload de um arquivo para o Google Drive.

        Args:
            caminho_local: Caminho do arquivo local
            nome_no_drive: Nome no Drive (default: nome original)
            pasta_destino_id: ID da pasta destino (default: self.folder_id)
            mime_type: MIME type (default: detectado automaticamente)

        Returns:
            Metadados do arquivo criado ou None se erro
        """
        try:
            if not nome_no_drive:
                nome_no_drive = os.path.basename(caminho_local)

            if not pasta_destino_id:
                pasta_destino_id = self.folder_id

            metadata = {"name": nome_no_drive}
            if pasta_destino_id:
                metadata["parents"] = [pasta_destino_id]

            media = MediaFileUpload(
                filename=caminho_local, mimetype=mime_type, resumable=True
            )

            arquivo = (
                self.service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, mimeType, parents",
                )
                .execute()
            )

            logging.info(
                f"Arquivo {nome_no_drive} enviado com sucesso (ID: {arquivo['id']})"
            )
            return arquivo

        except Exception as e:
            logging.error(f"Erro ao fazer upload do arquivo {caminho_local}: {e}")
            return None

    def upload_bytes(
        self,
        data: bytes,
        nome_no_drive: str,
        pasta_destino_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
    ) -> Optional[Dict]:
        """
        Faz upload de bytes diretamente para o Google Drive.

        Args:
            data: Bytes do arquivo
            nome_no_drive: Nome no Drive
            pasta_destino_id: ID da pasta destino (default: self.folder_id)
            mime_type: MIME type

        Returns:
            Metadados do arquivo criado ou None se erro
        """
        try:
            if not pasta_destino_id:
                pasta_destino_id = self.folder_id

            metadata = {"name": nome_no_drive}
            if pasta_destino_id:
                metadata["parents"] = [pasta_destino_id]

            media = MediaIoBaseUpload(
                io.BytesIO(data), mimetype=mime_type, resumable=True
            )

            arquivo = (
                self.service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, mimeType, parents",
                )
                .execute()
            )

            logging.info(
                f"Arquivo {nome_no_drive} enviado com sucesso (ID: {arquivo['id']})"
            )
            return arquivo

        except Exception as e:
            logging.error(f"Erro ao fazer upload de bytes como {nome_no_drive}: {e}")
            return None

    def upload_temp_images(
        self, temp_file_paths: List[str], base_filename: str
    ) -> List[Dict]:
        """
        Faz upload de múltiplas imagens temporárias para o Google Drive.

        Args:
            temp_file_paths: Lista de caminhos para arquivos temporários
            base_filename: Nome base para os arquivos (ex: "generated_image_20231007_143022")

        Returns:
            Lista de dicionários com informações dos arquivos enviados
        """
        uploaded_files = []

        for i, temp_path in enumerate(temp_file_paths):
            filename = f"{base_filename}_{i + 1}.png"

            result = self.upload_arquivo(
                caminho_local=temp_path, nome_no_drive=filename, mime_type="image/png"
            )

            if result:
                file_info = {
                    "id": result["id"],
                    "name": result["name"],
                    "drive_link": f"https://drive.google.com/file/d/{result['id']}/view",
                }
                uploaded_files.append(file_info)
            else:
                logging.warning(f"Falha ao fazer upload da imagem {filename}")

        return uploaded_files
