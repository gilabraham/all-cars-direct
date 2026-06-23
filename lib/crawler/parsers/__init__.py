"""Parser registry. Add new parsers by subclassing ``Parser`` and registering."""
from __future__ import annotations

from .base import Parser
from .generic import GenericParser
from .selectors import SelectorParser

PARSERS: dict[str, type[Parser]] = {
    "generic": GenericParser,
    "json_ld": GenericParser,        # alias — generic prefers JSON-LD anyway
    "selectors": SelectorParser,     # user-supplied CSS selectors
}

__all__ = ["Parser", "PARSERS"]
