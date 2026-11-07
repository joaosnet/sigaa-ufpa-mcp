# Automa??o Web do SIGAA

> **Comunidade 6** ? 11 n?s ? Coes?o: 0.18 ? Fonte prim?ria: `server.py`

## Vis?o Geral
O SIGAA da UFPA ? constru?do sobre JavaServer Faces (JSF) com p?ginas din?micas, renderiza??o ass?ncrona parcial e tempos de resposta vari?veis. Esta comunidade re?ne os m?todos essenciais de intera??o de baixo n?vel do navegador.

---

## ?? Componentes Principais

### `esperar_elemento(page, selector, timeout=15.0, poll_interval=0.5)`
* **Fun??o:** Implementa espera ativa ass?ncrona (polling com retries) por seletores CSS espec?ficos.
* **Comportamento:**
  * Evita falhas intermitentes comuns causadas pelo carregamento lento do JSF.
  * Captura exce??es transientes de DOM e registra avisos caso o elemento n?o seja encontrado antes do esgotamento do tempo limite.
* **Seletores Cr?ticos Utilizados:**
  * Formul?rio de Login: `#conteudo > div.logon > form > table`
  * Campo Usu?rio: `input[type=text]`
  * Campo Senha: `input[type=password]`
  * Bot?o Entrar: `input[type=submit]`
  * Menus do Discente: `.menus` e `.perfil`

### `perform_login_discente(page)`
* **Fun??o:** Realiza o preenchimento autom?tico das credenciais do usu?rio lidas a partir de `SIGAA_USERNAME` e `SIGAA_PASSWORD`.
* **Garantia de Estado:** Ap?s o clique de submiss?o, aguarda explicitamente o carregamento e clica no elemento `.menus` para assegurar que a sess?o do discente est? ativa antes de devolver o controle.

### `esperar_extracao_dados(page, prompt, model, llm, timeout=15.0)`
* **Fun??o:** Invoca a extra??o sem?ntica estruturada usando Pydantic e o modelo Gemini (`gemini-flash-latest`) diretamente sobre o DOM da p?gina.

### `login_sigaa(browser_session)`
* **Fun??o:** Wrapper ass?ncrono decorado com `@tools.action` registrado como ferramenta utiliz?vel internamente pelos agentes aut?nomos `browser_use.Agent`.

---

## ?? Armadilhas e Resili?ncia
1. **Sess?es Simult?neas:** O SIGAA invalida logins caso m?ltiplos acessos ocorram com o mesmo discente em n?s distintos. O cont?iner opera com sess?o de navegador isolada com `keep_alive=(transport_mode == "http")`.
2. **Seletores JSF com IDs Din?micos:** IDs gerados pelo JSF como `#j_id_jsp_...` sofrem escape de dois-pontos nos seletores CSS (`\#`).
