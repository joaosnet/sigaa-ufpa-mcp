# trocar_imagem_perfil()

> **God Node** ? 8 conex?es ? Fonte: `server.py`
> **Comunidade:** [Servi?os do Portal Discente SIGAA](Servicos_do_Portal_Discente_SIGAA.md)

## Descri??o Arquitetural
Esta ? a ferramenta de maior complexidade orquestral do servidor MCP. Ela conecta o reposit?rio de arquivos do Google Drive, a extra??o estruturada de dados sens?veis no SIGAA e a confirma??o em duas etapas exigida pela UFPA.

## Fluxo de Execu??o
```mermaid
sequenceDiagram
    participant Agent as LLM / MCP Client
    participant Tool as trocar_imagem_perfil()
    participant Drive as GoogleDriveService
    participant Browser as browser-use (Chromium)
    participant SIGAA as SIGAA UFPA Portal

    Agent->>Tool: drive_file_id, descricao
    Tool->>Drive: download_em_base64(drive_file_id)
    Drive-->>Tool: Bytes em Base64
    Tool->>Tool: Grava temp_image_path (.jpg)
    Tool->>Browser: Navega at? Meus Dados Pessoais
    Tool->>Browser: Extrai Data de Nascimento e CPF (Pydantic UserInfo)
    Tool->>Browser: Navega at? Atualizar Foto e Perfil
    Tool->>Browser: Agente 1: Faz upload da foto e altera descri??o
    Tool->>Browser: Agente 2: Confirma identidade com CPF e Senha
    Tool->>Tool: Remove arquivo tempor?rio (finally)
    Tool-->>Agent: Retorna status consolidado
```

---
*Parte da Wiki de Conhecimento do Graphify. Veja o [?ndice](index.md).*
