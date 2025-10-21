"""Community curated mappings between biomedical entities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from .resources import (
    SemanticMapping,
    get_false_graph,
    get_predictions_graph,
    get_true_graph,
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
)

if TYPE_CHECKING:
    from sssom_pydantic import MappingTool

__all__ = [
    "SemanticMapping",
    "get_false_graph",
    "get_predictions_graph",
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
    from . import lexical_workflow
    from .utils import CURATED_PATHS, PREDICTIONS_SSSOM_PATH, get_script_url

    return lexical_workflow.lexical_prediction_cli(
        prefix,
        target,
        mapping_tool=MappingTool(name=get_script_url(script), version=None),
        path=PREDICTIONS_SSSOM_PATH,
        curated_paths=CURATED_PATHS,
        **kwargs,
    )


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str | MappingTool,
    **kwargs: Any,
) -> None:
    """Append lexical predictions."""
    from . import lexical_workflow
    from .utils import CURATED_PATHS, PREDICTIONS_SSSOM_PATH

    return lexical_workflow.append_lexical_predictions(
        prefix,
        target_prefixes,
        mapping_tool=provenance,
        path=PREDICTIONS_SSSOM_PATH,
        curated_paths=CURATED_PATHS,
        **kwargs,
    )
