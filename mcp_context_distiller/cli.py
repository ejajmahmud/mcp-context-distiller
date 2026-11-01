"""
CLI Interface for mcp-context-distiller.
"""

import argparse
import json
import sys
from .distiller import distill_schema, distill_output, estimate_tokens
from .proxy import MCPProxy


def main():
    parser = argparse.ArgumentParser(
        prog="mcp-distill",
        description="High-performance context compressor and token condenser for MCP servers"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: proxy
    proxy_parser = subparsers.add_parser("proxy", help="Run proxy wrapping a target MCP server")
    proxy_parser.add_argument("--cmd", required=True, help="Command to run target MCP server (e.g. 'npx -y @modelcontextprotocol/server-postgres ...')")
    proxy_parser.add_argument("--mode", default="compact", choices=["compact", "minimal"], help="Schema pruning mode")

    # Subcommand: benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark token savings on a JSON payload or schema file")
    bench_parser.add_argument("file", help="Path to JSON file containing raw schema or tool response")
    bench_parser.add_argument("--mode", default="compact", choices=["compact", "minimal"])

    args = parser.parse_args()

    if args.command == "proxy":
        proxy = MCPProxy(target_command=args.cmd, schema_mode=args.mode)
        proxy.start()

    elif args.command == "benchmark":
        with open(args.file, "r", encoding="utf-8") as f:
            raw_text = f.read()
            data = json.loads(raw_text)

        orig_len = len(raw_text)
        orig_tokens = estimate_tokens(raw_text)

        if isinstance(data, dict) and ("type" in data or "properties" in data):
            distilled = distill_schema(data, mode=args.mode)
        else:
            distilled = distill_output(data)

        distilled_text = json.dumps(distilled, separators=(",", ":"))
        new_len = len(distilled_text)
        new_tokens = estimate_tokens(distilled_text)

        savings_pct = (1.0 - (new_tokens / max(1, orig_tokens))) * 100

        print("=== MCP Context Distiller Benchmark ===")
        print(f"Original Size   : {orig_len:,} chars (~{orig_tokens:,} tokens)")
        print(f"Distilled Size  : {new_len:,} chars (~{new_tokens:,} tokens)")
        print(f"Tokens Saved    : {orig_tokens - new_tokens:,} ({savings_pct:.1f}% reduction)")


if __name__ == "__main__":
    main()
