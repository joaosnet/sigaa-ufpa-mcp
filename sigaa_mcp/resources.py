"""FastMCP 4.1 Resources and Resource Templates for status, Drive media, and local downloads."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from fastmcp import FastMCP

from sigaa_mcp.config import settings
from sigaa_mcp.drive_service import GoogleDriveService, is_drive_configured
from sigaa_mcp.session import session_manager


def register_resources(mcp: FastMCP) -> None:
    """Register the 4 static/templated MCP resources."""

    @mcp.resource(
        "resource://status-init",
        name="status-init",
        description="Estado da sessão SIGAA UFPA, modo de autenticação, URL de Login Visual e configuração opcional do Google Drive.",
        mime_type="application/json",
    )
    async def resource_status_init() -> str:
        estado = session_manager.get_estado_sessao()
        payload = {
            "servidor": "sigaa-ufpa-mcp",
            "motor": "playwright-deterministico-zero-token",
            "sessao": estado.model_dump(mode="json"),
            "google_drive_configurado": is_drive_configured(),
            "diretorio_downloads": str(settings.download_dir),
            "headless": settings.chrome_headless,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.resource(
        "resource://drive-images",
        name="drive-images",
        description="Lista imagens disponíveis na pasta configurada do Google Drive (retorna vazio com aviso amigável se não configurado).",
        mime_type="application/json",
    )
    async def resource_drive_images() -> str:
        if not is_drive_configured():
            return json.dumps(
                {
                    "configurado": False,
                    "mensagem": "Google Drive opcional não configurado. Use 'caminho_ou_url' para enviar imagens locais ou URLs HTTPS.",
                    "imagens": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        try:
            svc = GoogleDriveService()
            arquivos = svc.listar_arquivos_na_pasta()
            imagens = [
                arq
                for arq in arquivos
                if str(arq.get("mimeType", "")).startswith("image/")
            ]
            return json.dumps(
                {
                    "configurado": True,
                    "total_imagens": len(imagens),
                    "imagens": imagens,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as exc:
            return json.dumps(
                {"configurado": False, "erro": str(exc), "imagens": []},
                ensure_ascii=False,
                indent=2,
            )

    @mcp.resource(
        "resource://downloads",
        name="downloads-list",
        description="Lista todos os documentos acadêmicos gerados localmente em ./downloads (PDFs e CSVs).",
        mime_type="application/json",
    )
    async def resource_downloads_list() -> str:
        settings.download_dir.mkdir(parents=True, exist_ok=True)
        items = []
        for fpath in sorted(
            settings.download_dir.iterdir(),
            key=lambda p: p.stat().st_mtime if p.is_file() else 0,
            reverse=True,
        ):
            if not fpath.is_file() or fpath.name.startswith("."):
                continue
            stat_info = fpath.stat()
            mime, _ = mimetypes.guess_type(fpath.name)
            items.append(
                {
                    "filename": fpath.name,
                    "uri": f"resource://downloads/{fpath.name}",
                    "path": str(fpath.resolve()),
                    "size_bytes": stat_info.st_size,
                    "mime_type": mime or "application/octet-stream",
                }
            )
        return json.dumps(
            {
                "diretorio": str(settings.download_dir),
                "total_arquivos": len(items),
                "arquivos": items,
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.resource(
        "resource://downloads/{filename}",
        name="download-file-by-name",
        description="Lê o conteúdo de um arquivo específico gerado em ./downloads (texto direto para CSV ou metadados+base64 para PDF).",
        mime_type="application/json",
    )
    async def resource_download_file(filename: str) -> str:
        safe_name = Path(filename).name
        if safe_name != filename or ".." in filename:
            raise ValueError("Nome de arquivo inválido.")

        target = (settings.download_dir / safe_name).resolve()
        if target.parent != settings.download_dir.resolve() or not target.is_file():
            raise FileNotFoundError(f"Arquivo '{safe_name}' não encontrado em {settings.download_dir}.")

        mime, _ = mimetypes.guess_type(target.name)
        mime = mime or "application/octet-stream"
        if mime.startswith("text/") or target.suffix.lower() in {".csv", ".txt", ".json", ".md"}:
            return json.dumps(
                {
                    "filename": target.name,
                    "mime_type": mime,
                    "encoding": "utf-8",
                    "content": target.read_text(encoding="utf-8", errors="replace"),
                },
                ensure_ascii=False,
                indent=2,
            )

        raw = target.read_bytes()
        return json.dumps(
            {
                "filename": target.name,
                "mime_type": mime,
                "size_bytes": len(raw),
                "encoding": "base64",
                "content_base64": base64.b64encode(raw).decode("ascii"),
            },
            ensure_ascii=False,
            indent=2,
        )
