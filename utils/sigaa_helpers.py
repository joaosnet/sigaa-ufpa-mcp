import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SIGAAHelpers:
    """Classe com utilitários para trabalhar com dados do SIGAA"""
    
    @staticmethod
    def parse_grade(grade_text: str) -> Optional[float]:
        """Converte texto de nota para número"""
        try:
            # Remover espaços e caracteres especiais
            clean_text = re.sub(r'[^\d,.]', '', grade_text)
            
            # Substituir vírgula por ponto se necessário
            if ',' in clean_text:
                clean_text = clean_text.replace(',', '.')
            
            return float(clean_text)
        except:
            return None
    
    @staticmethod
    def parse_semester(semester_text: str) -> Dict[str, Any]:
        """Parseia informações de semestre"""
        try:
            # Padrão: 2024.1, 2024.2, etc.
            match = re.search(r'(\d{4})\.(\d)', semester_text)
            if match:
                year = int(match.group(1))
                period = int(match.group(2))
                return {
                    "year": year,
                    "period": period,
                    "full": f"{year}.{period}"
                }
        except:
            pass
        
        return {"full": semester_text}
    
    @staticmethod
    def calculate_gpa(grades: List[Dict]) -> Optional[float]:
        """Calcula coeficiente de rendimento (CR)"""
        try:
            total_points = 0
            total_credits = 0
            
            for subject in grades:
                grade = SIGAAHelpers.parse_grade(subject.get('nota', '0'))
                credits = subject.get('creditos', 0)
                
                if grade is not None and credits > 0:
                    total_points += grade * credits
                    total_credits += credits
            
            if total_credits > 0:
                return round(total_points / total_credits, 2)
                
        except Exception as e:
            logger.error(f"Erro ao calcular CR: {e}")
        
        return None
    
    @staticmethod
    def format_schedule(schedule_data: Dict) -> str:
        """Formata horário de aulas em texto legível"""
        try:
            if not schedule_data:
                return "Nenhum horário encontrado"
            
            formatted = "📅 **HORÁRIO DE AULAS**\n\n"
            
            # Organizar por dia da semana
            days_order = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
            
            for day in days_order:
                day_classes = []
                
                # Procurar aulas deste dia
                for item in schedule_data.get('classes', []):
                    if day.lower() in item.get('dia', '').lower():
                        day_classes.append(item)
                
                if day_classes:
                    formatted += f"**{day}:**\n"
                    for cls in day_classes:
                        formatted += f"  • {cls.get('disciplina', 'N/A')} - {cls.get('horario', 'N/A')} - Sala: {cls.get('sala', 'N/A')}\n"
                    formatted += "\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Erro ao formatar horário: {e}")
            return str(schedule_data)
    
    @staticmethod
    def extract_student_info(page_content: str) -> Dict[str, Any]:
        """Extrai informações do estudante do conteúdo da página"""
        info = {}
        
        try:
            # Extrair matrícula
            matricula_match = re.search(r'Matrícula[:\s]*(\d+)', page_content, re.IGNORECASE)
            if matricula_match:
                info['matricula'] = matricula_match.group(1)
            
            # Extrair nome
            name_patterns = [
                r'Nome[:\s]*([A-ZÁÀÃÂÄÇÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÑ][a-záàãâäçéèêëíìîïóòôõöúùûüñ\s]+)',
                r'Aluno[:\s]*([A-ZÁÀÃÂÄÇÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÑ][a-záàãâäçéèêëíìîïóòôõöúùûüñ\s]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, page_content)
                if match:
                    info['nome'] = match.group(1).strip()
                    break
            
            # Extrair curso
            curso_match = re.search(r'Curso[:\s]*([A-ZÁÀÃÂÄÇÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÑ][a-záàãâäçéèêëíìîïóòôõöúùûüñ\s\-]+)', page_content, re.IGNORECASE)
            if curso_match:
                info['curso'] = curso_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações do estudante: {e}")
        
        return info
    
    @staticmethod
    def validate_document_type(doc_type: str) -> bool:
        """Valida se o tipo de documento é suportado"""
        valid_types = [
            'historico_academico',
            'comprovante_matricula', 
            'atestado_matricula',
            'diploma',
            'certificado',
            'ira',
            'comprovante_conclusao'
        ]
        
        return doc_type.lower() in valid_types
    
    @staticmethod
    def format_transcript(transcript_data: List[Dict]) -> str:
        """Formata histórico acadêmico em texto legível"""
        try:
            if not transcript_data:
                return "Nenhum dado de histórico encontrado"
            
            formatted = "📋 **HISTÓRICO ACADÊMICO**\n\n"
            
            # Agrupar por período
            periods = {}
            for subject in transcript_data:
                period = subject.get('periodo', 'Não informado')
                if period not in periods:
                    periods[period] = []
                periods[period].append(subject)
            
            # Ordenar períodos
            sorted_periods = sorted(periods.keys())
            
            total_credits = 0
            completed_credits = 0
            
            for period in sorted_periods:
                formatted += f"**{period}:**\n"
                
                for subject in periods[period]:
                    name = subject.get('nome', 'N/A')
                    code = subject.get('codigo', '')
                    credits = subject.get('creditos', 0)
                    grade = subject.get('nota', 'N/A')
                    status = subject.get('situacao', 'N/A')
                    
                    formatted += f"  • {code} - {name}\n"
                    formatted += f"    Créditos: {credits} | Nota: {grade} | Situação: {status}\n"
                    
                    total_credits += credits
                    if status.lower() in ['aprovado', 'aprovada']:
                        completed_credits += credits
                
                formatted += "\n"
            
            # Resumo
            formatted += "**RESUMO:**\n"
            formatted += f"• Total de créditos: {total_credits}\n"
            formatted += f"• Créditos concluídos: {completed_credits}\n"
            
            if total_credits > 0:
                progress = (completed_credits / total_credits) * 100
                formatted += f"• Progresso: {progress:.1f}%\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Erro ao formatar histórico: {e}")
            return str(transcript_data)