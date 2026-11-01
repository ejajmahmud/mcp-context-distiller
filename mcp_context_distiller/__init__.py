"""
MCP Context Distiller
Dynamic context pruner and token condenser for Model Context Protocol servers and agents.
"""

from .distiller import ContextDistiller, distill_schema, distill_output

__version__ = "0.1.0"
__all__ = ["ContextDistiller", "distill_schema", "distill_output"]
