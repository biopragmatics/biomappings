"""Glue functions for lexical workflows."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import click
import curies
from more_click import verbose_option
from sssom_pydantic import SemanticMapping
from tqdm.asyncio import tqdm

from biomappings.lexical_core import PredictionMethod, get_predictions
from biomappings.resources import append_predictions
from biomappings.utils import get_script_url

__all__ = [
    "append_predictions",
    "lexical_prediction_cli",
]


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str,
    *,
    relation: str | None | curies.NamableReference = None,
    identifiers_are_names: bool = False,
    path: Path | None = None,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    batch_size: int | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
    progress: bool = True,
    filter_mutual_mappings: bool = False,
) -> None:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with
        ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param identifiers_are_names: The source prefix's identifiers should be considered
        as names
    :param path: A custom path to predictions TSV file
    :param method: The lexical predication method to use
    :param cutoff: an optional minimum prediction confidence cutoff
    :param batch_size: The batch size for embeddings
    :param custom_filter_function: A custom function that decides if semantic mappings
        should be kept, applied after all other logic.
    :param progress: Should progress be shown?
    :param filter_mutual_mappings: Should mappings between entities in the given
        namespaces be filtered out?
    """
    predictions = get_predictions(
        prefix,
        target_prefixes,
        provenance,
        relation=relation,
        identifiers_are_names=identifiers_are_names,
        method=method,
        cutoff=cutoff,
        batch_size=batch_size,
        custom_filter_function=custom_filter_function,
        progress=progress,
        filter_mutual_mappings=filter_mutual_mappings,
    )
    tqdm.write(f"[{prefix}] generated {len(predictions):,} predictions")

    # since the function that constructs the predictions already
    # pre-standardizes, we don't have to worry about standardizing again
    append_predictions(predictions, path=path)


def lexical_prediction_cli(
    script: str,
    prefix: str,
    target: str | list[str],
    *,
    filter_mutual_mappings: bool = False,
    identifiers_are_names: bool = False,
    predicate: str | None | curies.NamableReference = None,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
) -> None:
    """Construct a CLI and run it."""
    tt = target if isinstance(target, str) else ", ".join(target)

    @click.command(help=f"Generate mappings from {prefix} to {tt}")
    @verbose_option  # type:ignore[misc]
    def main() -> None:
        """Generate mappings."""
        append_lexical_predictions(
            prefix,
            target,
            filter_mutual_mappings=filter_mutual_mappings,
            provenance=get_script_url(script),
            identifiers_are_names=identifiers_are_names,
            relation=predicate,
            method=method,
            cutoff=cutoff,
            custom_filter_function=custom_filter_function,
        )

    main()
