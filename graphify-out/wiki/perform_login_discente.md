# perform_login_discente()

> **God Node** ? 5 conex?es ? Fonte: `server.py`
> **Comunidade:** [Automa??o Web do SIGAA](Automacao_Web_do_SIGAA.md)

## Descri??o Arquitetural
Injeta credenciais de autentica??o (`SIGAA_USERNAME` e `SIGAA_PASSWORD`) nos campos de input do formul?rio JSF do SIGAA e aciona o submit.

* **Valida??es:** Verifica rigorosamente a presen?a dos n?s de input antes de invocar `.fill()`.
* **Transi??o de Estado:** N?o encerra sua execu??o at? que o clique no elemento de menu `.menus` seja conclu?do com ?xito.

---
*Parte da Wiki de Conhecimento do Graphify. Veja o [?ndice](index.md).*
