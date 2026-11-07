"""Pydantic v2 data schemas for SIGAA UFPA MCP tools, apps, and parsers."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class VinculoItem(BaseModel):
    """Representa um vínculo institucional do estudante no SIGAA."""

    indice: int = Field(description="Índice posicional na tabela de vínculos")
    identificador: str = Field(default="", description="Identificador ou texto do link de seleção")
    matricula: str = Field(default="", description="Número de matrícula associado ao vínculo")
    curso: str = Field(default="", description="Curso ou unidade do vínculo")
    nivel: str = Field(default="", description="Nível de ensino (Graduação, Pós, etc.)")
    situacao: str = Field(default="", description="Situação cadastral (ATIVO, CONCLUÍDO, etc.)")
    ativo: bool = Field(default=True, description="Indica se o vínculo está ativo")


class IndiceAcademico(BaseModel):
    """Índice oficial do discente no SIGAA UFPA (CRG, MC, MCN, IEA, etc.)."""

    sigla: str
    nome: str = ""
    valor: str


class PerfilDiscenteResumo(BaseModel):
    """Dados consolidados do perfil acadêmico no Portal do Discente."""

    nome: str = ""
    matricula: str = ""
    curso: str = ""
    nivel: str = ""
    status: str = ""
    email: str = ""
    entrada: str = ""
    semestre_atual: str = ""
    foto_url: str = ""
    descricao_pessoal: str = ""
    indices: dict[str, str] = Field(default_factory=dict)


class SlotHorario(BaseModel):
    """Um bloco individual de 50 minutos decodificado a partir do código de horário da UFPA."""

    dia_codigo: str
    dia_nome: str
    turno_codigo: str
    turno_nome: str
    slot_numero: int
    hora_inicio: str
    hora_fim: str
    codigo_original: str


class TurmaMatriculada(BaseModel):
    """Turma em que o discente está matriculado no período vigente."""

    codigo: str = ""
    disciplina: str
    turma: str = ""
    docente: str = ""
    local: str = ""
    horario_bruto: str = ""
    periodo_datas: str = ""
    semestre: str = ""
    slots_decodificados: list[SlotHorario] = Field(default_factory=list)


class ChoqueHorario(BaseModel):
    """Conflito detectado entre duas ou mais disciplinas no mesmo dia/turno/slot."""

    dia_nome: str
    turno_nome: str
    slot_numero: int
    faixa_horaria: str
    disciplinas: list[str]


class NotaDisciplina(BaseModel):
    """Linha de boletim extraída do relatório 'Consultar Minhas Notas'."""

    semestre: str = ""
    codigo: str = ""
    disciplina: str
    unidade_1: str = "-"
    unidade_2: str = "-"
    unidade_3: str = "-"
    recuperacao: str = "-"
    resultado: str = "-"
    faltas: str = "0"
    situacao: str = "-"


class CargaHorariaItem(BaseModel):
    """Quadro de carga horária (Exigido / Integralizado / Pendente) do Histórico Escolar."""

    exigido: int = 0
    integralizado: int = 0
    pendente: int = 0


class HistoricoResumo(BaseModel):
    """Resumo estruturado extraído do PDF oficial do Histórico Escolar."""

    nome: str = ""
    matricula: str = ""
    curso: str = ""
    status: str = ""
    crg: str = ""
    mc: str = ""
    iea: str = ""
    carga_horaria_total: CargaHorariaItem = Field(default_factory=CargaHorariaItem)
    carga_horaria_obrigatoria: CargaHorariaItem = Field(default_factory=CargaHorariaItem)
    carga_horaria_optativa: CargaHorariaItem = Field(default_factory=CargaHorariaItem)
    carga_horaria_complementar: CargaHorariaItem = Field(default_factory=CargaHorariaItem)
    componentes_cursados_ou_cursando: int = 0
    obrigatorias_pendentes_qtd: int = 0
    obrigatorias_pendentes_amostra: list[str] = Field(default_factory=list)
    arquivo_pdf: str = ""
    drive_link: Optional[str] = None


class AtestadoResumo(BaseModel):
    """Resumo estruturado do Atestado de Matrícula emitido pelo SIGAA."""

    nome: str = ""
    matricula: str = ""
    curso: str = ""
    semestre: str = ""
    codigo_verificacao: str = ""
    turmas: list[TurmaMatriculada] = Field(default_factory=list)
    choques_horario: list[ChoqueHorario] = Field(default_factory=list)
    arquivo_pdf: str = ""
    drive_link: Optional[str] = None


class HorariosExportadosResumo(BaseModel):
    """Resultado da exportação de grade horária semanal."""

    semestre: str = ""
    total_turmas: int = 0
    total_slots_semanais: int = 0
    arquivo_csv: str = ""
    drive_link: Optional[str] = None
    turmas: list[TurmaMatriculada] = Field(default_factory=list)
    choques_horario: list[ChoqueHorario] = Field(default_factory=list)


class AvisoTurma(BaseModel):
    """Notícia ou comunicado publicado pelos docentes nas turmas virtuais."""

    disciplina: str
    semestre: str = ""
    data: str = ""
    titulo: str
    conteudo: str = ""
    origem: str = "portal"


class AtividadePendente(BaseModel):
    """Tarefa, questionário ou avaliação identificada nas turmas virtuais (AVA)."""

    disciplina: str
    tipo: str = "Tarefa"
    titulo: str
    prazo: str = ""
    situacao: str = ""
    concluida: bool = False


class DisciplinaOfertada(BaseModel):
    """Turma ofertada encontrada na consulta de turmas da UFPA."""

    codigo: str = ""
    disciplina: str
    turma: str = ""
    docente: str = ""
    horario_bruto: str = ""
    local: str = ""
    ano_periodo: str = ""
    vagas_ofertadas: str = ""
    vagas_ocupadas: str = ""
    tem_choque_com_grade: bool = False
    detalhes_choque: list[str] = Field(default_factory=list)


class ResultadoTrocaPerfil(BaseModel):
    """Retorno da operação de atualização ou simulação de foto/perfil discente."""

    sucesso: bool
    modo_simulacao: bool = False
    mensagem: str
    origem_imagem: str = ""
    arquivo_validado: str = ""
    cpf_detectado_automaticamente: bool = False
    data_nascimento_detectada_automaticamente: bool = False
    descricao_aplicada: Optional[str] = None


class EstadoSessao(BaseModel):
    """Estado atual da sessão autenticada no SIGAA UFPA."""

    autenticado: bool = False
    usuario: str = ""
    nome_discente: str = ""
    matricula_ativa: str = ""
    curso_ativo: str = ""
    semestre_atual: str = ""
    modo_persistencia: str = "volatil_ram"
    tem_credenciais_env: bool = False
    tem_sessao_salva_disco: bool = False
    multiplos_vinculos: bool = False
    aguardando_escolha_vinculo: bool = False
    vinculos: list[VinculoItem] = Field(default_factory=list)
    login_url: str = ""
    mensagem: str = ""
