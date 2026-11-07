"""Integration tests for FastMCP 4.1 tools, Apps, Prompts, Resources, and Visual Login security."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from server import cache_store, invalidate_response_cache, mcp
from sigaa_mcp.config import settings
from sigaa_mcp.session import session_manager


@pytest.mark.asyncio
async def test_mcp_surface_and_zero_password_exposure() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = {t.name for t in tools}

        expected = {
            "baixar_historico_escolar",
            "emitir_atestado_matricula",
            "consultar_notas_frequencia",
            "listar_atividades_pendentes",
            "exportar_horarios_csv",
            "listar_avisos_turmas",
            "listar_disciplinas_ofertadas",
            "trocar_imagem_perfil",
            "reiniciar_sessao",
            "encerrar_sessao",
            "abrir_login_sigaa",
            "abrir_painel_academico",
            "abrir_explorador_turmas",
            "abrir_estudio_perfil",
        }
        assert expected.issubset(tool_names)
        assert "autenticar_credenciais_ui" not in tool_names

        # Security bar: zero password fields exposed in any model-visible tool schema
        for tool in tools:
            schema_dump = json.dumps(tool.input_schema).lower()
            assert "senha" not in schema_dump, f"Tool {tool.name} leaked 'senha' to LLM!"
            assert "password" not in schema_dump, f"Tool {tool.name} leaked 'password' to LLM!"

        prompts = await client.list_prompts()
        assert {p.name for p in prompts} == {
            "planejar_matricula_semestre",
            "briefing_semana_academica",
            "auditar_integralizacao_curricular",
        }

        prompt_res = await client.get_prompt(
            "planejar_matricula_semestre",
            {"curso": "Engenharia da Computação", "turno_preferido": "M"},
        )
        assert "Engenharia da Computação" in str(prompt_res)


@pytest.mark.asyncio
async def test_resources_and_path_traversal_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "download_dir", tmp_path)
    sample_csv = tmp_path / "horarios_teste.csv"
    sample_csv.write_text("Semestre,Disciplina\n2026.4,SINAIS E SISTEMAS\n", encoding="utf-8")

    async with Client(mcp) as client:
        st = await client.read_resource("resource://status-init")
        st_data = json.loads(st[0].text)
        assert st_data["motor"] == "playwright-deterministico-zero-token"

        dl_list = await client.read_resource("resource://downloads")
        dl_data = json.loads(dl_list[0].text)
        assert dl_data["total_arquivos"] == 1
        assert dl_data["arquivos"][0]["filename"] == "horarios_teste.csv"

        dl_item = await client.read_resource("resource://downloads/horarios_teste.csv")
        item_data = json.loads(dl_item[0].text)
        assert "SINAIS E SISTEMAS" in item_data["content"]

        with pytest.raises(Exception):
            await client.read_resource("resource://downloads/..%2Fpyproject.toml")


@pytest.mark.asyncio
async def test_visual_login_auto_card_when_logged_out(monkeypatch: pytest.MonkeyPatch) -> None:
    saved_user = session_manager.username
    saved_pwd = session_manager.get_password_for_form()
    saved_auth = session_manager.authenticated
    try:
        session_manager.clear_ram_credentials(keep_env_fallback=False)
        session_manager.authenticated = False
        await invalidate_response_cache()

        async with Client(mcp) as client:
            # 1. Direct visual login app call
            login_res = await client.call_tool("abrir_login_sigaa", {})
            text_json = json.loads(login_res.content[0].text)
            assert text_json["autenticado"] is False
            assert "/login" in text_json["login_url"]
            sc_dump = json.dumps(login_res.structured_content)
            assert '"$prefab"' in sc_dump
            assert '"inputType": "password"' in sc_dump
            assert '"value": "{{ manter_sessao }}"' not in sc_dump

            # 2. Calling a protected academic tool while logged out returns the visual login card gracefully
            notas_res = await client.call_tool("consultar_notas_frequencia", {})
            notas_json = json.loads(notas_res.content[0].text)
            assert notas_json["autenticado"] is False
            assert '"inputType": "password"' in json.dumps(notas_res.structured_content)
    finally:
        session_manager.set_ram_credentials(saved_user, saved_pwd)
        session_manager.authenticated = saved_auth
        await invalidate_response_cache()


@pytest.mark.asyncio
async def test_cache_invalidation_on_session_change() -> None:
    await cache_store.put("dummy_key", {"cached": True}, collection="test_col")
    assert await cache_store.get("dummy_key", collection="test_col") == {"cached": True}
    await session_manager.notify_session_changed()
    assert await cache_store.get("dummy_key", collection="test_col") is None
