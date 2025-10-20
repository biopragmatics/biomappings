"""Glue functions for lexical workflows."""

from __future__ import annotations

import itertools as itt
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Callable

import click
import curies
import networkx as nx
import pyobo
from curies import ReferenceTuple
from more_click import verbose_option
from sssom_pydantic import SemanticMapping
from tqdm.asyncio import tqdm

from biomappings.lexical_core import CMapping, PredictionMethod, get_predictions
from biomappings.resources import append_predictions
from biomappings.utils import get_script_url

__all__ = [
    "append_predictions",
    "get_mutual_mapping_filter",
    "lexical_prediction_cli",
]


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str,
    *,
    relation: str | None | curies.NamableReference = None,
    custom_filter: CMapping | None = None,
    identifiers_are_names: bool = False,
    path: Path | None = None,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    batch_size: int | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
    progress: bool = True,
) -> None:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with
        ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param custom_filter: A triple nested dictionary from source prefix to target prefix
        to source id to target id. Any source prefix, target prefix, source id
        combinations in this dictionary will be filtered.
    :param identifiers_are_names: The source prefix's identifiers should be considered
        as names
    :param path: A custom path to predictions TSV file
    :param method: The lexical predication method to use
    :param cutoff: an optional minimum prediction confidence cutoff
    :param batch_size: The batch size for embeddings
    :param custom_filter_function: A custom function that decides if semantic mappings
        should be kept, applied after all other logic.
    :param progress: Should progress be shown?
    """
    predictions = get_predictions(
        prefix,
        target_prefixes,
        provenance,
        relation=relation,
        custom_filter=custom_filter,
        identifiers_are_names=identifiers_are_names,
        method=method,
        cutoff=cutoff,
        batch_size=batch_size,
        custom_filter_function=custom_filter_function,
        progress=progress,
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
        if filter_mutual_mappings:
            mutual_mapping_filter = get_mutual_mapping_filter(prefix, target)
        else:
            mutual_mapping_filter = None

        append_lexical_predictions(
            prefix,
            target,
            custom_filter=mutual_mapping_filter,
            provenance=get_script_url(script),
            identifiers_are_names=identifiers_are_names,
            relation=predicate,
            method=method,
            cutoff=cutoff,
            custom_filter_function=custom_filter_function,
        )

    main()


def get_mutual_mapping_filter(prefix: str, targets: Iterable[str]) -> CMapping:
    """Get a custom filter dictionary induced over the mutual mapping graph with all target prefixes.

    :param prefix: The source prefix
    :param targets: All potential target prefixes

    :returns: A filter 3-dictionary of source prefix to target prefix to source
        identifier to target identifier
    """
    graph = _mutual_mapping_graph([prefix, *targets])
    rv: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for node in graph:
        if node.prefix != prefix:
            continue
        for xref_prefix, xref_identifier in nx.single_source_shortest_path(graph, node):
            rv[xref_prefix][node.identifier] = xref_identifier
    return {prefix: dict(rv)}


def _mutual_mapping_graph(
    prefixes: Iterable[str],
    skip_sources: Iterable[str] | None = None,
    skip_targets: Iterable[str] | None = None,
) -> nx.Graph:
    """Get the undirected mapping graph between the given prefixes.

    :param prefixes: A list of prefixes to use with :func:`pyobo.get_filtered_xrefs` to
        get xrefs.
    :param skip_sources: An optional list of prefixes to skip as the source for xrefs
    :param skip_targets: An optional list of prefixes to skip as the target for xrefs

    :returns: The undirected mapping graph containing mappings between entries in the
        given namespaces.
    """
    prefixes = sorted(prefixes)
    skip_sources = _upgrade_set(skip_sources)
    skip_targets = _upgrade_set(skip_targets)
    graph = nx.Graph()
    for source, target in itt.product(prefixes, repeat=2):
        if source == target or source in skip_sources or target in skip_targets:
            continue
        for source_id, target_id in pyobo.get_filtered_xrefs(source, target).items():
            graph.add_edge(ReferenceTuple(source, source_id), ReferenceTuple(target, target_id))
    return graph


def _upgrade_set(values: Iterable[str] | None = None) -> set[str]:
    return set() if values is None else set(values)
