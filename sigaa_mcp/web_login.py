"""Local HTTP visual login portal (/login, /login/vinculo, /logout, /health) for non-UI MCP clients."""

from __future__ import annotations

import html
import secrets
from urllib.parse import parse_qs

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from sigaa_mcp.auth import authenticate_with_credentials, logout_sigaa, select_vinculo
from sigaa_mcp.config import settings
from sigaa_mcp.schemas import EstadoSessao
from sigaa_mcp.session import session_manager

_CSRF_COOKIE = "sigaa_mcp_csrf"


def _esc(val: str) -> str:
    return html.escape(val or "", quote=True)


def _render_login_html(estado: EstadoSessao, csrf_token: str, flash_msg: str = "", is_error: bool = False) -> str:
    status_badge_cls = "badge-online" if estado.autenticado else "badge-offline"
    status_badge_txt = "SESSÃO ATIVA" if estado.autenticado else "DESCONECTADO"
    alert_msg = flash_msg or estado.mensagem
    alert_cls = "notice-error" if is_error else ("notice-ok" if estado.autenticado else "notice-neutral")

    active_panel = ""
    if estado.autenticado:
        active_panel = f"""
        <section class="session-panel" aria-label="Resumo da sessão ativa">
          <div class="section-head">
            <span class="eyebrow">VÍNCULO EM EXECUÇÃO</span>
            <span class="mono-tag">{_esc(estado.modo_persistencia.upper())}</span>
          </div>
          <dl class="meta-grid">
            <div><dt>Discente</dt><dd>{_esc(estado.nome_discente or estado.usuario)}</dd></div>
            <div><dt>Matrícula</dt><dd class="tabular">{_esc(estado.matricula_ativa or "—")}</dd></div>
            <div><dt>Curso</dt><dd>{_esc(estado.curso_ativo or "—")}</dd></div>
            <div><dt>Período</dt><dd class="tabular">{_esc(estado.semestre_atual or "—")}</dd></div>
          </dl>
          <form method="post" action="/logout" class="logout-form">
            <input type="hidden" name="csrf_token" value="{_esc(csrf_token)}">
            <button type="submit" class="btn btn-danger">Encerrar sessão e limpar RAM</button>
          </form>
        </section>
        """

    vinculos_panel = ""
    if estado.vinculos and (estado.aguardando_escolha_vinculo or len(estado.vinculos) > 1):
        items_html = []
        for v in estado.vinculos:
            items_html.append(
                f"""
                <li class="vinculo-row">
                  <div class="vinculo-meta">
                    <strong class="tabular">{_esc(v.matricula or v.identificador)}</strong>
                    <span>{_esc(v.curso)}</span>
                    <span class="mono-tag">{_esc(v.situacao)}</span>
                  </div>
                  <form method="post" action="/login/vinculo">
                    <input type="hidden" name="csrf_token" value="{_esc(csrf_token)}">
                    <input type="hidden" name="vinculo" value="{_esc(v.matricula or str(v.indice))}">
                    <button type="submit" class="btn btn-secondary">Selecionar</button>
                  </form>
                </li>
                """
            )
        vinculos_panel = f"""
        <section class="vinculos-panel" aria-label="Seleção de vínculo institucional">
          <h2 class="sub-heading">Vínculos institucionais encontrados</h2>
          <ul class="vinculo-list">{''.join(items_html)}</ul>
        </section>
        """

    checked_attr = "checked" if estado.tem_sessao_salva_disco else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Autenticação Local — SIGAA UFPA MCP</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg-canvas: #f6f7f8;
      --bg-surface: #ffffff;
      --bg-subtle: #eef0f3;
      --fg-primary: #111418;
      --fg-secondary: #4a5360;
      --fg-muted: #687385;
      --border-hairline: #d6dce3;
      --border-strong: #9aa5b4;
      --accent: #0b5cab;
      --accent-hover: #084785;
      --accent-fg: #ffffff;
      --ok-bg: #eaf6ee;
      --ok-fg: #135c2d;
      --ok-border: #9bd3ae;
      --err-bg: #fdf0ef;
      --err-fg: #9c1c1c;
      --err-border: #ebaba7;
      --danger-bg: #b42318;
      --danger-hover: #912018;
      --danger-fg: #ffffff;
      --radius: 8px;
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 24px;
      --space-6: 32px;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg-canvas: #0c0e12;
        --bg-surface: #13171e;
        --bg-subtle: #1a2029;
        --fg-primary: #f1f4f8;
        --fg-secondary: #b4becb;
        --fg-muted: #8793a4;
        --border-hairline: #27303d;
        --border-strong: #414f64;
        --accent: #3b9eff;
        --accent-hover: #62b1ff;
        --accent-fg: #061322;
        --ok-bg: #0f291a;
        --ok-fg: #7ee2a0;
        --ok-border: #1e5434;
        --err-bg: #2c1214;
        --err-fg: #fca5a5;
        --err-border: #692326;
        --danger-bg: #f87171;
        --danger-hover: #fca5a5;
        --danger-fg: #1f0505;
      }}
    }}

    @supports (color: light-dark(white, black)) {{
      :root {{
        --bg-canvas: light-dark(#f6f7f8, #0c0e12);
        --bg-surface: light-dark(#ffffff, #13171e);
        --bg-subtle: light-dark(#eef0f3, #1a2029);
        --fg-primary: light-dark(#111418, #f1f4f8);
        --fg-secondary: light-dark(#4a5360, #b4becb);
        --fg-muted: light-dark(#687385, #8793a4);
        --border-hairline: light-dark(#d6dce3, #27303d);
        --border-strong: light-dark(#9aa5b4, #414f64);
        --accent: light-dark(#0b5cab, #3b9eff);
        --accent-hover: light-dark(#084785, #62b1ff);
        --accent-fg: light-dark(#ffffff, #061322);
        --ok-bg: light-dark(#eaf7ef, #0f291a);
        --ok-fg: light-dark(#135e32, #7ee2a0);
        --ok-border: light-dark(#9cd8b4, #1e5434);
        --err-bg: light-dark(#fdf0ef, #2c1214);
        --err-fg: light-dark(#9c1c1c, #fca5a5);
        --err-border: light-dark(#ebaba7, #692326);
        --danger-bg: light-dark(#b42318, #f87171);
        --danger-hover: light-dark(#912018, #fca5a5);
        --danger-fg: light-dark(#ffffff, #1f0505);
      }}
    }}

    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100dvh;
      background: var(--bg-canvas);
      color: var(--fg-primary);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.5;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--space-4);
    }}

    .shell {{
      width: 100%;
      max-width: 520px;
      background: var(--bg-surface);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius);
      padding: var(--space-6);
    }}

    @media (max-width: 480px) {{
      .shell {{ padding: var(--space-4); }}
    }}

    header.top-bar {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--space-3);
      padding-bottom: var(--space-4);
      border-bottom: 1px solid var(--border-hairline);
      margin-bottom: var(--space-5);
    }}

    .brand-kicker {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      letter-spacing: 0.08em;
      color: var(--fg-muted);
      text-transform: uppercase;
      display: block;
      margin-bottom: var(--space-1);
    }}

    h1 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.25;
      letter-spacing: -0.015em;
      font-weight: 650;
    }}

    .subtitle {{
      margin: var(--space-2) 0 0;
      color: var(--fg-secondary);
      font-size: 13.5px;
    }}

    .badge {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.05em;
      padding: 4px 8px;
      border-radius: 4px;
      white-space: nowrap;
      border: 1px solid var(--border-hairline);
    }}

    .badge-online {{
      background: var(--ok-bg);
      color: var(--ok-fg);
      border-color: var(--ok-border);
    }}

    .badge-offline {{
      background: var(--bg-subtle);
      color: var(--fg-secondary);
    }}

    .notice {{
      padding: var(--space-3) var(--space-4);
      border-radius: var(--radius);
      font-size: 13.5px;
      margin-bottom: var(--space-5);
      border: 1px solid var(--border-hairline);
    }}
    .notice-neutral {{ background: var(--bg-subtle); color: var(--fg-secondary); }}
    .notice-ok {{ background: var(--ok-bg); color: var(--ok-fg); border-color: var(--ok-border); }}
    .notice-error {{ background: var(--err-bg); color: var(--err-fg); border-color: var(--err-border); }}

    .session-panel, .vinculos-panel {{
      background: var(--bg-subtle);
      border: 1px solid var(--border-hairline);
      border-radius: var(--radius);
      padding: var(--space-4);
      margin-bottom: var(--space-5);
    }}

    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-3);
    }}

    .eyebrow, .mono-tag {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      color: var(--fg-muted);
    }}

    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--space-3);
      margin: 0 0 var(--space-4);
    }}
    @media (max-width: 420px) {{
      .meta-grid {{ grid-template-columns: 1fr; }}
    }}
    .meta-grid dt {{ font-size: 12px; color: var(--fg-muted); }}
    .meta-grid dd {{ margin: 2px 0 0; font-weight: 600; font-size: 13.5px; overflow-wrap: anywhere; }}
    .tabular {{ font-variant-numeric: tabular-nums; }}

    .sub-heading {{
      margin: 0 0 var(--space-3);
      font-size: 14px;
      font-weight: 600;
    }}

    .vinculo-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: var(--space-2);
    }}

    .vinculo-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--space-3);
      padding: var(--space-2) var(--space-3);
      background: var(--bg-surface);
      border: 1px solid var(--border-hairline);
      border-radius: 6px;
    }}
    .vinculo-meta {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 13px;
    }}

    .field {{ margin-bottom: var(--space-4); }}
    label.field-label {{
      display: block;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--fg-primary);
    }}

    .input-wrap {{
      display: flex;
      gap: var(--space-2);
      align-items: stretch;
    }}

    input[type="text"], input[type="password"] {{
      width: 100%;
      min-height: 44px;
      padding: 10px 12px;
      font-size: 15px;
      color: var(--fg-primary);
      background: var(--bg-canvas);
      border: 1px solid var(--border-strong);
      border-radius: 6px;
      transition: border-color 140ms ease;
    }}
    input[type="text"]:focus-visible, input[type="password"]:focus-visible {{
      outline: 2px solid var(--accent);
      outline-offset: 1px;
      border-color: var(--accent);
    }}

    .checkbox-row {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin: var(--space-4) 0 var(--space-5);
      cursor: pointer;
      font-size: 13px;
      color: var(--fg-secondary);
      min-height: 44px;
    }}
    .checkbox-row input[type="checkbox"] {{
      width: 18px;
      height: 18px;
      margin-top: 2px;
      flex-shrink: 0;
      accent-color: var(--accent);
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 10px 16px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid transparent;
      cursor: pointer;
      transition: background-color 140ms ease, border-color 140ms ease;
    }}
    .btn-primary {{
      width: 100%;
      background: var(--accent);
      color: var(--accent-fg);
    }}
    .btn-primary:hover {{ background: var(--accent-hover); }}

    .btn-secondary {{
      background: var(--bg-subtle);
      color: var(--fg-primary);
      border-color: var(--border-strong);
      white-space: nowrap;
    }}
    .btn-danger {{
      width: 100%;
      background: var(--danger-bg);
      color: var(--danger-fg);
    }}
    .btn-danger:hover {{ background: var(--danger-hover); }}

    footer.foot-note {{
      margin-top: var(--space-5);
      padding-top: var(--space-4);
      border-top: 1px solid var(--border-hairline);
      font-size: 12px;
      color: var(--fg-muted);
      display: flex;
      justify-content: space-between;
      gap: var(--space-2);
      flex-wrap: wrap;
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="top-bar">
      <div>
        <span class="brand-kicker">SIGAA UFPA • SERVIDOR MCP LOCAL</span>
        <h1>Autenticação Direta</h1>
        <p class="subtitle">Suas credenciais permanecem na memória RAM deste servidor local e nunca passam pelo histórico do chat ou pelo LLM.</p>
      </div>
      <span class="badge {status_badge_cls}">{status_badge_txt}</span>
    </header>

    <div class="notice {alert_cls}" role="status">{_esc(alert_msg)}</div>

    {active_panel}
    {vinculos_panel}

    <form method="post" action="/login" aria-label="Formulário de acesso ao SIGAA UFPA">
      <input type="hidden" name="csrf_token" value="{_esc(csrf_token)}">

      <div class="field">
        <label class="field-label" for="username">Usuário do SIGAA</label>
        <input
          id="username"
          name="username"
          type="text"
          value="{_esc(estado.usuario)}"
          autocomplete="username"
          spellcheck="false"
          autocorrect="off"
          autocapitalize="off"
          required
          autofocus
          placeholder="Ex.: joao.silva"
        >
      </div>

      <div class="field">
        <label class="field-label" for="password">Senha institucional</label>
        <div class="input-wrap">
          <input
            id="password"
            name="password"
            type="password"
            autocomplete="current-password"
            required
            placeholder="••••••••••••"
          >
          <button
            type="button"
            id="toggle-pwd"
            class="btn btn-secondary"
            aria-controls="password"
            aria-pressed="false"
          >Mostrar</button>
        </div>
      </div>

      <div class="field">
        <label class="field-label" for="matricula">Matrícula específica (opcional)</label>
        <input
          id="matricula"
          name="matricula"
          type="text"
          value="{_esc(estado.matricula_ativa)}"
          spellcheck="false"
          autocorrect="off"
          autocapitalize="off"
          placeholder="Apenas se possuir múltiplos vínculos"
        >
      </div>

      <label class="checkbox-row" for="manter_sessao">
        <input id="manter_sessao" name="manter_sessao" type="checkbox" value="1" {checked_attr}>
        <span>Manter sessão ativa entre reinicializações (salva somente cookies locais; jamais grava sua senha em disco).</span>
      </label>

      <button type="submit" class="btn btn-primary">Entrar no SIGAA UFPA</button>
    </form>

    <footer class="foot-note">
      <span>Endpoint MCP: <code>/mcp</code></span>
      <span>Motor Playwright Determinístico • Zero Tokens Externos</span>
    </footer>
  </main>

  <script>
    (function () {{
      const btn = document.getElementById('toggle-pwd');
      const pwd = document.getElementById('password');
      if (!btn || !pwd) return;
      btn.addEventListener('click', function () {{
        const showing = pwd.type === 'text';
        pwd.type = showing ? 'password' : 'text';
        btn.setAttribute('aria-pressed', String(!showing));
        btn.textContent = showing ? 'Mostrar' : 'Ocultar';
      }});
    }})();
  </script>
</body>
</html>"""


async def _parse_form_urlencoded(request: Request) -> dict[str, str]:
    raw = (await request.body()).decode("utf-8", errors="replace")
    parsed = parse_qs(raw, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}


def _verify_csrf(request: Request, form_data: dict[str, str]) -> bool:
    cookie_tok = request.cookies.get(_CSRF_COOKIE, "")
    form_tok = form_data.get("csrf_token", "")
    return bool(cookie_tok and form_tok and secrets.compare_digest(cookie_tok, form_tok))


def register_web_routes(mcp: FastMCP) -> None:
    """Register /login, /login/vinculo, /logout, and /health on the FastMCP HTTP app."""

    @mcp.custom_route("/health", methods=["GET"])
    async def health_route(_request: Request) -> JSONResponse:
        estado = session_manager.get_estado_sessao()
        return JSONResponse(
            {
                "status": "ok",
                "server": "sigaa-ufpa-mcp",
                "authenticated": estado.autenticado,
                "matricula": estado.matricula_ativa,
                "headless": settings.chrome_headless,
            }
        )

    @mcp.custom_route("/login", methods=["GET", "POST"])
    async def login_route(request: Request) -> HTMLResponse:
        csrf_token = request.cookies.get(_CSRF_COOKIE) or secrets.token_urlsafe(32)
        flash_msg = ""
        is_error = False

        if request.method == "POST":
            form_data = await _parse_form_urlencoded(request)
            if not _verify_csrf(request, form_data):
                estado = session_manager.get_estado_sessao()
                html_doc = _render_login_html(
                    estado, csrf_token, "Token de segurança expirado. Tente enviar o formulário novamente.", True
                )
                resp = HTMLResponse(html_doc, status_code=403)
                resp.set_cookie(_CSRF_COOKIE, csrf_token, httponly=True, samesite="strict")
                return resp

            username = form_data.get("username", "").strip()
            password = form_data.get("password", "")
            matricula = form_data.get("matricula", "").strip()
            manter = form_data.get("manter_sessao") == "1"

            estado = await authenticate_with_credentials(
                username=username,
                password=password,
                manter_sessao=manter,
                matricula_preferida=matricula or None,
                allow_pause_for_visual_choice=True,
            )
            flash_msg = estado.mensagem
            is_error = not estado.autenticado and not estado.aguardando_escolha_vinculo
        else:
            estado = session_manager.get_estado_sessao()

        html_doc = _render_login_html(estado, csrf_token, flash_msg=flash_msg, is_error=is_error)
        resp = HTMLResponse(html_doc)
        resp.set_cookie(_CSRF_COOKIE, csrf_token, httponly=True, samesite="strict")
        return resp

    @mcp.custom_route("/login/vinculo", methods=["POST"])
    async def login_vinculo_route(request: Request) -> HTMLResponse:
        csrf_token = request.cookies.get(_CSRF_COOKIE) or secrets.token_urlsafe(32)
        form_data = await _parse_form_urlencoded(request)
        if not _verify_csrf(request, form_data):
            return HTMLResponse("CSRF inválido.", status_code=403)

        vinculo = form_data.get("vinculo", "").strip()
        estado = await select_vinculo(vinculo)
        html_doc = _render_login_html(
            estado, csrf_token, flash_msg=estado.mensagem, is_error=not estado.autenticado
        )
        resp = HTMLResponse(html_doc)
        resp.set_cookie(_CSRF_COOKIE, csrf_token, httponly=True, samesite="strict")
        return resp

    @mcp.custom_route("/logout", methods=["POST"])
    async def logout_route(request: Request) -> RedirectResponse | HTMLResponse:
        form_data = await _parse_form_urlencoded(request)
        if not _verify_csrf(request, form_data):
            return HTMLResponse("CSRF inválido.", status_code=403)
        await logout_sigaa()
        return RedirectResponse(url="/login", status_code=303)
