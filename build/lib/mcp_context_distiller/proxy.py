"""
MCP JSON-RPC Stdio Proxy.
Runs between LLM client and target MCP server, distilling messages on the fly.
"""

import sys
import json
import subprocess
import threading
from typing import Optional
from .distiller import ContextDistiller


class MCPProxy:
    def __init__(self, target_command: str, schema_mode: str = "compact"):
        self.target_command = target_command
        self.distiller = ContextDistiller(schema_mode=schema_mode)
        self.process: Optional[subprocess.Popen] = None

    def start(self):
        """Starts the downstream MCP server process and pipes stdio."""
        self.process = subprocess.Popen(
            self.target_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            shell=True,
            bufsize=1
        )

        # Thread: reads downstream output, distills, and writes to stdout
        t_out = threading.Thread(target=self._pipe_server_to_client, daemon=True)
        t_out.start()

        # Main thread: reads stdin from client, passes to downstream server
        try:
            for line in sys.stdin:
                if self.process.poll() is not None:
                    break
                if self.process.stdin:
                    self.process.stdin.write(line)
                    self.process.stdin.flush()
        except (KeyboardInterrupt, BrokenPipeError):
            pass
        finally:
            if self.process:
                self.process.terminate()

    def _pipe_server_to_client(self):
        try:
            assert self.process and self.process.stdout
            for line in self.process.stdout:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    payload = json.loads(line_str)
                    # Check if response to tools/list
                    result = payload.get("result", {})
                    if "tools" in result and isinstance(result["tools"], list):
                        result["tools"] = self.distiller.process_tool_list(result["tools"])
                        payload["result"] = result
                    # Check if response to tools/call
                    elif "content" in result:
                        payload["result"] = self.distiller.process_tool_call_result(result)
                    
                    sys.stdout.write(json.dumps(payload) + "\n")
                    sys.stdout.flush()
                except Exception:
                    sys.stdout.write(line)
                    sys.stdout.flush()
        except Exception:
            pass
