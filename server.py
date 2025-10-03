import os
import sys
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

# Configuração global de logging para stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Função para configurar todos os loggers para usar stderr
def configure_all_loggers():
    """
    Configura todos os loggers registrados no sistema para usar stderr e nível INFO
    """
    # Configura o root logger
    global logger
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.addHandler(logging.StreamHandler(sys.stderr))
    logger.setLevel(logging.INFO)

    # Itera sobre todos os loggers registrados
    for logger_name, logger_instance in logging.Logger.manager.loggerDict.items():
        if isinstance(logger_instance, logging.Logger):
            logger_instance.handlers.clear()
            logger_instance.addHandler(logging.StreamHandler(sys.stderr))
            logger_instance.setLevel(logging.INFO)
            logger_instance.propagate = False  # Evita duplicação de logs

# Executa a configuração
configure_all_loggers()

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
    logger.warning(f"Elemento '{selector}' não encontrado após {timeout}s.")
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
        logger.info("Login SIGAA realizado com sucesso.")
    except Exception as e:
        startup_status["success"] = False
        startup_status["message"] = f"Erro no login SIGAA: {e}"
        startup_status["logged_in"] = False
        logger.error(f"Erro no login SIGAA: {e}")


# Lifespan async para FastMCP
@asynccontextmanager
async def lifespan_manager(app):
    logger.info("🚀 Iniciando servidor MCP...")
    try:
        await login_sigaa()
        logger.info("✅ Função de startup (login_sigaa) executada com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
    yield
    logger.info("🔄 Desligando servidor...")


# Inicializar FastMCP com lifespan
mcp = FastMCP(
    name="SIGAA UFPA MCP Server",
    lifespan=lifespan_manager,
)


@mcp.resource("resource://status-init")
def get_status_login():
    return {
        "startup_success": startup_status["success"],
        "message": startup_status["message"],
        "logged_in": startup_status["logged_in"],
    }


# Ferramenta 0: Reiniciar sessão do navegador e relogar
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
        logger.error(f"Erro ao reiniciar sessão: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 1: Baixar histórico escolar em PDF
@mcp.tool()
async def baixar_historico_escolar() -> Dict[str, Any]:
    """
    Baixa o histórico escolar completo do aluno em PDF e retorna o caminho do arquivo salvo.
    """

    prompt = """
    1. Se aparecer Selecione o Ano-Período mais atual
    2. Se aparecer Selecione o Portal do Discente
    3. Clique em Ensino
    4. Clique em Emitir Histórico
    5. O Histórico será salvo automaticamente no navegador
    Obs.: Durante o período de processamento de matricula não é possível emitir histórico"""

    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logger.error(f"Erro ao baixar histórico escolar: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 2: Listar disciplinas ofertadas no semestre atual
@mcp.tool()
async def listar_disciplinas_ofertadas(
    curso: str = Field(..., description="Nome do curso (ex: Engenharia de Computação)"),
    turno: str = Field("", description="Turno (ex: Matutino, Noturno, opcional)"),
) -> Dict[str, Any]:
    """
    Lista todas as disciplinas ofertadas no semestre atual para o curso e turno informados.
    """
    prompt = f""" Para o curso de {curso} e turno {turno}, liste todas as disciplinas ofertadas no semestre atual.
    # Como entrar no SIGAA UFPA e Listar disciplinas ofertas do semestre
## **1. Acessando o Portal do Discente**

### **Passo 1: Selecionar Período Letivo**
- Após o login, **selecione o Ano-Período mais atual** (exemplo: 2025.2)
- Esta informação aparecerá logo após o login ou poderá ser alterada no menu principal

### **Passo 2: Acessar Portal do Discente**
- Na tela principal, clique em **"Portal do Discente"**
- Esta opção dará acesso a todas as funcionalidades acadêmicas do estudante

## **2. Consultando Disciplinas Ofertas**

### **Método 1: Através do Menu Ensino**

#### **Passo 1: Acessar Menu Ensino**
- No Portal do Discente, clique na aba **"Ensino"**

#### **Passo 2: Acessar Consultas Gerais**
- Dentro do menu Ensino, clique em **"Consultas Gerais"**
- No Consultas Gerais você encontrará:
  - Consultar Curso
  - Consultar Componente Curricular
  - Consultar Estrutura Curricular
  - Consultar Turma
  - Consultar Unidades Academicas
#### **Passo 3: Consultar Turma**
- Clique em **"Consultar Turma"**
- Na página de Consulta de Turmas, utilize os filtros para buscar por:
  - **Ofertadas ao curso:**: Selecione o curso desejado (ex: ENGENHARIA DA COMPUTACAO/ITEC - BELÉM)
  - **Ano-Período:**: Selecione a caixa para o semestre atual
  - **Unidade:**: Selecione a unidade acadêmica correspondente ao curso
  - **Nome do componente:**: Deixe em branco para listar todas as disciplinas


### **Método 2: Consulta Pública de Turmas**

#### **Passo Alternativo: Consultar Turmas do Semestre**
- Acesse diretamente: https://sigaa.ufpa.br/sigaa/public/turmas/listar.jsf?aba=p-ensino
- Esta página permite consultar **todas as turmas oferecidas pela instituição**
- Utilize os filtros disponíveis para buscar por:
  - **Curso específico**
  - **Turno** (matutino, vespertino, noturno)
  - **Período/semestre**
  - **Instituto/Faculdade**

### **Método 3: Consulta de Componentes Curriculares**
- Acesse: https://sigaa.ufpa.br/sigaa/public/componentes/busca_componentes.jsf?aba=p-ensino
- Esta página permite consultar **todos os componentes curriculares (disciplinas)** oferecidos
- Filtre por curso, instituto ou nome da disciplina
- Visualize detalhes e programas atuais das disciplinas
    """

    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logger.error(f"Erro ao listar disciplinas ofertadas: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 3: Exportar horários de aula do aluno em CSV
@mcp.tool()
async def exportar_horarios_csv() -> Dict[str, Any]:
    """
    Exporta todos os horários de aula do aluno no semestre atual em formato CSV.
    """
    prompt = """
    Obs.: Os horários de aula podem ser encontrados na seção de "Turmas do Semestre" e no Atestado de Matrícula.
    1. Se aparecer Selecione o Ano-Período mais atual
    2. Se aparecer Selecione o Portal do Discente
    3. Se necessário, clique em Ensino
    4. Se necessário, clique em Emitir Atestado de Matrícula(Note que quando o atestado é emitido, é aberta outra aba no navegador)
    """

    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logger.error(f"Erro ao exportar horários: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 4: Listar avisos/comunicados recentes das turmas do aluno
@mcp.tool()
async def listar_avisos_turmas() -> Dict[str, Any]:
    """
    Lista todos os avisos/comunicados recentes das turmas em que o aluno está matriculado.
    """
    prompt = """
    Obs.: Os horários de aula podem ser encontrados na seção de "Turmas do Semestre" e no Atestado de Matrícula.
    1. Se aparecer Selecione o Ano-Período mais atual
    2. Se aparecer Selecione o Portal do Discente
    E em Turmas do Semestre em cada turma nessa sessão:
    1. Clique na turma
    2. Clique em Notícias
    3. Extraia todos os avisos/comunicados recentes
    4. Repita para todas as turmas
    """
    try:
        result = await Agent(
            task=prompt,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
        ).run()
        return result
    except Exception as e:
        logger.error(f"Erro ao listar avisos das turmas: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    try:
        logger.info(os.environ)
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio")
        if transport_mode == "http":
            logger.info("Iniciando servidor MCP em modo HTTP...")
            mcp.run(transport="http", host="0.0.0.0", port=8000)
        elif transport_mode == "stdio":
            logger.info("Iniciando servidor MCP em modo stdio...")
            mcp.run(transport="stdio")
        else:
            logger.error(
                f"Modo de transporte desconhecido: {transport_mode}. Use 'stdio' ou 'http'."
            )
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Encerrando servidor...")
