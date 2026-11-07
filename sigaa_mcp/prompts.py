"""FastMCP 4.1 Prompts for recurring UFPA academic workflows."""

from __future__ import annotations

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register the 3 structured academic prompts on the FastMCP server."""

    @mcp.prompt(
        name="planejar_matricula_semestre",
        description="Cruza histórico escolar, disciplinas pendentes e turmas ofertadas sem choque de horário.",
        tags={"academico", "planejamento"},
    )
    def planejar_matricula_semestre(curso: str, turno_preferido: str = "") -> str:
        turno_info = f" priorizando o turno '{turno_preferido}'" if turno_preferido else ""
        return (
            f"Atue como orientador acadêmico da UFPA para o curso '{curso}'{turno_info}.\n"
            "Siga rigorosamente estas etapas usando as ferramentas do servidor `sigaa-ufpa`:\n"
            "1. Chame `baixar_historico_escolar` para verificar CRG, carga horária pendente e componentes obrigatórios pendentes.\n"
            "2. Chame `exportar_horarios_csv` para mapear os slots já ocupados na grade atual.\n"
            f"3. Chame `listar_disciplinas_ofertadas(curso='{curso}', turno='{turno_preferido}')` para identificar turmas ofertadas sem choque de horário (`tem_choque_com_grade=False`).\n"
            "4. Apresente uma recomendação objetiva de matrícula priorizando obrigatórias pendentes, equilíbrio de carga horária e zero conflitos."
        )

    @mcp.prompt(
        name="briefing_semana_academica",
        description="Consolida avisos recentes dos docentes, atividades/provas pendentes e situação de faltas.",
        tags={"academico", "rotina"},
    )
    def briefing_semana_academica() -> str:
        return (
            "Gere um briefing executivo da minha semana acadêmica na UFPA:\n"
            "1. Chame `listar_atividades_pendentes` para levantar tarefas, questionários e avaliações abertas.\n"
            "2. Chame `listar_avisos_turmas` para verificar comunicados recentes dos professores.\n"
            "3. Chame `consultar_notas_frequencia` para conferir conceitos parciais e número de faltas nas turmas matriculadas.\n"
            "4. Organize a resposta por prioridade de prazo, destacando qualquer disciplina com atenção em frequência."
        )

    @mcp.prompt(
        name="auditar_integralizacao_curricular",
        description="Analisa progresso de integralização curricular, índices oficiais (CRG/MC/IEA) e pendências para formatura.",
        tags={"academico", "formatura"},
    )
    def auditar_integralizacao_curricular() -> str:
        return (
            "Realize uma auditoria completa da minha integralização curricular no SIGAA UFPA:\n"
            "1. Execute `baixar_historico_escolar` e `emitir_atestado_matricula`.\n"
            "2. Calcule o percentual concluído da carga horária exigida e liste todos os componentes obrigatórios ainda pendentes (incluindo ENADE, TCC ou Estágio, se houver).\n"
            "3. Compare as turmas atualmente matriculadas no atestado com as pendências restantes e estime o horizonte de conclusão do curso."
        )
