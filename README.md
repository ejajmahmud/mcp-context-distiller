# MCP Context Distiller ⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

**MCP Context Distiller** is a zero-latency proxy and optimization engine for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). It drastically cuts token consumption by intelligently pruning redundant tool schema metadata and dynamically condensing large tool outputs before they reach your LLM agent's context window.

---

## 🚀 Why MCP Context Distiller?

Modern agentic workflows often hit rate limits and context degradation because:
- **Schema Bloat**: MCP servers expose extensive JSON Schemas with multi-paragraph human descriptions, unnecessary drafts, and null properties that burn thousands of prompt tokens on every turn.
- **Output Flooding**: Database queries, file searches, or log lookups return huge arrays that eat 80%+ of an agent's available context window.
- **Reasoning Drift**: LLMs lose track of original instructions when flooded with repetitive structural boilerplate.

**MCP Context Distiller** intercepts the JSON-RPC stream between any MCP client (Claude Desktop, Antigravity, Cursor, Continue) and downstream MCP servers to solve this transparently.

```
+--------------------+        +-------------------------+        +---------------------+
|     MCP Client     |  <-->  |  mcp-context-distiller  |  <-->  | Downstream Server   |
| (Claude/IDE/Agent) |        |   (Smart Pruning Proxy) |        | (DB, Filesystem...) |
+--------------------+        +-------------------------+        +---------------------+
                                         │
                                         ▼
                            -40% to -75% Token Reduction
```

---

## ✨ Features

- **AST-Aware Schema Pruning**: Strips internal schema directives (`$schema`, `title`, redundant `definitions`) while preserving critical types, parameter names, and required constraints.
- **Dynamic Array & String Distillation**: Intelligently summarizes massive lists with head/tail sampling and explicit omission counters (e.g. `[...46 items omitted for brevity...]`).
- **Zero Configuration Stdio Proxy**: Wrap any existing MCP server command in one line without altering server or client source code.
- **Zero Third-Party Dependencies**: Pure Python 3 standard library implementation for maximum speed, security, and portability.

---

## 📦 Installation

```bash
git clone https://github.com/ejajmahmud/mcp-context-distiller.git
cd mcp-context-distiller
pip install -e .
```

---

## 🛠️ Usage

### 1. Transparent MCP Stdio Proxy

In your agent or MCP client configuration (e.g., `claude_desktop_config.json` or Antigravity configuration):

```json
{
  "mcpServers": {
    "postgres-distilled": {
      "command": "mcp-distill",
      "args": [
        "proxy",
        "--cmd",
        "npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb",
        "--mode",
        "compact"
      ]
    }
  }
}
```

### 2. Schema Benchmarking CLI

Test token savings on your existing tool definitions:

```bash
mcp-distill benchmark ./sample_tool_schema.json --mode minimal
```

Output:
```text
=== MCP Context Distiller Benchmark ===
Original Size   : 14,250 chars (~3,562 tokens)
Distilled Size  : 3,820 chars (~955 tokens)
Tokens Saved    : 2,607 (73.2% reduction)
```

---

## 🧪 Testing

Run the included unit test suite:

```bash
python -m unittest discover -s tests
```

---

## 📄 License

MIT © [Ejaj Mahmud](https://github.com/ejajmahmud)
