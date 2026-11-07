"""PerfilDiscenteApp — Interactive Student Profile & Photo Studio."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCPApp
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from prefab_ui.actions import SetState, ShowToast
from prefab_ui.actions.mcp import CallTool
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    ERROR,
    RESULT,
    STATE,
    Alert,
    AlertDescription,
    Badge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    Checkbox,
    Column,
    Grid,
    If,
    Input,
    Metric,
    Row,
    Textarea,
)

from sigaa_mcp.apps.auth_app import build_login_required_tool_result
from sigaa_mcp.drive_service import GoogleDriveService, is_drive_configured
from sigaa_mcp.flows.academico import obter_resumo_portal_flow
from sigaa_mcp.flows.perfil import trocar_imagem_perfil_flow
from sigaa_mcp.session import AuthenticationRequiredError
from sigaa_mcp.ui_components import build_dual_tool_result

PERFIL_APP_NAME = "sigaa-perfil"
perfil_app = FastMCPApp(PERFIL_APP_NAME)


@perfil_app.tool(
    name="atualizar_perfil_ui",
    description="Callback da UI para simular (dry_run) ou gravar nova foto/descrição de perfil no SIGAA.",
    model=False,
    timeout=75.0,
)
async def atualizar_perfil_ui(
    caminho_ou_url: str = "",
    drive_file_id: str = "",
    descricao: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    res = await trocar_imagem_perfil_flow(
        drive_file_id=drive_file_id or None,
        caminho_ou_url=caminho_ou_url or None,
        descricao=descricao if descricao.strip() else None,
        dry_run=dry_run,
    )
    return res.model_dump(mode="json")


@perfil_app.ui(
    name="abrir_estudio_perfil",
    title="Estúdio de Perfil Discente SIGAA",
    description=(
        "Abre o Estúdio Interativo de Perfil do SIGAA UFPA para validar, simular (dry_run) ou aplicar "
        "nova foto (arquivo local, URL HTTPS ou Google Drive ID) e descrição pessoal."
    ),
    tags={"perfil", "app"},
    annotations=ToolAnnotations(
        title="Estúdio de Perfil Discente SIGAA",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    timeout=60.0,
)
async def abrir_estudio_perfil(ctx: Context = CurrentContext()) -> ToolResult:
    try:
        perfil, _, _, _ = await obter_resumo_portal_flow(ctx=ctx)
    except AuthenticationRequiredError as exc:
        return build_login_required_tool_result(str(exc))

    drive_imagens: list[dict[str, str]] = []
    if is_drive_configured():
        try:
            svc = GoogleDriveService()
            drive_imagens = [
                {"id": str(arq.get("id", "")), "name": str(arq.get("name", ""))}
                for arq in svc.listar_arquivos_na_pasta()
                if str(arq.get("mimeType", "")).startswith("image/")
            ]
        except Exception:
            drive_imagens = []

    state = {
        "caminho_ou_url": "",
        "drive_file_id": "",
        "descricao": perfil.descricao_pessoal or "",
        "dry_run": True,
        "feedback_msg": "",
    }

    with Column(gap=4) as view:
        with Card():
            with CardHeader():
                with Row(gap=2):
                    CardTitle("Estúdio de Foto e Perfil — SIGAA UFPA")
                    Badge(label=perfil.matricula or "Discente", variant="outline")
                CardDescription(
                    "Valide dimensões/formato e simule o preenchimento automático de CPF/Data de Nascimento em RAM antes de gravar."
                )
            with CardContent():
                with Column(gap=3):
                    with Grid(columns=2, gap=3):
                        Metric(label="Discente", value=perfil.nome or "-")
                        Metric(label="E-mail Cadastrado", value=perfil.email or "-")

                    if drive_imagens:
                        with Row(gap=2):
                            for img in drive_imagens[:6]:
                                Button(
                                    label=f"Drive: {img['name'][:24]}",
                                    variant="outline",
                                    size="sm",
                                    on_click=SetState(key="drive_file_id", value=img["id"]),
                                )

                    Input(
                        name="caminho_ou_url",
                        value=STATE.caminho_ou_url,
                        placeholder="Caminho local da imagem (ex.: ./foto.png) ou URL https://...",
                    )
                    Input(
                        name="drive_file_id",
                        value=STATE.drive_file_id,
                        placeholder="Ou ID do arquivo no Google Drive (opcional)",
                    )
                    Textarea(
                        name="descricao",
                        value=STATE.descricao,
                        placeholder="Descrição pessoal / áreas de interesse acadêmico (opcional)",
                    )
                    Checkbox(
                        name="dry_run",
                        value=True,
                        label="Modo Simulação Segura (dry_run=True — valida tudo sem clicar em 'Gravar perfil')",
                    )

                    with If(STATE.feedback_msg):
                        with Alert(variant="info"):
                            AlertDescription(STATE.feedback_msg)

            with CardFooter():
                Button(
                    label="Executar Validação / Atualização de Perfil",
                    variant="default",
                    on_click=CallTool(
                        tool=atualizar_perfil_ui,
                        arguments={
                            "caminho_ou_url": STATE.caminho_ou_url,
                            "drive_file_id": STATE.drive_file_id,
                            "descricao": STATE.descricao,
                            "dry_run": STATE.dry_run,
                        },
                        on_success=[
                            SetState(key="feedback_msg", value=RESULT.mensagem),
                            ShowToast(message=RESULT.mensagem, variant="success"),
                        ],
                        on_error=ShowToast(message=ERROR, variant="error"),
                    ),
                )

    prefab = PrefabApp(title="Estúdio de Perfil SIGAA", state=state, view=view)
    return build_dual_tool_result(perfil, prefab, fastmcp_app_name=PERFIL_APP_NAME)
