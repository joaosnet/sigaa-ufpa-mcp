"""HTTP route tests for /health, /login, CSRF protection, and /logout."""

from __future__ import annotations

import re
import httpx
import pytest

from server import mcp
from sigaa_mcp.schemas import EstadoSessao
import sigaa_mcp.web_login as web_login_mod


@pytest.mark.asyncio
async def test_health_and_login_portal_modern_web_compliance() -> None:
    app = mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8003") as client:
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        resp = await client.get("/login")
        assert resp.status_code == 200
        body = resp.text

        # Modern web guidance checks: dark-mode + autofill-sign-in-form
        assert '<meta name="color-scheme" content="light dark">' in body
        assert 'autocomplete="username"' in body
        assert 'spellcheck="false"' in body
        assert 'type="password"' in body
        assert 'autocomplete="current-password"' in body
        assert 'id="toggle-pwd"' in body

        # Submitting POST without CSRF token must return 403
        bad_post = await client.post(
            "/login",
            content="username=teste&password=123",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert bad_post.status_code == 403


@pytest.mark.asyncio
async def test_login_and_logout_post_with_csrf(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_auth(username: str, password: str, manter_sessao: bool = False, **kwargs):
        return EstadoSessao(
            autenticado=True,
            usuario=username,
            nome_discente="DISCENTE TESTE",
            matricula_ativa="202006840099",
            curso_ativo="ENGENHARIA DA COMPUTAÇÃO",
            semestre_atual="2026.4",
            mensagem="Login simulado com sucesso.",
        )

    async def fake_logout():
        return EstadoSessao(autenticado=False, mensagem="Logout simulado.")

    monkeypatch.setattr(web_login_mod, "authenticate_with_credentials", fake_auth)
    monkeypatch.setattr(web_login_mod, "logout_sigaa", fake_logout)

    app = mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8003") as client:
        get_resp = await client.get("/login")
        m_csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.text)
        assert m_csrf is not None
        csrf_token = m_csrf.group(1)

        post_resp = await client.post(
            "/login",
            data={
                "csrf_token": csrf_token,
                "username": "aluno.ufpa",
                "password": "segredo_nao_logado",
                "manter_sessao": "1",
            },
        )
        assert post_resp.status_code == 200
        assert "DISCENTE TESTE" in post_resp.text
        assert "SESSÃO ATIVA" in post_resp.text
        assert "segredo_nao_logado" not in post_resp.text

        logout_resp = await client.post("/logout", data={"csrf_token": csrf_token})
        assert logout_resp.status_code == 303
