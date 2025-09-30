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
from contextlib import asynccontextmanager

warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings(
    "ignore", message="websockets.server.WebSocketServerProtocol is deprecated"
)

load_dotenv()

# Variável global para armazenar o status do login/startup
startup_status = {"success": False, "message": "", "logged_in": False}

BASE_URL = "https://sigaa.ufpa.br"

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
browser = Browser(
    allowed_domains=[BASE_URL],
    keep_alive=True,
)


async def esperar_elemento(
    page, selector: str, timeout: float = 15.0, poll_interval: float = 0.5
):
    """
    Espera até que um elemento esteja presente na página.
    :param page: instância da página (browser_use.Page)
    :param selector: seletor CSS do elemento a esperar
    :param timeout: tempo máximo de espera em segundos
    :param poll_interval: intervalo entre tentativas em segundos
    :return: elemento encontrado ou None se não encontrado
    """
    import time

    start = time.time()
    while time.time() - start < timeout:
        try:
            elements = await page.get_elements_by_css_selector(selector)
            if elements:
                return elements[0]
        except Exception:
            # Pode ser que o DOM ainda não esteja pronto
            pass
        await asyncio.sleep(poll_interval)
    logging.warning(f"Elemento '{selector}' não encontrado após {timeout}s.")
    return None


# Função de login adaptada para uso no lifespan
async def login_sigaa():
    try:
        await browser.start()
        page = await browser.get_current_page()
        await page.goto(BASE_URL)

        # Espera dinâmica pelo campo de usuário
        campo_usuario = await esperar_elemento(
            page,
            "#conteudo > div.logon > form > table > tbody > tr:nth-child(1) > td > input[type=text]",
            timeout=20.0,
            poll_interval=0.5,
        )
        if not campo_usuario:
            raise Exception("Campo de usuário não encontrado na tela de login.")
        await campo_usuario.fill(os.environ.get("SIGAA_USERNAME"))

        # Espera dinâmica pelo campo de senha
        campo_senha = await esperar_elemento(
            page,
            "#conteudo > div.logon > form > table > tbody > tr:nth-child(2) > td > input[type=password]",
            timeout=10.0,
            poll_interval=0.5,
        )
        if not campo_senha:
            raise Exception("Campo de senha não encontrado na tela de login.")
        await campo_senha.fill(os.environ.get("SIGAA_PASSWORD"))

        # Espera dinâmica pelo botão de submit
        botao_submit = await esperar_elemento(
            page,
            "#conteudo > div.logon > form > table > tfoot > tr > td > input[type=submit]",
            timeout=10.0,
            poll_interval=0.5,
        )
        if not botao_submit:
            raise Exception("Botão de login não encontrado na tela de login.")
        await botao_submit.click()

        startup_status["success"] = True
        startup_status["message"] = "Login realizado com sucesso"
        startup_status["logged_in"] = True
        logging.info("Login SIGAA realizado com sucesso.")
    except Exception as e:
        startup_status["success"] = False
        startup_status["message"] = f"Erro no login SIGAA: {e}"
        startup_status["logged_in"] = False
        logging.error(f"Erro no login SIGAA: {e}")


# Lifespan async para FastMCP
@asynccontextmanager
async def lifespan_manager(app):
    logging.info("🚀 Iniciando servidor MCP...")
    try:
        await login_sigaa()
        logging.info("✅ Função de startup (login_sigaa) executada com sucesso")
    except Exception as e:
        logging.error(f"❌ Erro na inicialização: {e}")
    yield
    logging.info("🔄 Desligando servidor...")


# Inicializar FastMCP com lifespan
mcp = FastMCP(name="SIGAA UFPA MCP Server", lifespan=lifespan_manager)


@mcp.resource("resource://status-init")
def get_status_login():
    return {
        "startup_success": startup_status["success"],
        "message": startup_status["message"],
        "logged_in": startup_status["logged_in"],
    }


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
        logging.info(os.environ)
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
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logging.info("Encerrando servidor...")
