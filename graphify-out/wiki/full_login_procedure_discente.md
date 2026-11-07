# full_login_procedure_discente()

> **God Node** ? 9 conex?es ? Fonte: `server.py`
> **Comunidade:** [Servi?os do Portal Discente SIGAA](Servicos_do_Portal_Discente_SIGAA.md)

## Descri??o Arquitetural
Fun??o ass?ncrona respons?vel por orquestrar a inicializa??o do navegador headless/Chromium, navegar at? a URL base do SIGAA (`https://sigaa.ufpa.br`), invocar `perform_login_discente()` e atualizar o dicion?rio de status global `startup_status`.

## Comportamento Operacional
1. Inicializa o `browser.start()` se a sess?o estiver fechada.
2. Abre a p?gina inicial e submete as credenciais do discente.
3. Altera as flags globais:
   * `startup_status["success"] = True`
   * `startup_status["logged_in"] = True`
4. Em caso de falha de conex?o ou credenciais incorretas, captura a exce??o, registra log cr?tico no Loguru e marca `startup_status["logged_in"] = False`.

---
*Parte da Wiki de Conhecimento do Graphify. Veja o [?ndice](index.md).*
