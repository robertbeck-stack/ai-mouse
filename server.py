"""
AI Mouse MCP Server Entrypoint.
Runs the modular ai_mouse MCP server.
"""

import sys
from pathlib import Path

# Add src to python path for modular import
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ai_mouse.server import server, main

if __name__ == "__main__":
    main()
