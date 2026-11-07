# Servi?os do Portal Discente SIGAA

> **Comunidade 4** ? 16 n?s ? Coes?o: 0.21 ? Fonte prim?ria: `server.py`

## Vis?o Geral
Esta comunidade encapsula as ferramentas MCP p?blicas fornecidas aos modelos de linguagem (Claude Desktop, etc.) para manipular a interface web do SIGAA como um discente autenticado.

---

## ??? Cat?logo de Ferramentas MCP

### 1. `baixar_historico_escolar()`
* **Objetivo:** Realiza o download do hist?rico acad?mico completo do discente em formato PDF.
* **Fluxo de A??o:**
  1. Acessa o Portal do Discente (`https://sigaa.ufpa.br/sigaa/portais/discente/discente.jsf`).
  2. Seleciona o per?odo letivo mais recente.
  3. Clica no menu **Ensino** -> **Emitir Hist?rico**.
  4. O download ? interceptado pelo Chromium e salvo no diret?rio tempor?rio/downloads mapeado.
* **Tratamento de Exce??es & Restri??es:**
  * Durante o per?odo de matr?cula e processamento institucional, o SIGAA bloqueia a emiss?o de hist?rico; a ferramenta intercepta a falha e registra aviso.

### 2. `listar_disciplinas_ofertadas(curso: str, turno: str)`
* **Objetivo:** Lista todas as turmas e mat?rias abertas no semestre atual para um curso universit?rio espec?fico.
* **Par?metros:**
  * `curso` (string, obrigat?rio): Nome ou sigla do curso (ex.: *"Engenharia da Computa??o/ITEC - Bel?m"*).
  * `turno` (string, opcional): Turno acad?mico (*"Matutino"*, *"Noturno"*, *"Integral"*).
* **Fluxo de A??o:**
  1. Entra em **Ensino** -> **Consultas Gerais** -> **Consultar Turma** (ou pela URL direta `/sigaa/public/turmas/listar.jsf`).
  2. Preenche os campos do formul?rio e aciona a busca.
  3. Extrai tabelas contendo c?digo da disciplina, turma, docentes, local e hor?rios.

### 3. `exportar_horarios_csv()`
* **Objetivo:** Exporta a grade hor?ria das turmas em que o aluno est? matriculado para formato CSV.
* **Fluxo de A??o:**
  1. Localiza a se??o *"Turmas do Semestre"* no Portal do Discente.
  2. Se necess?rio, emite o *Atestado de Matr?cula* (que abre em nova aba).
  3. Formata os hor?rios semanais estruturados em linhas CSV para importa??o em calend?rios ou planilhas.

### 4. `listar_avisos_turmas()`
* **Objetivo:** Varre todas as turmas do discente no semestre ativo e consolida notifica??es/not?cias recentes.
* **Fluxo de A??o:**
  1. Itera sobre cada link de turma presente no painel do discente.
  2. Navega at? a aba **Not?cias** do ambiente virtual da turma.
  3. Extrai t?tulo, data de publica??o, conte?do da mensagem e docente autor.

### 5. `trocar_imagem_perfil(drive_file_id: str, descricao: str)`
* **Objetivo:** Automatiza a troca de imagem do perfil do aluno no SIGAA atrav?s de um arquivo previamente armazenado no Google Drive.
* **Fluxo Multiagente de Alta Complexidade:**
  1. **Download do Drive:** Conecta ao `GoogleDriveService` e baixa o arquivo `drive_file_id` em Base64, gravando em arquivo tempor?rio local (`.jpg`).
  2. **Extra??o de Valida??o:** Acessa `Meus Dados Pessoais` no SIGAA e emprega um agente LLM para extrair CPF e Data de Nascimento (dados sens?veis exigidos pelo SIGAA para confirmar altera??o cadastral).
  3. **Envio da Foto:** Clica em *Atualizar Foto e Perfil*, faz upload do arquivo tempor?rio e altera a descri??o biogr?fica.
  4. **Confirma??o:** Um segundo agente valida a confirma??o de identidade com a senha do usu?rio e confirma o sucesso da opera??o.
  5. **Limpeza:** Remove os arquivos tempor?rios criados em disco via bloco `finally`.

### 6. `reiniciar_sessao()`
* **Objetivo:** Reinicia a inst?ncia do navegador, limpa cookies/sess?o e reexecuta o procedimento de login.
* **Disponibilidade:** Ativa quando executado em modo HTTP (`MCP_TRANSPORT=http`).

---

## ?? Rela??es com Outros M?dulos
* **[Automacao Web do SIGAA](Automacao_Web_do_SIGAA.md):** Utiliza as primitivas `esperar_elemento()` e `perform_login_discente()`.
* **[Integracao com Google Drive](Integracao_com_Google_Drive.md):** A ferramenta `trocar_imagem_perfil()` depende diretamente do download via Drive API.
* **[Configuracao de Implantacao FastMCP](Configuracao_de_Implantacao_FastMCP.md):** Registra todas as rotas e lifecycle callbacks.
