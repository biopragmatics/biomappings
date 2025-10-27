"""Community curated mappings between biomedical entities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from .resources import (
    append_predictions,
    get_false_graph,
    get_predictions_graph,
    get_true_graph,
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
)
from .utils import DEFAULT_REPO, get_script_url

if TYPE_CHECKING:
    from sssom_pydantic import MappingTool

__all__ = [
    "DEFAULT_REPO",
    "append_lexical_predictions",
    "append_predictions",
    "get_false_graph",
    "get_predictions_graph",
    "get_script_url",
    "get_true_graph",
    "lexical_prediction_cli",
    "load_false_mappings",
    "load_mappings",
    "load_predictions",
    "load_unsure",
]


def lexical_prediction_cli(
    prefix: str,
    target: str | list[str],
    /,
    *,
    script: str,
    **kwargs: Any,
) -> None:
    """Run the lexical predictions CLI."""
    return DEFAULT_REPO.lexical_prediction_cli(
        prefix, target, mapping_tool=get_script_url(script), **kwargs
    )


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    *,
    mapping_tool: str | MappingTool | None = None,
    **kwargs: Any,
) -> None:
    """Append lexical predictions."""
    return DEFAULT_REPO.append_lexical_predictions(
        prefix, target_prefixes, mapping_tool=mapping_tool, **kwargs
    )
