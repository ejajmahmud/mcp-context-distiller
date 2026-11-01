"""
Context Distillation Core Logic.
Compresses JSON schemas and tool outputs while preserving semantic fidelity.
"""

import json
from typing import Any, Dict, List, Optional, Union


def estimate_tokens(text: str) -> int:
    """Fast token heuristic (average ~3.8 characters per token for JSON/code)."""
    return max(1, len(text) // 4)


def distill_schema(schema: Dict[str, Any], mode: str = "compact") -> Dict[str, Any]:
    """
    Minimizes tool input JSON schemas.
    Modes:
      - 'compact': Strips empty fields, redundant metadata, and trims repetitive descriptions.
      - 'minimal': Keeps only type, properties, required fields, and enum values.
    """
    if not isinstance(schema, dict):
        return schema

    cleaned: Dict[str, Any] = {}
    allowed_keys = {
        "compact": {"type", "properties", "required", "items", "description", "enum", "default"},
        "minimal": {"type", "properties", "required", "items", "enum"}
    }.get(mode, {"type", "properties", "required", "items", "description"})

    for k, v in schema.items():
        if k not in allowed_keys or v is None or v == "" or v == []:
            continue

        if k == "description" and isinstance(v, str) and mode == "compact":
            # Condense verbose descriptions to the first sentence or 120 chars
            first_sentence = v.split(". ")[0].strip()
            if len(first_sentence) > 120:
                first_sentence = first_sentence[:117] + "..."
            cleaned[k] = first_sentence
        elif k == "properties" and isinstance(v, dict):
            cleaned["properties"] = {
                prop_name: distill_schema(prop_val, mode=mode)
                for prop_name, prop_val in v.items()
            }
        elif k == "items" and isinstance(v, dict):
            cleaned["items"] = distill_schema(v, mode=mode)
        else:
            cleaned[k] = v

    return cleaned


def distill_output(
    data: Any,
    max_tokens: int = 1500,
    max_array_items: int = 10,
    truncate_strings: int = 300
) -> Any:
    """
    Recursively compresses tool outputs:
    1. Truncates long string values with length annotations.
    2. Samples head and tail of oversized arrays and adds condensation metadata.
    3. Drops null or blank object entries.
    """
    if isinstance(data, str):
        if len(data) > truncate_strings:
            omitted = len(data) - truncate_strings
            return data[:truncate_strings] + f" ...[+{omitted} chars truncated]"
        return data

    if isinstance(data, list):
        if len(data) > max_array_items:
            head_count = max_array_items // 2
            tail_count = max_array_items - head_count
            head = [distill_output(x, max_tokens, max_array_items, truncate_strings) for x in data[:head_count]]
            tail = [distill_output(x, max_tokens, max_array_items, truncate_strings) for x in data[-tail_count:]]
            omitted = len(data) - (head_count + tail_count)
            return head + [f"...[{omitted} items omitted for brevity]..."] + tail
        return [distill_output(x, max_tokens, max_array_items, truncate_strings) for x in data]

    if isinstance(data, dict):
        distilled: Dict[str, Any] = {}
        for k, v in data.items():
            if v is None or v == "":
                continue
            distilled[k] = distill_output(v, max_tokens, max_array_items, truncate_strings)
        return distilled

    return data


class ContextDistiller:
    def __init__(self, schema_mode: str = "compact", max_output_tokens: int = 1500):
        self.schema_mode = schema_mode
        self.max_output_tokens = max_output_tokens

    def process_tool_list(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes tools/list response from MCP server."""
        processed = []
        for tool in tools:
            copy_tool = dict(tool)
            if "inputSchema" in copy_tool:
                copy_tool["inputSchema"] = distill_schema(copy_tool["inputSchema"], mode=self.schema_mode)
            processed.append(copy_tool)
        return processed

    def process_tool_call_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Processes tools/call response from MCP server."""
        distilled = dict(result)
        if "content" in distilled and isinstance(distilled["content"], list):
            new_content = []
            for item in distilled["content"]:
                if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                    raw_text = item["text"]
                    try:
                        parsed = json.loads(raw_text)
                        compressed = distill_output(parsed, max_tokens=self.max_output_tokens)
                        new_content.append({"type": "text", "text": json.dumps(compressed, separators=(",", ":"))})
                    except Exception:
                        if len(raw_text) > 1000:
                            truncated = raw_text[:800] + f"\n...[+{len(raw_text)-800} chars truncated]"
                            new_content.append({"type": "text", "text": truncated})
                        else:
                            new_content.append(item)
                else:
                    new_content.append(item)
            distilled["content"] = new_content
        return distilled
