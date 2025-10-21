"""Glue functions for lexical workflows."""

from __future__ import annotations

import typing
from typing import Any

import click
from sssom_pydantic import MappingTool

from . import lexical_core

__all__ = [
    "append_lexical_predictions",
    "get_predict_cli",
    "lexical_prediction_cli",
]


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | typing.Iterable[str],
    provenance: str | MappingTool,
    **kwargs: Any,
) -> None:
    """Append lexical predictions."""
    from biomappings.utils import CURATED_PATHS, PREDICTIONS_SSSOM_PATH

    return lexical_core.append_lexical_predictions(
        prefix,
        target_prefixes,
        mapping_tool=provenance,
        path=PREDICTIONS_SSSOM_PATH,
        curated_paths=CURATED_PATHS,
        **kwargs,
    )


def lexical_prediction_cli(
    script: str,
    prefix: str,
    target: str | list[str],
    **kwargs: Any,
) -> None:
    """Run the lexical predictions CLI."""
    from biomappings.utils import CURATED_PATHS, PREDICTIONS_SSSOM_PATH

    return lexical_core.lexical_prediction_cli(
        script, prefix, target, path=PREDICTIONS_SSSOM_PATH, curated_paths=CURATED_PATHS, **kwargs
    )


def get_predict_cli(
    source_prefix: str | None = None, target_prefix: str | None | list[str] = None
) -> click.Command:
    """Create a prediction CLI."""
    from biomappings.utils import CURATED_PATHS, PREDICTIONS_SSSOM_PATH

    return lexical_core.get_predict_cli(
        source_prefix=source_prefix,
        target_prefix=target_prefix,
        path=PREDICTIONS_SSSOM_PATH,
        curated_paths=CURATED_PATHS,
    )
