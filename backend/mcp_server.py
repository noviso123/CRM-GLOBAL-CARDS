#!/usr/bin/env python3
"""CRM GLOBAL CARDS - Model Context Protocol (MCP) Stdio Server.

Permite conectar Claude Desktop, Cursor, Antigravity ou qualquer agente IA
ao CRM GLOBAL CARDS, Bling ERP v3 e Fornecedores Gráficos diretamente via Stdio (Standard I/O).

Uso no claude_desktop_config.json:
{
  "mcpServers": {
    "crm-globalcards": {
      "command": "python",
      "args": ["C:/Users/Jhonatan/Documents/Projetos/CRM Bling/backend/mcp_server.py"]
    }
  }
}
"""

import sys
import json
from pathlib import Path

# Adiciona o diretório backend ao sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database.dbf_manager import DBFManager
from app.mcp.bling_mcp import BlingMCPEngine


def main() -> None:
    mgr = DBFManager()
    engine = BlingMCPEngine(mgr)

    sys.stderr.write("CRM GLOBAL CARDS MCP Server iniciado via Stdio (Protocolo 2024-11-05)\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = engine.handle_jsonrpc(req)
            if res:
                sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Erro interno no servidor MCP: {str(exc)}"},
            }
            sys.stdout.write(json.dumps(err_res, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
