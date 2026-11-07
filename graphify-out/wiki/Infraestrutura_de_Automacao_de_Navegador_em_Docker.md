# Infraestrutura de Automa??o de Navegador em Docker

> **Comunidade 3** ? 17 n?s ? Coes?o: 0.12 ? Fontes: `Dockerfile`, `docker-compose.yml`

## Vis?o Geral
Para executar automa??o web interativa de forma reproduz?vel e isolada em servidores remotos ou m?quinas de desenvolvimento, o cont?iner inclui um ecossistema gr?fico virtual completo baseado em Linux.

---

## ??? Topologia de Portas e Servi?os Gr?ficos

| Porta | Protocolo / Servi?o | Descri??o e Acesso |
| :---: | :--- | :--- |
| **8003** | `HTTP / FastMCP` | Endpoint MCP para clientes web (`http://localhost:8003/mcp`) |
| **6080** | `noVNC (Web Browser)` | Interface gr?fica direta no navegador (`http://localhost:6080/vnc.html?autoconnect=1&resize=scale&password=browser-use`) |
| **5900** | `VNC Server (RFB)` | Conex?o para clientes nativos VNC (TigerVNC, RealVNC, senha: `browser-use`) |

---

## ?? Componentes de Sistema Operacional no Docker
1. **Xvfb (X Virtual Framebuffer):** Cria um display em mem?ria (`:99`) permitindo que o Chromium renderize p?ginas com acelera??o gr?fica virtual sem placa de v?deo f?sica.
2. **x11vnc & websockify:** Captura o display do X11 e exp?e via WebSockets para visualiza??o remota via noVNC.
3. **Openbox:** Gerenciador de janelas ultra-leve para organizar abas e di?logos de download.
4. **Google Chrome / Chromium:** Navegador controlado pelo `browser-use`.
