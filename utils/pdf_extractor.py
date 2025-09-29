import pypdf
import logging
from typing import Optional
from pathlib import Path
import aiofiles

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Classe para extrair texto de arquivos PDF"""
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extrai texto de um arquivo PDF"""
        try:
            path = Path(pdf_path)
            if not path.exists():
                logger.error(f"Arquivo PDF não encontrado: {pdf_path}")
                return None
            
            text_content = ""
            
            async with aiofiles.open(pdf_path, 'rb') as file:
                pdf_content = await file.read()
                
                # Usar pypdf para extrair texto
                from io import BytesIO
                pdf_file = pypdf.PdfReader(BytesIO(pdf_content))
                
                for page_num in range(len(pdf_file.pages)):
                    page = pdf_file.pages[page_num]
                    text_content += page.extract_text() + "\n"
            
            # Limpar texto extraído
            cleaned_text = self._clean_extracted_text(text_content)
            
            logger.info(f"Texto extraído com sucesso do PDF: {pdf_path}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF {pdf_path}: {e}")
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """Limpa e formata o texto extraído"""
        try:
            # Remover quebras de linha excessivas
            cleaned = text.replace('\n\n\n', '\n\n')
            
            # Remover espaços extras
            lines = [line.strip() for line in cleaned.split('\n')]
            cleaned = '\n'.join(line for line in lines if line)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Erro ao limpar texto: {e}")
            return text