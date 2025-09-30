# Servidor MCP para SIGAA UFPA com Browser-Use

Este projeto implementa um servidor MCP (Model Context Protocol) específico para automatizar o acesso ao SIGAA da UFPA usando browser-use com agents para autenticação automática.

## 📋 Estrutura do Projeto

```
sigaa-ufpa-mcp/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── .env.exemple
├── server.py
├── mcp.json
├── fastmcp.json
└── data/
    └── downloads/
```

## 🚀 Como Usar com Docker

Este projeto é otimizado para execução com Docker, oferecendo dois modos principais: `http` (serviço web) e `stdio` (para clientes MCP).

### 1. Pré-requisitos

- Docker e Docker Compose instalados.
- Credenciais de acesso ao SIGAA e uma chave de API para o Google Gemini.

### 2. Configuração

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/sigaa-ufpa-mcp.git
    cd sigaa-ufpa-mcp
    ```

2. **Configure as Variáveis de Ambiente:**
    Copie o arquivo de exemplo e preencha com suas credenciais.
    ```bash
    cp .env.exemple .env
    nano .env
    ```
    Preencha `SIGAA_USERNAME`, `SIGAA_PASSWORD` e `GOOGLE_API_KEY`.

### 3. Construindo a Imagem Docker

Antes de executar o contêiner, construa a imagem com uma tag específica. Isso só precisa ser feito uma vez ou sempre que o `Dockerfile` for alterado.

```bash
docker build -t sigaa-ufpa-mcp .
```

### 4. Modos de Execução

#### a) Modo Serviço Web (via Docker Compose)

```json
{
  "mcp_servers": {
    "sigaa-ufpa": {
      "name": "SIGAA UFPA MCP Server (Docker Compose)",
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp",
      "disabled": false,
      "alwaysAllow": [
        "reiniciar_sessao",
        "baixar_historico_escolar",
        "exportar_horarios_csv",
        "listar_avisos_turmas",
        "listar_disciplinas_ofertadas"
      ],
      "env": {
        "GOOGLE_API_KEY": "COLE_SUA_API_KEY_DO_GEMINI_AQUI",
        "SIGAA_USERNAME": "COLE_SEU_USUARIO_SIGAA_AQUI",
        "SIGAA_PASSWORD": "COLE_SUA_SENHA_SIGAA_AQUI",
        "MCP_TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO",
        "CHROME_HEADLESS": "true"
      },
      "timeout": 1800
    }
  }
}
```

Ideal para manter o servidor rodando como um serviço de fundo, com reinicialização automática e acesso via VNC.

```bash
docker-compose up -d
```

- O servidor estará acessível na porta `8000`.
- Você pode monitorar os logs com `docker-compose logs -f`.
- A interface gráfica pode ser acessada via VNC no endereço `localhost:5900` (senha padrão: `browser-use`).
- A interface gráfica também pode ser acessada via noVNC no navegador em `http://localhost:6080/vnc.html?autoconnect=1&resize=scale&password=browser-use`.

### Acessando o Servidor VNC

Para visualizar a interface gráfica do navegador automatizado:

1. **Acesso via noVNC (navegador):**
   - Acesse http://localhost:6080/vnc.html?autoconnect=1&resize=scale&password=browser-use

2. **Acesso via cliente VNC:**
   - Instale um cliente VNC em seu computador (como TigerVNC Viewer, RealVNC, UltraVNC, ou qualquer outro cliente VNC de sua preferência)
   - Conecte-se ao servidor VNC usando:
     - Endereço: `localhost:5900` (já que a porta 5900 do contêiner está mapeada para a porta 5900 do host)
     - Senha: `browser-use` (padrão definido no Dockerfile)

3. **Visualize as automações** em execução no navegador que está sendo controlado pelo sistema de automação do SIGAA.

O acesso VNC/noVNC é especialmente útil para:
- Monitorar visualmente as automações em execução
- Depurar problemas de navegação
- Verificar visualmente se as tarefas estão sendo executadas corretamente

#### b) Modo Cliente MCP (via `docker run`)

Este modo é para integrar o servidor a um cliente MCP, como o Claude Desktop, que se comunica via `stdio`.

Adicione a seguinte configuração ao seu cliente MCP. Este método é o mais recomendado, pois centraliza todas as configurações no cliente e não depende de um arquivo `.env`.

```json
{
  "mcp_servers": {
        "sigaa-ufpa-docker": {
      "name": "SIGAA UFPA MCP Server",
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-p",
        "8000:8000",
        "-p",
        "5900:5900",
        "-p",
        "6080:6080",
        "sigaa-ufpa-mcp:latest"
      ],
      "env": {
        "GOOGLE_API_KEY": "COLE_SUA_API_KEY_DO_GEMINI_AQUI",
        "SIGAA_USERNAME": "COLE_SEU_USUARIO_SIGAA_AQUI",
        "SIGAA_PASSWORD": "COLE_SUA_SENHA_SIGAA_AQUI",
        "MCP_TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO",
        "CHROME_HEADLESS": "true"
      },
      "alwaysAllow": [
        "reiniciar_sessao",
        "baixar_historico_escolar",
        "exportar_horarios_csv",
        "listar_avisos_turmas",
        "listar_disciplinas_ofertadas"
      ],
      "timeout": 1800,
      "disabled": false
    }
  }
}
```

**Explicação da configuração:**

- `"command": "docker"` e `"args": [...]`: Executa o contêiner a partir da imagem `sigaa-ufpa-mcp` que você construiu.
  - `--rm`: Remove o contêiner automaticamente após o uso.
  - `-i`: Mantém o `STDIN` aberto, essencial para a comunicação `stdio`.
- `"env"`: Passa todas as credenciais e chaves de API diretamente para o ambiente do contêiner. O servidor lerá essas variáveis para funcionar.
- `"type": "stdio"`: Informa ao cliente para se comunicar via entrada/saída padrão. O servidor no contêiner já inicia neste modo por padrão.

### 3. Exemplo de Uso

Após configurar, você pode usar no Claude:

```
"Faça login no SIGAA e me traga minhas notas do semestre atual"

"Baixe meu histórico acadêmico em PDF"

"Verifique se tenho alguma notificação no SIGAA"

"Extraia meu horário de aulas desta semana"
```

## 📋 Ferramentas Disponíveis

1. **reiniciar_sessao** - Reinicia a sessão do navegador e realiza o login novamente.
2. **baixar_historico_escolar** - Baixa o histórico escolar completo do aluno em PDF e retorna o caminho do arquivo salvo.
3. **listar_disciplinas_ofertadas** - Lista todas as disciplinas ofertadas no semestre atual para o curso e turno informados.
4. **exportar_horarios_csv** - Exporta todos os horários de aula do aluno no semestre atual em formato CSV.
5. **listar_avisos_turmas** - Lista todos os avisos/comunicados recentes das turmas em que o aluno está matriculado.

## 🔒 Segurança

- **Credenciais**: Armazenadas apenas em variáveis de ambiente
- **Browser Isolado**: Executa em container Docker separado
- **Logs**: Não registram senhas ou dados sensíveis
- **Cleanup**: Sessões são limpas automaticamente

## 🛠️ Desenvolvimento

Para desenvolvimento local:

```bash
# Instalar dependências com uv
uv sync --frozen

# Executar em modo desenvolvimento
uv run server.py

# Logs em tempo real
tail -f logs/server.log
```

## ⚠️ Importante

- Este servidor é específico para o SIGAA da UFPA
- Requer credenciais válidas da universidade
- Respeite os termos de uso do SIGAA
- Use apenas para automação pessoal legítima

## 📞 Suporte

Para problemas ou melhorias:

1. Verifique os logs em `/app/logs/server.log`
2. Confirme que as credenciais estão corretas
3. Teste a conectividade com o SIGAA
4. Verifique se a `GOOGLE_API_KEY` está funcionando