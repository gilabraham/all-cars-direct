"""Base class for crawler parsers."""
from __future__ import annotations

import abc
import json
from typing import Iterable


class Parser(abc.ABC):
    """A parser turns HTML from one URL into zero or more canonical listings.

    Subclasses implement ``parse``. Each yielded dict should match (a subset of)
    the columns in ``db.EDITABLE_COLUMNS`` — at minimum ``make``, ``model``,
    ``year``. The runner upserts using (source_id, external_id), where
    ``external_id`` is taken from the dict if present, otherwise the URL.
    """

    @classmethod
    def from_config(cls, config: dict | str | None) -> "Parser":
        cfg: dict = {}
        if isinstance(config, str) and config.strip():
            try:
                cfg = json.loads(config)
            except json.JSONDecodeError:
                cfg = {}
        elif isinstance(config, dict):
            cfg = config
        return cls(cfg)

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abc.abstractmethod
    def parse(self, html: str, url: str) -> Iterable[dict]:
        ...
