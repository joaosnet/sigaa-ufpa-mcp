import os
import logging
from typing import Any, Dict
from browser_use import Agent
from browser_use.llm.google import ChatGoogle
from fastmcp import FastMCP
from pydantic import Field
from dotenv import dotenv_values
import warnings

warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings(
    "ignore", message="websockets.server.WebSocketServerProtocol is deprecated"
)

# Inicializar FastMCP
mcp = FastMCP("SIGAA UFPA MCP Server")
BASE_URL = "https://sigaa.ufpa.br"
LOGIN_URL = f"{BASE_URL}/sigaa/verTelaLogin.do"
MOBILE_URL = f"{BASE_URL}/sigaa/mobile/touch/public/principal.jsf"

descricao = "Nome da tarefa a ser executada no sigaa"

@mcp.tool()
async def pegar_conteudo_sigaa(
    task: str = Field(..., description=descricao),
) -> Dict[str, Any]:
    try:
        config = dotenv_values(".env")
        sensitive_data = {
            "x_user": config.get("SIGAA_USERNAME"),
            "x_pass": config.get("SIGAA_PASSWORD"),
        }
        task += f"if need Log into {LOGIN_URL} with username x_user and password x_pass"
        result = await Agent(
            task=task,
            sensitive_data=sensitive_data,
            llm=ChatGoogle(
                api_key=config.get("GOOGLE_API_KEY"),
                model="gemini-flash-latest",
            ),
        ).run()

        logging.info(f"Login attempt result: {result['success']}")
        return result

    except Exception as e:
        logging.error(f"Erro no login SIGAA: {e}")
        return {"success": False, "error": str(e), "logged_in": False}


if __name__ == "__main__":
    try:
        # Padrão é 'stdio', a menos que MCP_TRANSPORT seja 'http'
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio")

        if transport_mode == "http":
            logging.info("Iniciando servidor MCP em modo HTTP...")
            mcp.run(transport="http", host="0.0.0.0", port=8000)
        elif transport_mode == "stdio":
            logging.info("Iniciando servidor MCP em modo stdio...")
            mcp.run(transport="stdio")
        else:
            logging.error(
                f"Modo de transporte desconhecido: {transport_mode}. Use 'stdio' ou 'http'."
            )
            # Inicia em stdio como fallback seguro para clientes MCP
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logging.info("Encerrando servidor...")
