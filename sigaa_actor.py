import asyncio
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from browser_use import Browser, Agent
from browser_use.browser.browser import BrowserConfig
from browser_use.llm.openai import ChatOpenAI
from browser_use.llm.anthropic import ChatAnthropic
from browser_use.llm.google import ChatGoogle

from utils.sigaa_helpers import SIGAAHelpers

logger = logging.getLogger(__name__)

class SIGAAConfig:
    BASE_URL = "https://sigaa.ufpa.br"
    LOGIN_URL = f"{BASE_URL}/sigaa/public/home.jsf"
    MOBILE_URL = f"{BASE_URL}/sigaa/mobile/touch/public/principal.jsf"
    
    # Seletores CSS comuns
    SELECTORS = {
        "username_field": "input[name='loginForm:login']",
        "password_field": "input[name='loginForm:senha']", 
        "login_button": "input[value='Entrar']",
        "menu_discente": "a[href*='discente']",
        "logout_link": "a[href*='logout']"
    }

class SIGAAActor:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.current_page = None
        self.llm = None
        self.is_logged_in_flag = False
        self.user_info = {}
        self.helpers = SIGAAHelpers()
        
        # Configurar LLM baseado nas variáveis de ambiente
        self._setup_llm()
    
    def _setup_llm(self):
        """Configura o LLM baseado nas variáveis de ambiente disponíveis"""
        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o",
                temperature=0.1
            )
        elif os.getenv("ANTHROPIC_API_KEY"):
            self.llm = ChatAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model="claude-3-5-sonnet-20241022",
                temperature=0.1
            )
        elif os.getenv("GEMINI_API_KEY"):
            self.llm = ChatGoogle(
                api_key=os.getenv("GEMINI_API_KEY"),
                model="gemini-1.5-pro",
                temperature=0.1
            )
        else:
            raise ValueError("Nenhuma API key de LLM encontrada. Configure OPENAI_API_KEY, ANTHROPIC_API_KEY ou GEMINI_API_KEY")
    
    async def initialize(self):
        """Inicializa o browser e configurações"""
        try:
            # Configuração do browser
            config = BrowserConfig(
                headless=os.getenv("CHROME_HEADLESS", "false").lower() == "true",
                chrome_user_data_dir="/app/data/chrome-data",
                debugging_port=int(os.getenv("CHROME_DEBUG_PORT", "9222")),
                window_width=1920,
                window_height=1080,
                disable_security=True  # Necessário para alguns sites
            )
            
            self.browser = Browser(config=config)
            await self.browser.start()
            
            logger.info("SIGAA Actor inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar SIGAA Actor: {e}")
            raise
    
    async def login(self, username: str, password: str, force_new: bool = False) -> Dict[str, Any]:
        """
        Realiza login no SIGAA usando browser actors
        """
        try:
            if self.is_logged_in_flag and not force_new:
                return {
                    "success": True,
                    "message": "Já logado no SIGAA",
                    "logged_in": True,
                    "user_info": self.user_info
                }
            
            logger.info("Iniciando login no SIGAA UFPA")
            
            # Navegar para a página de login
            page = await self.browser.new_page(SIGAAConfig.LOGIN_URL)
            await asyncio.sleep(3)  # Aguardar carregamento
            
            # Aguardar elementos de login aparecerem
            username_field = None
            password_field = None
            login_button = None
            
            for attempt in range(5):
                try:
                    # Tentar localizar campos de login usando CSS seletores
                    username_elements = await page.get_elements_by_css_selector(SIGAAConfig.SELECTORS["username_field"])
                    password_elements = await page.get_elements_by_css_selector(SIGAAConfig.SELECTORS["password_field"])
                    button_elements = await page.get_elements_by_css_selector(SIGAAConfig.SELECTORS["login_button"])
                    
                    if username_elements and password_elements and button_elements:
                        username_field = username_elements[0]
                        password_field = password_elements[0]
                        login_button = button_elements[0]
                        break
                        
                    # Se não encontrou pelos seletores CSS, tentar usando LLM
                    username_field = await page.get_element_by_prompt("campo de nome de usuário ou login", llm=self.llm)
                    password_field = await page.get_element_by_prompt("campo de senha", llm=self.llm)
                    login_button = await page.get_element_by_prompt("botão entrar ou login", llm=self.llm)
                    
                    if username_field and password_field and login_button:
                        break
                        
                except Exception as e:
                    logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
                    await asyncio.sleep(2)
            
            if not all([username_field, password_field, login_button]):
                return {
                    "success": False,
                    "error": "Não foi possível localizar os campos de login",
                    "logged_in": False
                }
            
            # Preencher credenciais
            await username_field.fill(username)
            await asyncio.sleep(1)
            
            await password_field.fill(password)
            await asyncio.sleep(1)
            
            # Clicar no botão de login
            await login_button.click()
            await asyncio.sleep(5)  # Aguardar redirecionamento
            
            # Verificar se o login foi bem-sucedido
            current_url = await page.evaluate("() => window.location.href")
            
            # Procurar por elementos que indicam login bem-sucedido
            success_indicators = [
                "Portal do Discente",
                "menu discente",
                "Bem-vindo",
                "logout"
            ]
            
            page_content = await page.evaluate("() => document.body.innerText")
            login_successful = any(indicator.lower() in page_content.lower() for indicator in success_indicators)
            
            if login_successful or "discente" in current_url.lower():
                self.is_logged_in_flag = True
                self.current_page = page
                
                # Extrair informações básicas do usuário
                try:
                    self.user_info = await self._extract_user_info(page)
                except Exception as e:
                    logger.warning(f"Não foi possível extrair informações do usuário: {e}")
                    self.user_info = {"username": username}
                
                return {
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "logged_in": True,
                    "user_info": self.user_info,
                    "current_url": current_url
                }
            else:
                # Verificar mensagens de erro
                error_elements = await page.get_elements_by_css_selector(".error, .alert, .mensagem-erro")
                error_message = "Falha no login - verifique suas credenciais"
                
                if error_elements:
                    try:
                        error_text = await error_elements[0].evaluate("el => el.innerText")
                        if error_text:
                            error_message = error_text
                    except:
                        pass
                
                return {
                    "success": False,
                    "error": error_message,
                    "logged_in": False,
                    "current_url": current_url
                }
                
        except Exception as e:
            logger.error(f"Erro durante o login: {e}")
            return {
                "success": False,
                "error": str(e),
                "logged_in": False
            }
    
    async def _extract_user_info(self, page) -> Dict[str, Any]:
        """Extrai informações básicas do usuário logado"""
        try:
            user_info = {}
            
            # Tentar extrair nome do usuário
            name_selectors = [
                ".usuario-nome",
                ".nome-usuario", 
                ".welcome-message",
                "#usuario-info"
            ]
            
            for selector in name_selectors:
                elements = await page.get_elements_by_css_selector(selector)
                if elements:
                    text = await elements[0].evaluate("el => el.innerText")
                    if text and len(text.strip()) > 0:
                        user_info["name"] = text.strip()
                        break
            
            # Extrair matrícula se visível
            matricula_element = await page.get_element_by_prompt("número de matrícula do aluno", llm=self.llm)
            if matricula_element:
                matricula_text = await matricula_element.evaluate("el => el.innerText")
                user_info["matricula"] = matricula_text.strip()
            
            return user_info
            
        except Exception as e:
            logger.warning(f"Erro ao extrair informações do usuário: {e}")
            return {}
    
    def is_logged_in(self) -> bool:
        """Verifica se está logado"""
        return self.is_logged_in_flag
    
    async def navigate_to_section(self, section: str) -> Dict[str, Any]:
        """Navega para uma seção específica do SIGAA"""
        try:
            if not self.current_page:
                return {"success": False, "error": "Nenhuma sessão ativa"}
            
            section_map = {
                "notas": ["Consultar Notas", "notas", "grades"],
                "historico": ["Histórico", "histórico acadêmico", "transcript"],
                "matricula": ["Matrícula", "enrollment", "disciplinas"],
                "comprovantes": ["Comprovantes", "documentos", "certificates"],
                "atestados": ["Atestados", "atestado de matrícula"],
                "horario": ["Horário", "horário de aulas", "schedule"]
            }
            
            # Encontrar termos de busca para a seção
            search_terms = section_map.get(section.lower(), [section])
            
            # Tentar encontrar link/menu para a seção
            for term in search_terms:
                try:
                    element = await self.current_page.get_element_by_prompt(
                        f"link ou menu para {term}", 
                        llm=self.llm
                    )
                    if element:
                        await element.click()
                        await asyncio.sleep(3)
                        
                        current_url = await self.current_page.evaluate("() => window.location.href")
                        return {
                            "success": True,
                            "message": f"Navegado para seção: {section}",
                            "section": section,
                            "current_url": current_url
                        }
                except Exception as e:
                    logger.warning(f"Erro tentando navegar para {term}: {e}")
                    continue
            
            return {
                "success": False,
                "error": f"Não foi possível encontrar a seção: {section}",
                "section": section
            }
            
        except Exception as e:
            logger.error(f"Erro na navegação: {e}")
            return {"success": False, "error": str(e), "section": section}
    
    async def extract_grades(self) -> Dict[str, Any]:
        """Extrai notas das disciplinas"""
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
        """Baixa documentos do SIGAA"""
        try:
            # Mapear tipos de documento para termos de busca
            doc_map = {
                "historico_academico": ["histórico acadêmico", "histórico escolar", "transcript"],
                "comprovante_matricula": ["comprovante de matrícula", "atestado de matrícula"],
                "diploma": ["diploma", "certificado"],
                "ira": ["índice de rendimento", "IRA", "coeficiente"]
            }
            
            search_terms = doc_map.get(doc_type, [doc_type])
            
            # Procurar link para gerar/baixar documento
            for term in search_terms:
                try:
                    download_link = await self.current_page.get_element_by_prompt(
                        f"link para gerar ou baixar {term}",
                        llm=self.llm
                    )
                    
                    if download_link:
                        # Configurar download
                        download_path = Path(os.getenv("DOWNLOAD_PATH", "/app/data/downloads"))
                        download_path.mkdir(parents=True, exist_ok=True)
                        
                        filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                        full_path = download_path / filename
                        
                        # Clicar no link de download
                        await download_link.click()
                        await asyncio.sleep(5)  # Aguardar download
                        
                        # Verificar se arquivo foi baixado
                        if full_path.exists():
                            return {
                                "success": True,
                                "document_type": doc_type,
                                "file_path": str(full_path),
                                "filename": filename
                            }
                        else:
                            # Procurar na pasta de downloads padrão
                            downloads_dir = Path("/app/data/downloads")
                            latest_file = None
                            latest_time = 0
                            
                            for file in downloads_dir.glob(f"*.{format}"):
                                if file.stat().st_mtime > latest_time:
                                    latest_time = file.stat().st_mtime
                                    latest_file = file
                            
                            if latest_file and (datetime.now().timestamp() - latest_time) < 60:  # Arquivo recente
                                new_name = download_path / filename
                                latest_file.rename(new_name)
                                
                                return {
                                    "success": True,
                                    "document_type": doc_type,
                                    "file_path": str(new_name),
                                    "filename": filename
                                }
                        
                        break
                        
                except Exception as e:
                    logger.warning(f"Erro tentando baixar com termo {term}: {e}")
                    continue
            
            return {
                "success": False,
                "error": f"Não foi possível baixar documento: {doc_type}",
                "document_type": doc_type
            }
            
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return {"success": False, "error": str(e), "document_type": doc_type}
    
    async def execute_custom_task(self, task: str, max_steps: int = 20, return_data: bool = True) -> Dict[str, Any]:
        """Executa tarefa personalizada usando IA"""
        try:
            if not self.current_page:
                return {"success": False, "error": "Nenhuma sessão ativa"}
            
            # Criar agente para executar a tarefa
            agent = Agent(
                task=f"No SIGAA da UFPA: {task}",
                llm=self.llm,
                browser=self.browser,
                max_steps=max_steps
            )
            
            result = await agent.run()
            
            extracted_data = None
            if return_data:
                try:
                    extracted_data = await self.current_page.extract_content(
                        "Extrair dados relevantes da página atual após executar a tarefa",
                        dict,
                        llm=self.llm
                    )
                except:
                    pass
            
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
        """Obtém notificações do SIGAA"""
        try:
            # Procurar por área de notificações
            notification_element = await self.current_page.get_element_by_prompt(
                "área de notificações, avisos ou mensagens",
                llm=self.llm
            )
            
            if notification_element:
                notifications = await self.current_page.extract_content(
                    "Extrair todas as notificações, avisos e mensagens importantes",
                    list,
                    llm=self.llm
                )
            else:
                notifications = []
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter notificações: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_class_schedule(self) -> Dict[str, Any]:
        """Obtém horário de aulas"""
        try:
            # Navegar para área de horários se necessário
            schedule_link = await self.current_page.get_element_by_prompt(
                "link para horário de aulas ou cronograma",
                llm=self.llm
            )
            
            if schedule_link:
                await schedule_link.click()
                await asyncio.sleep(3)
            
            # Extrair horário
            schedule_data = await self.current_page.extract_content(
                "Extrair horário de aulas completo com disciplinas, horários, professores e salas",
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
        """Captura screenshot da página atual"""
        try:
            if not self.current_page:
                return ""
            
            screenshot_dir = Path("/app/data/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = screenshot_dir / filename
            
            screenshot_data = await self.current_page.screenshot()
            
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_data)
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {e}")
            return ""
    
    async def check_status(self) -> Dict[str, Any]:
        """Verifica status da sessão"""
        try:
            if not self.browser:
                return {
                    "success": False,
                    "logged_in": False,
                    "error": "Browser não inicializado"
                }
            
            status = {
                "success": True,
                "logged_in": self.is_logged_in_flag,
                "user_info": self.user_info,
                "browser_active": True
            }
            
            if self.current_page:
                try:
                    current_url = await self.current_page.evaluate("() => window.location.href")
                    status["current_url"] = current_url
                    status["on_sigaa"] = "sigaa.ufpa.br" in current_url
                except:
                    pass
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            return {"success": False, "error": str(e), "logged_in": False}
    
    async def logout(self) -> Dict[str, Any]:
        """Faz logout do SIGAA"""
        try:
            if not self.current_page:
                self.is_logged_in_flag = False
                return {"success": True, "message": "Nenhuma sessão ativa"}
            
            # Procurar link de logout
            logout_link = await self.current_page.get_element_by_prompt(
                "link de logout ou sair",
                llm=self.llm
            )
            
            if logout_link:
                await logout_link.click()
                await asyncio.sleep(3)
            
            self.is_logged_in_flag = False
            self.user_info = {}
            
            return {
                "success": True,
                "message": "Logout realizado com sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro no logout: {e}")
            self.is_logged_in_flag = False
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Limpa recursos do actor"""
        try:
            if self.browser:
                await self.browser.stop()
                self.browser = None
            
            self.current_page = None
            self.is_logged_in_flag = False
            self.user_info = {}
            
            logger.info("SIGAA Actor limpo com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na limpeza do SIGAA Actor: {e}")