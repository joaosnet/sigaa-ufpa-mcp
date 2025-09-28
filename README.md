# Servidor MCP para SIGAA UFPA com Browser-Use

Este projeto implementa um servidor MCP (Model Context Protocol) específico para automatizar o acesso ao SIGAA da UFPA usando browser-use com actors para autenticação automática.

## 📋 Estrutura do Projeto

```
sigaa-ufpa-mcp/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── server.py
├── sigaa_actor.py
├── config/
│   ├── browser_config.py
│   └── mcp_config.py
├── utils/
│   ├── __init__.py
│   ├── sigaa_helpers.py
│   └── pdf_extractor.py
├── logs/
└── data/
    └── downloads/
```
## 🚀 Como Usar

### 1. Configuração Inicial

```bash
# Clone/crie o projeto
mkdir sigaa-ufpa-mcp && cd sigaa-ufpa-mcp

# Configure o arquivo .env com suas credenciais
cp .env.example .env
nano .env  # Edite com suas credenciais

# Execute com Docker
docker-compose up -d
```

### 2. Configuração para Claude Desktop

Adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sigaa-ufpa": {
      "command": "docker",
      "args": [
        "exec", "-i", "sigaa-ufpa-mcp",
        "python", "server.py"
      ],
      "env": {}
    }
  }
}
```

### 3. Exemplo de Uso

Após configurar, você pode usar no Claude:

```
"Faça login no SIGAA e me traga minhas notas do semestre atual"

"Baixe meu histórico acadêmico em PDF"

"Verifique se tenho alguma notificação no SIGAA"

"Extraia meu horário de aulas desta semana"
```

## 📋 Ferramentas Disponíveis

1. **sigaa_login** - Login automático no SIGAA
2. **sigaa_navigate_and_extract** - Navegar e extrair dados de seções
3. **sigaa_download_document** - Baixar documentos acadêmicos  
4. **sigaa_custom_task** - Executar tarefas personalizadas com IA
5. **sigaa_get_notifications** - Obter notificações e avisos
6. **sigaa_get_class_schedule** - Extrair horário de aulas
7. **sigaa_check_status** - Verificar status da sessão
8. **sigaa_logout** - Fazer logout

## 🔒 Segurança

- **Credenciais**: Armazenadas apenas em variáveis de ambiente
- **Browser Isolado**: Executa em container Docker separado
- **Logs**: Não registram senhas ou dados sensíveis
- **Cleanup**: Sessões são limpas automaticamente

## 🛠️ Desenvolvimento

Para desenvolvimento local:

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar em modo desenvolvimento
python server.py

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
4. Verifique se a API key do LLM está funcionando