# esperar_elemento()

> **God Node** ? 5 conex?es ? Fonte: `server.py`
> **Comunidade:** [Automa??o Web do SIGAA](Automacao_Web_do_SIGAA.md)

## Descri??o Arquitetural
Fun??o utilit?ria ass?ncrona com mecanismo de polling ativo para mitiga??o de lat?ncia do DOM no portal SIGAA da UFPA.

```python
async def esperar_elemento(page: Page, selector: str, timeout: float = 15.0, poll_interval: float = 0.5):
    ...
```

* **Problema Resolvido:** O SIGAA baseia-se em JavaServer Faces (JSF), que realiza atualiza??es parciais de tela via AJAX com tempos de resposta imprevis?veis.
* **Seguran?a:** Trata exce??es internas do browser-use durante momentos em que o elemento ainda n?o existe na ?rvore do documento, evitando travamentos no servidor MCP.

---
*Parte da Wiki de Conhecimento do Graphify. Veja o [?ndice](index.md).*
