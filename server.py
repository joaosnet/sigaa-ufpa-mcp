import os
import logging
from typing import Any, Dict
from browser_use import Agent, Browser
from browser_use.llm.google import ChatGoogle
from fastmcp import FastMCP
from pydantic import Field
from dotenv import load_dotenv
import warnings
import asyncio

warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings(
    "ignore", message="websockets.server.WebSocketServerProtocol is deprecated"
)
load_dotenv()
# Inicializar FastMCP
mcp = FastMCP("SIGAA UFPA MCP Server")
BASE_URL = "https://sigaa.ufpa.br"
LOGIN_URL = f"{BASE_URL}/sigaa/verTelaLogin.do"
MOBILE_URL = f"{BASE_URL}/sigaa/mobile/touch/public/principal.jsf"

descricao = "Nome da tarefa a ser executada no sigaa"

descricao = (
    "Guia de Prompting para SIGAA:\n"
    "\n"
    "Dicas para criar prompts eficazes:\n"
    "\n"
    "1. Seja Específico (Recomendado):\n"
    "   ✅ Exemplo:\n"
    "   1. Acesse https://quotes.toscrape.com/\n"
    "   2. Use a ação extract_structured_data com a query 'primeiras 3 citações e autores'\n"
    "   3. Salve em quotes.csv usando write_file\n"
    "   4. Pesquise no Google a primeira citação e descubra quando foi escrita\n"
    "\n"
    "   ❌ Evite prompts abertos demais, como: 'Vá para a web e ganhe dinheiro'\n"
    "\n"
    "2. Nomeie Ações Diretamente:\n"
    "   - Referencie ações pelo nome quando souber o que precisa:\n"
    "   1. Use search para encontrar 'Python tutorials'\n"
    "   2. Use click_element_by_index para abrir o primeiro resultado\n"
    "   3. Use scroll para descer 2 páginas\n"
    "   4. Use extract_structured_data para extrair os 5 primeiros itens\n"
    "   5. Use send_keys com 'Tab Tab ArrowDown Enter'\n"
    "\n"
    "3. Resolva problemas de interação com navegação por teclado:\n"
    "   - Se não conseguir clicar em um botão, tente:\n"
    "     1. send_keys com 'Tab Tab Enter'\n"
    "     2. Ou 'ArrowDown ArrowDown Enter'\n"
    "\n"
    "4. Integre Ações Customizadas:\n"
    "   - Exemplo: get_2fa_code para autenticação em 2 fatores\n"
    "   - No prompt: 'Quando solicitado 2FA, use a ação get_2fa_code'\n"
    "\n"
    "5. Recuperação de Erros:\n"
    "   - Exemplo: Se a navegação falhar, use busca alternativa ou go_back\n"
    "\n"
    "Seja sempre claro e específico sobre as ações desejadas. Veja a documentação para a lista completa de ações disponíveis.\n"
)

llm = ChatGoogle(
                api_key=os.environ.get("GOOGLE_API_KEY"),
                model="gemini-flash-latest",
            )
browser = Browser(allowed_domains=[BASE_URL])

async def login_sigaa():
    global ok_login
    try:
        await browser.start()
        # login automático no SIGAA
        page = await browser.get_current_page()
        await page.goto(LOGIN_URL)
        # Esperando tempo indefinido para o carregamento da página
        await asyncio.sleep(15)
        elements = await page.get_elements_by_css_selector('#conteudo > div.logon > form > table > tbody > tr:nth-child(1) > td > input[type=text]')
        await elements[0].fill(os.environ.get("SIGAA_USERNAME"))
        elements = await page.get_elements_by_css_selector('#conteudo > div.logon > form > table > tbody > tr:nth-child(2) > td > input[type=password]')
        await elements[0].fill(os.environ.get("SIGAA_PASSWORD"))
        buttons = await page.get_elements_by_css_selector('#conteudo > div.logon > form > table > tfoot > tr > td > input[type=submit]')
        await buttons[0].click()
        ok_login = True
    except Exception:
        ok_login = False

@mcp.resource("resource://status-init")
def get_status_login():
    return {"logged_in": ok_login}

@mcp.tool()
async def pegar_conteudo_sigaa(
    prompt: str = Field(..., description=descricao),
) -> Dict[str, Any]:
    try:
        sensitive_data = {
            "x_user": os.environ.get("SIGAA_USERNAME"),
            "x_pass": os.environ.get("SIGAA_PASSWORD"),
        }
        
        # prompt += f"if need Log into {LOGIN_URL} with username x_user and password x_pass"
        result = await Agent(
            task=prompt,
            browser=browser,
            sensitive_data=sensitive_data,
            llm=llm,
        ).run()

        logging.info(f"Login attempt result: {result}")
        return result

    except Exception as e:
        logging.error(f"Erro no login SIGAA: {e}")
        return {"success": False, "error": str(e), "logged_in": False}


if __name__ == "__main__":
    try:
        # Padrão é 'stdio', a menos que MCP_TRANSPORT seja 'http'
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio")
        if transport_mode == "http":
            logging.info("Iniciando servidor MCP em modo HTTP...")
            mcp.run(transport="http", host="0.0.0.0", port=8000)
        elif transport_mode == "stdio":
            logging.info("Iniciando servidor MCP em modo stdio...")
            mcp.run(transport="stdio")
        else:
            logging.error(
                f"Modo de transporte desconhecido: {transport_mode}. Use 'stdio' ou 'http'."
            )
            # Inicia em stdio como fallback seguro para clientes MCP
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logging.info("Encerrando servidor...")
