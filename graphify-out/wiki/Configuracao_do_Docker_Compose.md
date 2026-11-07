# Configura??o do Docker Compose

> **Comunidade 5** ? 13 n?s ? Coes?o: 0.15 ? Fonte prim?ria: `docker-compose.yml`

## Vis?o Geral
Gerencia a orquestra??o do cont?iner `sigaa-mcp-server`, seus volumes persistentes, isolamento de rede e hot-reload durante desenvolvimento.

---

## ?? Par?metros de Orquestra??o
* **Nome do Servi?o:** `sigaa-mcp-server`
* **Volumes Persistentes:**
  * `sigaa-data`: Persiste arquivos baixados, hist?ricos e sess?es.
  * Mapeamento de c?digo local: montagem de `./` em `/app` para permitir atualiza??o em tempo real (`watch`).
* **Rede:** `sigaa-network` (driver bridge isolado).
* **Pol?tica de Reinicializa??o:** `restart: unless-stopped`.
