"""Student profile photo & personal description update flow (with dry_run simulation)."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from sigaa_mcp.auth import ensure_authenticated_portal
from sigaa_mcp.config import settings
from sigaa_mcp.drive_service import GoogleDriveService, is_drive_configured
from sigaa_mcp.flows.academico import _report
from sigaa_mcp.parsers import clean_ws, parse_dados_pessoais_html
from sigaa_mcp.schemas import ResultadoTrocaPerfil
from sigaa_mcp.session import SigaaSessionManager, session_manager

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _detect_image_extension(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


async def _resolve_profile_image(
    drive_file_id: Optional[str],
    caminho_ou_url: Optional[str],
) -> tuple[Path, str, bool]:
    """Resolve image from local file, HTTP(S) URL, data URI, or Google Drive ID.

    Returns ``(local_path, source_label, is_temporary)``.
    """
    raw_bytes: Optional[bytes] = None
    source_label = ""

    if caminho_ou_url and caminho_ou_url.strip():
        ref = caminho_ou_url.strip()
        if ref.startswith("data:image/"):
            header, _, b64_part = ref.partition(",")
            raw_bytes = base64.b64decode(b64_part)
            source_label = f"data_uri ({header[:30]})"
        elif ref.startswith(("http://", "https://")):
            async with httpx.AsyncClient(follow_redirects=True, timeout=25.0) as client:
                resp = await client.get(ref)
                resp.raise_for_status()
                raw_bytes = resp.content
            source_label = f"url ({ref[:80]})"
        else:
            local_candidate = Path(ref).expanduser().resolve()
            if not local_candidate.is_file():
                raise FileNotFoundError(f"Arquivo de imagem local não encontrado: {local_candidate}")
            data = local_candidate.read_bytes()
            if len(data) > MAX_IMAGE_BYTES:
                raise ValueError("A imagem excede o limite máximo permitido de 5 MB.")
            ext = _detect_image_extension(data)
            if not ext:
                raise ValueError("Formato de arquivo inválido. Envie uma imagem PNG, JPG, GIF ou WEBP.")
            return local_candidate, f"arquivo_local ({local_candidate.name})", False

    elif drive_file_id and drive_file_id.strip():
        if not is_drive_configured():
            raise ValueError(
                "Google Drive não configurado (client_secrets.json / DRIVE_FOLDER_ID ausentes). "
                "Informe 'caminho_ou_url' com arquivo local ou URL direta."
            )
        svc = GoogleDriveService()
        raw_bytes = svc.download_bytes(drive_file_id.strip())
        if not raw_bytes:
            raise RuntimeError(f"Não foi possível baixar o arquivo '{drive_file_id}' do Google Drive.")
        source_label = f"google_drive ({drive_file_id.strip()})"
    else:
        raise ValueError(
            "Forneça 'caminho_ou_url' (caminho local, URL https ou data URI) ou 'drive_file_id'."
        )

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("A imagem excede o limite máximo permitido de 5 MB.")

    ext = _detect_image_extension(raw_bytes)
    if not ext:
        raise ValueError("Os bytes recebidos não correspondem a uma imagem válida (PNG/JPG/GIF/WEBP).")

    tmp_file = tempfile.NamedTemporaryFile(prefix="sigaa_perfil_", suffix=ext, delete=False)
    tmp_path = Path(tmp_file.name)
    tmp_file.write(raw_bytes)
    tmp_file.close()
    return tmp_path, source_label, True


async def trocar_imagem_perfil_flow(
    drive_file_id: Optional[str] = None,
    caminho_ou_url: Optional[str] = None,
    descricao: Optional[str] = None,
    dry_run: bool = False,
    ctx: Any = None,
    session: Optional[SigaaSessionManager] = None,
) -> ResultadoTrocaPerfil:
    """Validate and update (or simulate when dry_run=True) the student's SIGAA profile photo."""
    mgr = session or session_manager
    img_path, origem_label, is_temp = await _resolve_profile_image(drive_file_id, caminho_ou_url)

    try:
        async with mgr.lock:
            await _report(ctx, 1, 4, "Autenticando e lendo dados de confirmação cadastral em RAM...")
            page = await ensure_authenticated_portal(ctx=ctx, session=mgr)
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )

            # Read CPF and Birth Date strictly in RAM from Meus Dados Pessoais
            dados_pessoais: dict[str, str] = {}
            mdp_link = page.locator(
                "a[id$=':meusDadosPessoais'], a:has-text('Meus Dados Pessoais')"
            ).first
            if await mdp_link.count() > 0:
                try:
                    async with page.expect_navigation(
                        wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
                    ):
                        await mdp_link.click()
                    dados_pessoais = parse_dados_pessoais_html(await page.content())
                except Exception as exc:
                    logger.debug(f"Leitura auxiliar de Meus Dados Pessoais ignorada: {exc}")

            await _report(ctx, 2, 4, "Abrindo tela 'Atualizar Foto e Perfil' no Portal do Discente...")
            await page.goto(
                f"{settings.base_url}/sigaa/verPortalDiscente.do",
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_ms,
            )
            perfil_link = page.locator("a.perfil, a:has-text('Atualizar Foto e Perfil')").first
            if await perfil_link.count() == 0:
                raise RuntimeError("Link 'Atualizar Foto e Perfil' não localizado no Portal do Discente.")

            async with page.expect_navigation(
                wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
            ):
                await perfil_link.click()

            # Select local file upload radio if present
            radio_arquivo = page.locator("input#tipoenviofotoarquivo, input[type='radio'][value*='arquivo']").first
            if await radio_arquivo.count() > 0:
                try:
                    await radio_arquivo.check()
                except Exception:
                    pass

            file_input = page.locator("input#alterarFoto, input[type='file']").first
            if await file_input.count() == 0:
                raise RuntimeError("Campo de upload de foto ('input#alterarFoto') não encontrado na página.")
            await file_input.set_input_files(str(img_path))

            if descricao is not None:
                desc_area = page.locator("textarea#descricaoPessoal, textarea[name*='descricao']").first
                if await desc_area.count() > 0:
                    await desc_area.fill(descricao)

            # Populate optional confirmation fields if requested by SIGAA UFPA's profile form
            cpf_filled = False
            nasc_filled = False
            cpf_inp = page.locator("input#cpf, input[name*='cpf']").first
            if await cpf_inp.count() > 0 and dados_pessoais.get("cpf"):
                await cpf_inp.fill(dados_pessoais["cpf"])
                cpf_filled = True

            nasc_inp = page.locator("input#dataNascimento, input[name*='Nascimento']").first
            if await nasc_inp.count() > 0 and dados_pessoais.get("data_nascimento"):
                await nasc_inp.fill(dados_pessoais["data_nascimento"])
                nasc_filled = True

            senha_inp = page.locator("input#senha, input[type='password']").first
            if await senha_inp.count() > 0 and mgr.get_password_for_form():
                await senha_inp.fill(mgr.get_password_for_form())

            if dry_run:
                await page.goto(
                    f"{settings.base_url}/sigaa/verPortalDiscente.do",
                    wait_until="domcontentloaded",
                    timeout=settings.browser_timeout_ms,
                )
                await _report(ctx, 4, 4, "Simulação dry_run concluída sem gravar alterações.")
                return ResultadoTrocaPerfil(
                    sucesso=True,
                    modo_simulacao=True,
                    mensagem=(
                        "Simulação concluída com sucesso (dry_run=True): formulário 'Atualizar Foto e Perfil' "
                        "preenchido e validado sem submeter alterações na conta real."
                    ),
                    origem_imagem=origem_label,
                    arquivo_validado=img_path.name,
                    cpf_detectado_automaticamente=cpf_filled or bool(dados_pessoais.get("cpf")),
                    data_nascimento_detectada_automaticamente=nasc_filled or bool(dados_pessoais.get("data_nascimento")),
                    descricao_aplicada=descricao,
                )

            await _report(ctx, 3, 4, "Gravando nova foto e perfil no SIGAA UFPA...")
            submit_btn = page.locator(
                "input[type='submit'][value*='Gravar'], input[value='Gravar perfil']"
            ).first
            async with page.expect_navigation(
                wait_until="domcontentloaded", timeout=settings.browser_timeout_ms
            ):
                await submit_btn.click()

            res_html = await page.content()
            soup = BeautifulSoup(res_html, "lxml")
            err = soup.select_one("#painel-erros, ul.erros")
            if err:
                err_txt = clean_ws(err.get_text(" ", strip=True))
                return ResultadoTrocaPerfil(
                    sucesso=False,
                    modo_simulacao=False,
                    mensagem=f"O SIGAA recusou a gravação do perfil: {err_txt}",
                    origem_imagem=origem_label,
                    arquivo_validado=img_path.name,
                    cpf_detectado_automaticamente=cpf_filled,
                    data_nascimento_detectada_automaticamente=nasc_filled,
                    descricao_aplicada=descricao,
                )

            await _report(ctx, 4, 4, "Foto e perfil atualizados com sucesso!")
            return ResultadoTrocaPerfil(
                sucesso=True,
                modo_simulacao=False,
                mensagem="Foto e perfil atualizados com sucesso no SIGAA UFPA.",
                origem_imagem=origem_label,
                arquivo_validado=img_path.name,
                cpf_detectado_automaticamente=cpf_filled,
                data_nascimento_detectada_automaticamente=nasc_filled,
                descricao_aplicada=descricao,
            )
    finally:
        if is_temp:
            img_path.unlink(missing_ok=True)
