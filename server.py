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


llm = ChatGoogle(
    api_key=os.environ.get("GOOGLE_API_KEY"),
    model="gemini-flash-latest",
)
browser = Browser(
    allowed_domains=[BASE_URL],
    keep_alive=True,
)
# sensitive_data = {
#     "x_user": os.environ.get("SIGAA_USERNAME"),
#     "x_pass": os.environ.get("SIGAA_PASSWORD"),
# }

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

#Ferramenta 0: Reiniciar sessão do navegador e relogar
@mcp.tool()
async def reiniciar_sessao() -> Dict[str, Any]:
    """
    Reinicia a sessão do navegador e realiza o login novamente.
    """
    global startup_status
    try:
        await browser.stop()
        await login_sigaa()
        return {
            "success": startup_status["success"],
            "message": startup_status["message"],
            "logged_in": startup_status["logged_in"],
        }
    except Exception as e:
        logging.error(f"Erro ao reiniciar sessão: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 1: Baixar histórico escolar em PDF
@mcp.tool()
async def baixar_historico_escolar() -> Dict[str, Any]:
    """
    Baixa o histórico escolar completo do aluno em PDF e retorna o caminho do arquivo salvo.
    """
    prompt = (
        "1. Acesse o SIGAA e navegue até a área do discente.\n"
        "2. Localize e acesse a opção 'Histórico Escolar'.\n"
        "3. Clique na opção para gerar/baixar o histórico em PDF.\n"
        "4. Salve o arquivo como 'historico_escolar.pdf' usando write_file action.\n"
        "5. Retorne o caminho do arquivo salvo."
    )

    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logging.error(f"Erro ao baixar histórico escolar: {e}")
        return {"success": False, "error": str(e)}

# Ferramenta 2: Listar disciplinas ofertadas no semestre atual
@mcp.tool()
async def listar_disciplinas_ofertadas(
    curso: str = Field(..., description="Nome do curso (ex: Engenharia de Computação)"),
    turno: str = Field("", description="Turno (ex: Matutino, Noturno, opcional)")
) -> Dict[str, Any]:
    """
    Lista todas as disciplinas ofertadas no semestre atual para o curso e turno informados.
    """
    prompt = (
        f"1. Acesse o SIGAA e navegue até a área de consulta de disciplinas ofertadas.\n"
        f"2. Filtre pelo curso '{curso}'"
        + (f" e turno '{turno}'" if turno else "")
        + ".\n3. Extraia nome, código, professor e horários de todas as disciplinas ofertadas neste semestre.\n"
        "4. Retorne os dados em formato de lista de dicionários."
    )
    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logging.error(f"Erro ao listar disciplinas ofertadas: {e}")
        return {"success": False, "error": str(e)}

# Ferramenta 3: Exportar horários de aula do aluno em CSV
@mcp.tool()
async def exportar_horarios_csv() -> Dict[str, Any]:
    """
    Exporta todos os horários de aula do aluno no semestre atual em formato CSV.
    """
    prompt = (
        "1. Acesse o SIGAA e navegue até a área de horários do discente.\n"
        "2. Extraia todas as disciplinas matriculadas, dias da semana, horários e salas.\n"
        "3. Salve os dados em 'horarios_aula.csv' usando write_file action.\n"
        "4. Retorne o caminho do arquivo salvo."
    )
    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logging.error(f"Erro ao exportar horários: {e}")
        return {"success": False, "error": str(e)}

# Ferramenta 4: Listar avisos/comunicados recentes das turmas do aluno
@mcp.tool()
async def listar_avisos_turmas() -> Dict[str, Any]:
    """
    Lista todos os avisos/comunicados recentes das turmas em que o aluno está matriculado.
    """
    prompt = (
        "1. Acesse o SIGAA e navegue até a área de turmas/disciplina do discente.\n"
        "2. Para cada turma, acesse a seção de avisos/comunicados.\n"
        "3. Extraia os avisos/comunicados publicados nos últimos 30 dias, incluindo título, data, disciplina e conteúdo.\n"
        "4. Retorne os dados em formato de lista de dicionários."
    )
    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logging.error(f"Erro ao listar avisos das turmas: {e}")
        return {"success": False, "error": str(e)}


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
