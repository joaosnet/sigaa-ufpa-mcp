import asyncio
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from browser_use import Agent, Browser
from browser_use.llm.google import ChatGoogle

from utils.sigaa_helpers import SIGAAHelpers

logger = logging.getLogger(__name__)

class SIGAAConfig:
    BASE_URL = "https://sigaa.ufpa.br"
    LOGIN_URL = f"{BASE_URL}/sigaa/verTelaLogin.do"
    MOBILE_URL = f"{BASE_URL}/sigaa/mobile/touch/public/principal.jsf"

class SIGAAActor:
    def __init__(self):
        self.llm = None
        self.is_logged_in_flag = False
        self.user_info = {}
        self.helpers = SIGAAHelpers()
        self.agent: Optional[Agent] = None
        self.browser: Optional[Browser] = None
        self.current_page = None # Para manter referência à página atual após login

        # Configurar LLM baseado nas variáveis de ambiente
        self._setup_llm()

    def _setup_llm(self):
        """Configura o LLM para usar o Google Gemini."""
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi configurada.")

        self.llm = ChatGoogle(
            api_key=gemini_api_key,
            model="gemini-flash-latest",
        )

    async def initialize(self):
        """Inicializa o SIGAA Actor"""
        try:
            self.browser = Browser()
            await self.browser.start()
            logger.info("SIGAA Actor e Browser inicializados.")
        except Exception as e:
            logger.error(f"Erro ao inicializar SIGAA Actor: {e}")
            raise

    async def login(self, username: str, password: str, force_new: bool = False) -> Dict[str, Any]:
        """
        Realiza login no SIGAA usando a abordagem direta com o browser.
        """
        if self.is_logged_in_flag and not force_new:
            return {
                "success": True,
                "message": "Já logado no SIGAA",
                "logged_in": True,
                "user_info": self.user_info
            }

        logger.info("Iniciando login no SIGAA UFPA")

        if not self.browser:
            await self.initialize()

        try:
            page = await self.browser.new_page(SIGAAConfig.LOGIN_URL)
            
            # Aguardar carregamento da página
            await asyncio.sleep(2)
            
            # Preencher usuário - usando IA para encontrar o campo
            username_field = await page.must_get_element_by_prompt("campo de nome de usuário ou matrícula para login", llm=self.llm)
            await username_field.fill(username)
            
            # Preencher senha - usando IA para encontrar o campo
            password_field = await page.must_get_element_by_prompt("campo de senha para login", llm=self.llm)
            await password_field.fill(password)

            # Clicar no botão de login - usando IA para encontrar o botão
            login_button = await page.must_get_element_by_prompt("botão de login ou entrar", llm=self.llm)
            await login_button.click()
            
            # Aguardar a navegação
            await asyncio.sleep(5)

            # Verificar se o login foi bem-sucedido
            final_page_url = await page.get_url()
            page_content = await page.evaluate('() => document.body.innerText')

            success_indicators = ["Portal do Discente", "Bem-vindo", "logout", "discente"]
            login_successful = any(indicator.lower() in page_content.lower() for indicator in success_indicators)

            if login_successful:
                self.is_logged_in_flag = True
                self.current_page = page # Armazenar referência à página logada
                
                # Extrair informações do usuário
                try:
                    # Verificar se estamos na página correta para extrair informações
                    if "discente" in final_page_url.lower() or "portal" in final_page_url.lower():
                        # Extrair informações do usuário usando IA
                        user_info_prompt = "Extraia o nome completo do usuário, a matrícula e o curso da página atual. Retorne como um objeto JSON com campos: nome, matricula, curso."
                        self.user_info = await page.extract_content(user_info_prompt, dict, llm=self.llm)
                    else:
                        # Navegar para uma página com informações do usuário
                        await page.goto(f"{SIGAAConfig.BASE_URL}/sigaa/verPortalDiscente.do")
                        await asyncio.sleep(3)
                        user_info_prompt = "Extraia o nome completo do usuário, a matrícula e o curso da página atual. Retorne como um objeto JSON com campos: nome, matricula, curso."
                        self.user_info = await page.extract_content(user_info_prompt, dict, llm=self.llm)
                except Exception as e:
                    logger.warning(f"Não foi possível extrair informações do usuário: {e}")
                    self.user_info = {"nome": "Não identificado", "matricula": "Não identificada", "curso": "Não identificado"}
                
                # Criar agente para uso posterior nas operações
                # O agente será criado sob demanda nos métodos que precisarem dele
                
                return {
                    "success": True,
                    "message": "Login realizado com sucesso.",
                    "logged_in": True,
                    "user_info": self.user_info,
                }
            else:
                # Tenta extrair mensagem de erro da página
                try:
                    error_text = await page.evaluate('() => document.querySelector(".msg-erro")?.innerText || document.querySelector(".error")?.innerText || "Falha no login. Verifique suas credenciais."')
                    error_message = error_text if error_text.strip() else "Falha no login. Verifique suas credenciais."
                except Exception:
                    error_message = "Falha no login. Verifique suas credenciais."
                
                return {
                    "success": False,
                    "error": error_message,
                    "logged_in": False,
                }

        except Exception as e:
            logger.error(f"Erro durante o login: {e}")
            return {
                "success": False,
                "error": str(e),
                "logged_in": False
            }
    
    def is_logged_in(self) -> bool:
        """Verifica se está logado"""
        return self.is_logged_in_flag
    
    async def navigate_to_section(self, section: str) -> Dict[str, Any]:
        """Navega para uma seção específica do SIGAA usando o browser diretamente."""
        if not self.is_logged_in_flag or not self.current_page:
            return {"success": False, "error": "Não está logado ou a página não está disponível."}

        logger.info(f"Navegando para a seção '{section}'.")

        try:
            # Mapeamento de seções para termos mais descritivos para o LLM
            section_map = {
                "notas": "Consultar Notas Finais",
                "historico": "Histórico Acadêmico",
                "matricula": "Matrícula Online",
                "comprovantes": "Emissão de Comprovantes e Declarações",
                "atestados": "Atestado de Matrícula",
                "horario": "Meu Horário de Aulas"
            }
            
            descriptive_section = section_map.get(section.lower(), section)

            # Usar IA para encontrar e clicar no link da seção
            task = f"No portal do discente, encontre e clique no link ou item de menu para '{descriptive_section}'."
            
            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page  # Usar a página atual
            )
            
            result = await agent.run()
            
            # Atualizar a referência da página atual após a navegação
            self.current_page = agent.page

            final_page_url = await agent.page.get_url()

            return {
                "success": True,
                "message": f"Navegação para a seção '{section}' concluída.",
                "section": section,
                "current_url": final_page_url,
                "details": str(result)
            }

        except Exception as e:
            logger.error(f"Erro ao navegar para a seção '{section}': {e}")
            return {"success": False, "error": str(e), "section": section}
    
    async def extract_grades(self) -> Dict[str, Any]:
        """Extrai notas das disciplinas"""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}
        try:
            # Usar IA para extrair dados estruturados de notas
            from pydantic import BaseModel
            
            class Grade(BaseModel):
                disciplina: str
                nota_final: Optional[str]
                situacao: str
                periodo: str
            
            grades_data = await self.current_page.extract_content(
                "Extrair todas as notas e situações das disciplinas desta página",
                List[Grade],
                llm=self.llm
            )
            
            return {
                "success": True,
                "data": grades_data,
                "type": "grades"
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair notas: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_transcript(self) -> Dict[str, Any]:
        """Extrai histórico acadêmico"""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}
        try:
            from pydantic import BaseModel
            
            class Subject(BaseModel):
                codigo: str
                nome: str
                creditos: int
                nota: Optional[str]
                situacao: str
                periodo: str
            
            transcript_data = await self.current_page.extract_content(
                "Extrair histórico acadêmico completo com todas as disciplinas",
                List[Subject],
                llm=self.llm
            )
            
            return {
                "success": True,
                "data": transcript_data,
                "type": "transcript"
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair histórico: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_enrollment_info(self) -> Dict[str, Any]:
        """Extrai informações de matrícula"""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}
        try:
            enrollment_info = await self.current_page.extract_content(
                "Extrair informações de matrícula atual incluindo disciplinas matriculadas, horários e status",
                dict,
                llm=self.llm
            )
            
            return {
                "success": True,
                "data": enrollment_info,
                "type": "enrollment"
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações de matrícula: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_general_info(self) -> Dict[str, Any]:
        """Extrai informações gerais da página atual"""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}
        try:
            page_info = await self.current_page.extract_content(
                "Extrair todas as informações importantes desta página do SIGAA",
                dict,
                llm=self.llm
            )
            
            return {
                "success": True,
                "data": page_info,
                "type": "general"
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações gerais: {e}")
            return {"success": False, "error": str(e)}
    
    async def download_document(self, doc_type: str, format: str = "pdf", semester: Optional[str] = None) -> Dict[str, Any]:
        """Baixa documentos do SIGAA."""
        if not self.is_logged_in_flag or not self.current_page:
            return {"success": False, "error": "Não está logado ou a página não está disponível."}

        logger.info(f"Tentando baixar documento '{doc_type}'.")

        try:
            doc_map = {
                "historico_academico": "histórico acadêmico",
                "comprovante_matricula": "comprovante de matrícula",
                "diploma": "diploma",
                "ira": "índice de rendimento (IRA)"
            }
            search_term = doc_map.get(doc_type, doc_type)

            task = f"Encontre e clique no link para gerar ou baixar o documento '{search_term}'. O formato esperado é {format}."
            if semester:
                task += f" para o período {semester}."

            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page  # Usar a página atual
            )
            
            await agent.run()
            
            # Atualizar a referência da página atual após a navegação
            self.current_page = agent.page
            
            # Aguardar um tempo para o download iniciar e concluir
            await asyncio.sleep(10)

            # Verificar a pasta de downloads
            download_path = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Procurar o arquivo mais recente na pasta de downloads
            latest_file = None
            latest_time = 0
            
            files_in_dir = list(download_path.glob(f"*.{format}"))
            # Adicionar busca em subdiretórios comuns de download do chrome
            chrome_download_path = Path("./chrome-data/Default/Downloads")
            if chrome_download_path.exists():
                files_in_dir.extend(list(chrome_download_path.glob(f"*.{format}")))

            for file in files_in_dir:
                if file.exists() and file.stat().st_mtime > latest_time:
                    latest_time = file.stat().st_mtime
                    latest_file = file

            if latest_file and (datetime.now().timestamp() - latest_time) < 120:  # Arquivo recente (2 minutos)
                filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                final_path = download_path / filename
                latest_file.rename(final_path)

                return {
                    "success": True,
                    "document_type": doc_type,
                    "file_path": str(final_path),
                    "filename": filename
                }
            
            return {
                "success": False,
                "error": f"Não foi possível confirmar o download do documento: {doc_type}",
                "document_type": doc_type
            }

        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return {"success": False, "error": str(e), "document_type": doc_type}
    
    async def execute_custom_task(self, task: str, max_steps: int = 20, return_data: bool = True) -> Dict[str, Any]:
        """Executa tarefa personalizada usando IA."""
        if not self.is_logged_in_flag or not self.current_page:
            return {"success": False, "error": "Não está logado ou a página não está disponível."}

        logger.info(f"Executando tarefa personalizada: {task}")

        try:
            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=f"No SIGAA da UFPA, execute a seguinte tarefa: {task}",
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page,  # Usar a página atual
                max_steps=max_steps
            )
            
            result = await agent.run()
            
            # Atualizar a referência da página atual após a execução da tarefa
            self.current_page = agent.page
            
            extracted_data = None
            if return_data:
                try:
                    extracted_data = await self.current_page.extract_content(
                        "Extrair dados relevantes da página atual após executar a tarefa",
                        dict,
                        llm=self.llm
                    )
                except Exception as e:
                    logger.warning(f"Falha ao extrair dados após tarefa personalizada: {e}")

            return {
                "success": True,
                "task": task,
                "result": str(result),
                "extracted_data": extracted_data
            }

        except Exception as e:
            logger.error(f"Erro na tarefa personalizada: {e}")
            return {"success": False, "error": str(e), "task": task}
    
    async def get_notifications(self) -> Dict[str, Any]:
        """Obtém notificações do SIGAA."""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}
        
        logger.info("Obtendo notificações.")
        
        try:
            task = "Navegue até a área de notificações ou página principal e extraia todos os avisos, mensagens e notificações não lidas."
            
            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page  # Usar a página atual
            )
            
            await agent.run()

            # Atualizar a referência da página atual após a navegação
            self.current_page = agent.page
            
            notifications = await self.current_page.extract_content(
                "Extraia o texto de todas as notificações, avisos e mensagens importantes da página",
                list,
                llm=self.llm
            )

            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter notificações: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_class_schedule(self) -> Dict[str, Any]:
        """Obtém horário de aulas."""
        if not self.current_page:
            return {"success": False, "error": "Página não está disponível."}

        logger.info("Obtendo horário de aulas.")

        try:
            task = "Navegue até a seção de horário de aulas e extraia todas as informações: nome da disciplina, horários, professor e sala."
            
            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page  # Usar a página atual
            )
            
            await agent.run()

            # Atualizar a referência da página atual após a navegação
            self.current_page = agent.page
            
            schedule_data = await self.current_page.extract_content(
                "Extrair o horário de aulas completo, incluindo disciplinas, horários, professores e salas.",
                dict,
                llm=self.llm
            )
            
            return {
                "success": True,
                "schedule": schedule_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter horário: {e}")
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, filename_prefix: str = "sigaa") -> str:
        """Captura screenshot da página atual."""
        if not self.current_page:
            return ""
        try:
            screenshot_dir = Path(os.getenv("SCREENSHOT_PATH", "./screenshots"))
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = screenshot_dir / filename
            
            await self.current_page.screenshot(path=str(screenshot_path))
            
            logger.info(f"Screenshot salvo em: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {e}")
            return ""
    
    async def check_status(self) -> Dict[str, Any]:
        """Verifica o status da sessão."""
        try:
            page_available = self.current_page is not None
            
            status = {
                "success": True,
                "logged_in": self.is_logged_in_flag,
                "user_info": self.user_info,
                "page_available": page_available
            }
            
            if page_available:
                current_url = await self.current_page.get_url()
                status["current_url"] = current_url
                status["on_sigaa"] = "sigaa.ufpa.br" in current_url

            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar status do agente: {e}")
            return {"success": False, "error": str(e), "logged_in": self.is_logged_in_flag}
    
    async def logout(self) -> Dict[str, Any]:
        """Faz logout do SIGAA."""
        if not self.is_logged_in_flag or not self.current_page:
            self.is_logged_in_flag = False
            return {"success": True, "message": "Nenhuma sessão ativa para fazer logout."}

        logger.info("Realizando logout.")

        try:
            task = "Encontre e clique no link de 'Sair' ou 'Logout' para encerrar a sessão."
            
            # Criar um agente temporário para esta tarefa específica
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,  # Usar o browser existente
                page=self.current_page  # Usar a página atual
            )
            
            await agent.run()

            self.is_logged_in_flag = False
            self.user_info = {}
            self.current_page = None
            
            # Idealmente, o cleanup do agente deveria ser chamado aqui ou no 'cleanup' geral.
            await self.cleanup()

            return {
                "success": True,
                "message": "Logout realizado com sucesso."
            }

        except Exception as e:
            logger.error(f"Erro no logout: {e}")
            self.is_logged_in_flag = False # Força o estado de deslogado
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Limpa os recursos do ator, incluindo o navegador."""
        logger.info("Iniciando limpeza do SIGAA Actor.")
        try:
            if self.browser:
                await self.browser.stop()
            
            self.agent = None
            self.browser = None
            self.current_page = None
            self.is_logged_in_flag = False
            self.user_info = {}
            
            logger.info("SIGAA Actor e recursos associados foram limpos com sucesso.")
            
        except Exception as e:
            logger.error(f"Erro durante a limpeza do SIGAA Actor: {e}")