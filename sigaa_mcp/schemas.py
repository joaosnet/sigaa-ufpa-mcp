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
    fonte_faltas: str = Field(
        default="boletim",
        description=(
            "Origem do campo 'faltas': 'boletim' = total consolidado lançado no relatório 'Minhas Notas' "
            "(pode estar defasado durante o semestre). A contagem mais atualizada fica no Mapa de "
            "Frequências da turma virtual (ver 'frequencia_turma')."
        ),
    )
    frequencia_turma: Optional["FrequenciaTurma"] = None


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
    semestre: str = ""
    tipo: str = "Tarefa"
    titulo: str
    prazo: str = ""
    situacao: str = ""
    concluida: bool = False


class MaterialTopico(BaseModel):
    """Material (arquivo, link, vídeo, tarefa...) publicado dentro de um tópico de aula."""

    nome: str
    tipo: str = ""
    descricao: str = ""


class TopicoAula(BaseModel):
    """Tópico de aula da página principal da turma virtual."""

    titulo: str
    periodo: str = ""
    conteudo: str = ""
    materiais: list[MaterialTopico] = Field(default_factory=list)


class ArquivoTurma(BaseModel):
    """Arquivo listado em 'Arquivos' da turma virtual."""

    titulo: str
    descricao: str = ""
    topico: str = ""


class ReferenciaTurma(BaseModel):
    """Referência bibliográfica/link listado em 'Referências' da turma virtual."""

    nome: str
    tipo: str = ""
    url: str = ""
    topico: str = ""


class ConteudoTurmaVirtual(BaseModel):
    """Conteúdo consolidado de uma turma virtual (AVA) do SIGAA."""

    semestre: str = ""
    codigo: str = ""
    disciplina: str = ""
    turma: str = ""
    ultima_noticia: Optional[AvisoTurma] = None
    topicos: list[TopicoAula] = Field(default_factory=list)
    noticias: list[AvisoTurma] = Field(default_factory=list)
    arquivos: list[ArquivoTurma] = Field(default_factory=list)
    referencias: list[ReferenciaTurma] = Field(default_factory=list)
    avaliacoes: list[AtividadePendente] = Field(default_factory=list)
    tarefas: list[AtividadePendente] = Field(default_factory=list)
    questionarios: list[AtividadePendente] = Field(default_factory=list)
    secoes_lidas: list[str] = Field(default_factory=list)
    erros: list[str] = Field(default_factory=list)


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


class RegistroFrequencia(BaseModel):
    """Uma aula lançada no Mapa de Frequências da turma virtual."""

    data: str
    situacao: str
    faltas: int = 0


class FrequenciaTurma(BaseModel):
    """Mapa de Frequências da turma virtual (fonte mais atualizada de faltas durante o semestre)."""

    fonte: str = "turma_virtual"
    semestre: str = ""
    codigo: str = ""
    disciplina: str = ""
    turma: str = ""
    presencas: int = 0
    aulas_ministradas: int = 0
    faltas: int = 0
    percentual_frequencia_ministradas: str = ""
    aulas_carga_horaria: int = 0
    percentual_frequencia_ch: str = ""
    limite_faltas: int = 0
    faltas_restantes: int = 0
    em_risco: bool = False
    registros: list[RegistroFrequencia] = Field(default_factory=list)
    erro: str = ""


class TurmaHistorica(BaseModel):
    """Linha de 'Todas as Turmas Virtuais' (portais/discente/turmas.jsf)."""

    semestre: str = ""
    codigo: str = ""
    disciplina: str
    turma: str = ""
    carga_horaria: str = ""
    horario_bruto: str = ""
    front_end_id: str = ""


class SemestreDisciplinaComparada(BaseModel):
    """Uma disciplina em um semestre específico: oferta da UFPA + seu resultado, se cursou."""

    semestre: str
    cursada: bool = False
    resultado_aluno: Optional[NotaDisciplina] = None
    turmas_ofertadas: list[DisciplinaOfertada] = Field(default_factory=list)
    docentes: list[str] = Field(default_factory=list)
    horarios: list[str] = Field(default_factory=list)
    vagas_ofertadas: int = 0
    vagas_ocupadas: int = 0
    taxa_ocupacao: Optional[float] = None
    erro: str = ""


class ComparativoDisciplina(BaseModel):
    """Comparação de um mesmo componente curricular ao longo de vários semestres."""

    consulta: str
    codigo: str = ""
    disciplina: str = ""
    semestres: list[SemestreDisciplinaComparada] = Field(default_factory=list)
    semestres_cursados: list[str] = Field(default_factory=list)
    docentes_distintos: list[str] = Field(default_factory=list)
    observacoes: list[str] = Field(default_factory=list)


NotaDisciplina.model_rebuild()
