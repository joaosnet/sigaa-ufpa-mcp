import os
from typing import Any, Dict
from browser_use import Agent, Browser, BrowserSession, Tools

from browser_use.llm.google import ChatGoogle
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from browser_use.actor.page import Page
from dotenv import load_dotenv
import warnings
import asyncio
from contextlib import asynccontextmanager
import drive_service
import tempfile
import base64
from loguru import logger
import logging

# Interceptar logs do logging padrão para passar pelo loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())

# Limpar handlers padrão e adicionar o intercept
logging.getLogger().handlers.clear()
logging.getLogger().addHandler(InterceptHandler())

warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings(
    "ignore", message="websockets.server.WebSocketServerProtocol is deprecated"
)

load_dotenv()

# Variável global para armazenar o status do login/startup
startup_status = {"success": False, "message": "", "logged_in": False}

BASE_URL = "https://sigaa.ufpa.br"

transport_mode = os.getenv("MCP_TRANSPORT", "stdio")

llm = ChatGoogle(
    api_key=os.environ.get("GOOGLE_API_KEY"),
    model="gemini-flash-latest",
)


browser = Browser(
    allowed_domains=[BASE_URL],
    # se for modo http, usar keep_alive=True para manter a sessão
    keep_alive=(transport_mode == "http"),
    highlight_elements=True,
)

tools = Tools()

# sensitive_data = {
#     "x_user": os.environ.get("SIGAA_USERNAME"),
#     "x_pass": os.environ.get("SIGAA_PASSWORD"),
# }


async def esperar_elemento(
    page: Page, selector: str, timeout: float = 15.0, poll_interval: float = 0.5
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


async def esperar_extracao_dados(
    page: Page,
    prompt: str,
    model: BaseModel,
    llm,
    timeout: float = 15.0,
    poll_interval: float = 0.5,
):
    """
    Espera até que os dados sejam extraídos corretamente da página.
    :param page: instância da página (browser_use.Page)
    :param prompt: prompt para extração
    :param model: modelo Pydantic para os dados
    :param llm: instância do LLM
    :param timeout: tempo máximo de espera em segundos
    :param poll_interval: intervalo entre tentativas em segundos
    :return: objeto extraído ou None se não conseguir
    """
    import time

    start = time.time()
    while time.time() - start < timeout:
        try:
            data = await page.extract_content(prompt, llm=llm)
            print(data)
            return data
        except Exception:
            # Pode ser que os dados ainda não estejam prontos
            pass
        await asyncio.sleep(poll_interval)
    logger.warning(f"Dados não extraídos após {timeout}s.")
    return None


# Função auxiliar para realizar o login em uma página
async def perform_login_discente(page):
    """
    Realiza o login no SIGAA UFPA na página fornecida.
    """
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
    botao = await esperar_elemento(
        page,
        "#conteudo > div.logon > form > table > tfoot > tr > td > input[type=submit]",
        timeout=10.0,
        poll_interval=0.5,
    )
    if not botao:
        raise Exception("Botão de login não encontrado na tela de login.")
    await botao.click()
    # Clicando em Menu do Discente
    botao = await esperar_elemento(page, ".menus")
    await botao.click()


async def full_login_procedure_discente():
    global startup_status
    try:
        await browser.start()
        page = await browser.get_current_page()
        await page.goto(BASE_URL)
        await perform_login_discente(page)
        startup_status["success"] = True
        startup_status["message"] = "Login realizado com sucesso"
        startup_status["logged_in"] = True
        logger.info("✅ Login SIGAA realizado com sucesso")
    except Exception as e:
        logger.error(f"Erro no login SIGAA: {e}")
        startup_status["success"] = False
        startup_status["message"] = f"Erro no login SIGAA: {e}"
        startup_status["logged_in"] = False


# Função de login adaptada para uso como ferramenta do browser-use
@tools.action(
    description="Perform login to SIGAA UFPA system using provided credentials from environment variables"
)
async def login_sigaa(browser_session: BrowserSession) -> str:
    try:
        # Obter a página atual do BrowserSession usando o método correto
        page = await browser_session.get_current_page()
        await page.goto(BASE_URL)
        await perform_login_discente(page)
        return "Login to SIGAA UFPA completed successfully."
    except Exception as e:
        logger.error(f"Erro no login SIGAA: {e}")
        return f"Login failed: {e}"


# Lifespan async para FastMCP
@asynccontextmanager
async def lifespan_manager(app):
    logger.info("🚀 Iniciando servidor MCP...")
    try:
        # await login_sigaa()
        if transport_mode == "http":
            await full_login_procedure_discente()
        yield
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
    finally:
        logger.info("🔄 Desligando servidor...")
        # Encerrando todos os recursos
        try:
            await browser.stop()
        except Exception as e:
            logger.error(f"Erro ao encerrar o navegador: {e}")


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


@mcp.resource("resource://drive-images")
def get_drive_images():
    try:
        service = drive_service.GoogleDriveService()
        files = service.listar_arquivos_na_pasta()
        images = [f for f in files if f.get("mimeType", "").startswith("image/")]
        return {"images": images}
    except Exception as e:
        return {"error": str(e)}


# Ferramenta 0 para http: Reiniciar sessão do navegador e relogar
if transport_mode == "http":

    @mcp.tool()
    async def reiniciar_sessao() -> Dict[str, Any]:
        """
        Reinicia a sessão do navegador e realiza o login novamente.
        """
        global startup_status
        await full_login_procedure_discente()
        return {
            "success": startup_status["success"],
            "message": startup_status["message"],
            "logged_in": startup_status["logged_in"],
        }


# Ferramenta 1: Baixar histórico escolar em PDF
@mcp.tool()
async def baixar_historico_escolar() -> Dict[str, Any]:
    """
    Baixa o histórico escolar completo do aluno em PDF e retorna o caminho do arquivo salvo.
    """
    prompt = """
    If you are not logged in, use the login_sigaa tool to log in first.
    1. Se aparecer Selecione o Ano-Período mais atual
    2. Se aparecer Selecione o Portal do Discente
    3. Clique em Ensino
    4. Clique em Emitir Histórico
    5. O Histórico será salvo automaticamente no navegador
    Obs.: Durante o período de processamento de matricula não é possível emitir histórico"""

    try:
        if transport_mode == "studio":
            await full_login_procedure_discente()
        result = await Agent(
            task=prompt,
            use_vision=False,
            max_failures=7,
            step_timeout=120,
            llm_timeout=90,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
            tools=tools,
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
    prompt = f"""If you are not logged in, use the login_sigaa tool to log in first.
 Para o curso de {curso} e turno {turno}, liste todas as disciplinas ofertadas no semestre atual.
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
        if transport_mode == "studio":
            await full_login_procedure_discente()
        result = await Agent(
            task=prompt,
            use_vision=False,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
            tools=tools,
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
    If you are not logged in, use the login_sigaa tool to log in first.
    Obs.: Os horários de aula podem ser encontrados na seção de "Turmas do Semestre" e no Atestado de Matrícula.
    1. Se aparecer Selecione o Ano-Período mais atual
    2. Se aparecer Selecione o Portal do Discente
    3. Se necessário, clique em Ensino
    4. Se necessário, clique em Emitir Atestado de Matrícula(Note que quando o atestado é emitido, é aberta outra aba no navegador)
    """

    try:
        if transport_mode == "studio":
            await full_login_procedure_discente()
        result = await Agent(
            task=prompt,
            use_vision=False,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
            tools=tools,
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
    If you are not logged in, use the login_sigaa tool to log in first.
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
        if transport_mode == "studio":
            await full_login_procedure_discente()
        result = await Agent(
            task=prompt,
            use_vision=False,
            browser=browser,
            # sensitive_data=sensitive_data,
            llm=llm,
            tools=tools,
        ).run()
        return result
    except Exception as e:
        logger.error(f"Erro ao listar avisos das turmas: {e}")
        return {"success": False, "error": str(e)}


# Ferramenta 5: Trocar a Imagem de Perfil do Discente e Descrição
@mcp.tool()
async def trocar_imagem_perfil(
    drive_file_id: str = Field(
        ..., description="ID do arquivo de imagem no Google Drive"
    ),
    descricao: str = Field("", description="Nova descrição para o perfil (opcional)"),
) -> Dict[str, Any]:
    """
    Troca a imagem de perfil do discente e atualiza a descrição.
    """

    try:
        # llm = ChatOpenAI(
        #     model="moonshotai/kimi-k2-instruct-0905",
        #     base_url="http://host.docker.internal:8080/api/Groq/",
        #     api_key=os.environ.get("GROQ_API_KEY"),
        # )
        service = drive_service.GoogleDriveService()
        b64 = service.download_em_base64(drive_file_id)
        if not b64:
            raise Exception("Falha ao baixar imagem do Drive")
        image_bytes = base64.b64decode(b64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_bytes)
            temp_image_path = temp_file.name

        if transport_mode == "studio":
            await full_login_procedure_discente()
        page = await browser.get_current_page()
        # Pegar o CPF e a data de nascimento dos dados do discente
        botao = await esperar_elemento(
            page, r"#j_id_jsp_612222572_250\:meusDadosPessoais"
        )
        await botao.click()
        await esperar_elemento(
            page, ".formulario > tbody:nth-child(2) > tr:nth-child(5) > td:nth-child(2)"
        )

        # Extract structured data
        class UserInfo(BaseModel):
            data_nascimento: str
            cpf: str

        userinfo = await Agent(
            task="Extract Data de Nascimento: ... and CPF: ... from the page.",
            use_vision=False,
            browser=browser,
            llm=llm,
            output_model_schema=UserInfo,
        ).run()
        userinfo = userinfo.final_result()
        userinfo: UserInfo = UserInfo.model_validate_json(userinfo)
        # data_nascimento_element = await esperar_elemento(
        #     page, ".formulario > tbody:nth-child(2) > tr:nth-child(5) > td:nth-child(2)"
        # )
        # cpf_element = await esperar_elemento(
        #     page,
        #     ".formulario > tbody:nth-child(2) > tr:nth-child(13) > td:nth-child(2)",
        # )
        # data_nascimento_element = await data_nascimento_element.get_attribute("innerText")
        # cpf_element = await cpf_element.get_attribute("innerText")
        sensitive_data = {
            "data_nascimento": userinfo.data_nascimento,
            "cpf": userinfo.cpf,
            "senha": os.environ.get("SIGAA_PASSWORD"),
        }
        print(sensitive_data)
        # Clicando em Menu do Discente
        botao = await esperar_elemento(page, ".menus")
        await botao.click()
        # Clicando em Atualizar Foto e Perfil
        botao = await esperar_elemento(page, ".perfil")
        await botao.click()
        # Primeiro agente: Adicionar imagem e descrição
        prompt_adicionar = f"""Troque a imagem de perfil do discente no SIGAA UFPA. A imagem está localizada em {temp_image_path}.
        Atualize a descrição do perfil para: {descricao} Não clique em gravar perfil"""
        result_adicionar = await Agent(
            task=prompt_adicionar,
            use_vision=False,
            browser=browser,
            llm=llm,
            tools=tools,
            available_file_paths=[temp_image_path],
        ).run()

        # Segundo agente: Confirmar usando dados pessoais e resultado do primeiro
        prompt_confirmar = f"""Com base no resultado da adição da imagem e descrição: {result_adicionar}\n
        Confirme a identidade do discente usando os dados pessoais (CPF ou Data de Nascimento) fornecidos e verifique se a troca foi realizada com sucesso."""
        result_confirmar = await Agent(
            task=prompt_confirmar,
            use_vision=False,
            browser=browser,
            sensitive_data=sensitive_data,
            llm=llm,
            tools=tools,
            available_file_paths=[temp_image_path],
        ).run()

        # Combinar resultados
        return result_confirmar

    except Exception as e:
        logger.error(f"Erro ao trocar imagem de perfil: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # Limpar arquivo temporário
        try:
            if "temp_image_path" in locals():
                os.unlink(temp_image_path)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        # logger.info(os.environ)
        if transport_mode == "http":
            logger.info("Iniciando servidor MCP em modo HTTP...")
            mcp.run(transport="http", host="0.0.0.0", port=8003)
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
