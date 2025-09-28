import asyncio
import os
import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from sigaa_actor import SIGAAActor
from utils.pdf_extractor import PDFExtractor

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar FastMCP
mcp = FastMCP("SIGAA UFPA MCP Server")

# Modelos de dados
class LoginCredentials(BaseModel):
    username: str = Field(..., description="Nome de usuário do SIGAA")
    password: str = Field(..., description="Senha do SIGAA")

class SIGAATask(BaseModel):
    task: str = Field(..., description="Tarefa a ser executada no SIGAA")
    max_steps: int = Field(default=20, description="Número máximo de passos")
    use_credentials: bool = Field(default=True, description="Usar credenciais do .env")
    custom_credentials: Optional[LoginCredentials] = None

class DocumentDownload(BaseModel):
    document_type: str = Field(..., description="Tipo de documento (historico, diploma, etc)")
    format: str = Field(default="pdf", description="Formato do documento")
    semester: Optional[str] = Field(None, description="Semestre específico (se aplicável)")

# Instância global do SIGAA Actor
sigaa_actor: Optional[SIGAAActor] = None

async def get_sigaa_actor() -> SIGAAActor:
    """Obter instância do SIGAA Actor (singleton)"""
    global sigaa_actor
    if sigaa_actor is None:
        sigaa_actor = SIGAAActor()
        await sigaa_actor.initialize()
    return sigaa_actor

@mcp.tool()
async def sigaa_login(
    username: Optional[str] = None, 
    password: Optional[str] = None,
    force_new_session: bool = False
) -> Dict[str, Any]:
    """
    Faz login no SIGAA UFPA usando as credenciais fornecidas ou do ambiente.
    
    Args:
        username: Nome de usuário (opcional, usa .env se não fornecido)
        password: Senha (opcional, usa .env se não fornecida)  
        force_new_session: Forçar nova sessão mesmo se já logado
    
    Returns:
        Resultado do login com informações da sessão
    """
    try:
        actor = await get_sigaa_actor()
        
        # Usar credenciais do ambiente se não fornecidas
        if not username:
            username = os.getenv("SIGAA_USERNAME")
        if not password:
            password = os.getenv("SIGAA_PASSWORD")
            
        if not username or not password:
            return {
                "success": False,
                "error": "Credenciais não fornecidas. Configure SIGAA_USERNAME e SIGAA_PASSWORD no .env",
                "logged_in": False
            }
        
        result = await actor.login(username, password, force_new_session)
        
        logger.info(f"Login attempt result: {result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"Erro no login SIGAA: {e}")
        return {
            "success": False,
            "error": str(e),
            "logged_in": False
        }

@mcp.tool()
async def sigaa_navigate_and_extract(
    section: str,
    extract_data: bool = True,
    take_screenshot: bool = True
) -> Dict[str, Any]:
    """
    Navega para uma seção específica do SIGAA e extrai informações.
    
    Args:
        section: Seção do SIGAA (exemplo: 'notas', 'historico', 'matricula')
        extract_data: Se deve extrair dados estruturados
        take_screenshot: Se deve capturar screenshot
    
    Returns:
        Dados extraídos da seção
    """
    try:
        actor = await get_sigaa_actor()
        
        if not actor.is_logged_in():
            login_result = await sigaa_login()
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Não foi possível fazer login",
                    "section": section
                }
        
        result = await actor.navigate_to_section(section)
        
        if result["success"] and extract_data:
            # Extrair dados específicos da seção
            if section.lower() in ["notas", "grades"]:
                result["extracted_data"] = await actor.extract_grades()
            elif section.lower() in ["historico", "history"]:
                result["extracted_data"] = await actor.extract_transcript()
            elif section.lower() in ["matricula", "enrollment"]:
                result["extracted_data"] = await actor.extract_enrollment_info()
            else:
                result["extracted_data"] = await actor.extract_general_info()
        
        if take_screenshot:
            screenshot_path = await actor.take_screenshot(f"sigaa_{section}")
            result["screenshot"] = screenshot_path
        
        return result
        
    except Exception as e:
        logger.error(f"Erro na navegação SIGAA: {e}")
        return {
            "success": False,
            "error": str(e),
            "section": section
        }

@mcp.tool()
async def sigaa_download_document(
    document_type: str,
    format: str = "pdf",
    semester: Optional[str] = None
) -> Dict[str, Any]:
    """
    Baixa documentos do SIGAA como histórico acadêmico, comprovantes, etc.
    
    Args:
        document_type: Tipo de documento (historico_academico, comprovante_matricula, etc)
        format: Formato do documento (pdf, html)
        semester: Semestre específico se aplicável (ex: 2024.1)
    
    Returns:
        Informações sobre o download do documento
    """
    try:
        actor = await get_sigaa_actor()
        
        if not actor.is_logged_in():
            login_result = await sigaa_login()
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Não foi possível fazer login",
                    "document_type": document_type
                }
        
        result = await actor.download_document(document_type, format, semester)
        
        # Se o documento foi baixado, extrair texto se for PDF
        if result["success"] and result.get("file_path") and format == "pdf":
            try:
                pdf_extractor = PDFExtractor()
                text_content = await pdf_extractor.extract_text_from_pdf(result["file_path"])
                result["text_content"] = text_content[:2000]  # Primeiros 2000 caracteres
            except Exception as e:
                logger.warning(f"Não foi possível extrair texto do PDF: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no download de documento: {e}")
        return {
            "success": False,
            "error": str(e),
            "document_type": document_type
        }

@mcp.tool()
async def sigaa_custom_task(
    task: str,
    max_steps: int = 20,
    return_structured_data: bool = True
) -> Dict[str, Any]:
    """
    Executa uma tarefa personalizada no SIGAA usando IA.
    
    Args:
        task: Descrição da tarefa em linguagem natural
        max_steps: Número máximo de passos para a tarefa
        return_structured_data: Se deve tentar extrair dados estruturados
    
    Returns:
        Resultado da execução da tarefa
    """
    try:
        actor = await get_sigaa_actor()
        
        if not actor.is_logged_in():
            login_result = await sigaa_login()
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Não foi possível fazer login",
                    "task": task
                }
        
        result = await actor.execute_custom_task(task, max_steps, return_structured_data)
        return result
        
    except Exception as e:
        logger.error(f"Erro na tarefa personalizada: {e}")
        return {
            "success": False,
            "error": str(e),
            "task": task
        }

@mcp.tool()
async def sigaa_get_notifications() -> Dict[str, Any]:
    """
    Obtém notificações e avisos do SIGAA.
    
    Returns:
        Lista de notificações e avisos
    """
    try:
        actor = await get_sigaa_actor()
        
        if not actor.is_logged_in():
            login_result = await sigaa_login()
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Não foi possível fazer login"
                }
        
        result = await actor.get_notifications()
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter notificações: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def sigaa_get_class_schedule() -> Dict[str, Any]:
    """
    Obtém o horário de aulas atual do aluno.
    
    Returns:
        Horário de aulas estruturado
    """
    try:
        actor = await get_sigaa_actor()
        
        if not actor.is_logged_in():
            login_result = await sigaa_login()
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Não foi possível fazer login"
                }
        
        result = await actor.get_class_schedule()
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter horário: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def sigaa_check_status() -> Dict[str, Any]:
    """
    Verifica o status da sessão SIGAA e informações básicas.
    
    Returns:
        Status da sessão e informações do usuário
    """
    try:
        actor = await get_sigaa_actor()
        result = await actor.check_status()
        return result
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return {
            "success": False,
            "error": str(e),
            "logged_in": False
        }

@mcp.tool()
async def sigaa_logout() -> Dict[str, Any]:
    """
    Faz logout do SIGAA e limpa a sessão.
    
    Returns:
        Resultado do logout
    """
    try:
        actor = await get_sigaa_actor()
        result = await actor.logout()
        
        # Cleanup global instance
        global sigaa_actor
        if sigaa_actor:
            await sigaa_actor.cleanup()
            sigaa_actor = None
            
        return result
        
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Cleanup ao encerrar
async def cleanup():
    """Limpa recursos ao encerrar o servidor"""
    global sigaa_actor
    if sigaa_actor:
        await sigaa_actor.cleanup()
        sigaa_actor = None

if __name__ == "__main__":
    try:
        # Padrão é 'stdio', a menos que MCP_TRANSPORT seja 'http'
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio")
        
        if transport_mode == "http":
            logger.info("Iniciando servidor MCP em modo HTTP...")
            mcp.run(transport="http", host="0.0.0.0", port=8000)
        elif transport_mode == "stdio":
            logger.info("Iniciando servidor MCP em modo stdio...")
            mcp.run(transport="stdio")
        else:
            logger.error(f"Modo de transporte desconhecido: {transport_mode}. Use 'stdio' ou 'http'.")
            # Inicia em stdio como fallback seguro para clientes MCP
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Encerrando servidor...")
    finally:
        asyncio.run(cleanup())