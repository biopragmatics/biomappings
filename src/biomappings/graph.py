"""Load Biomappings as a graph."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Collection, Iterable, Sequence
from typing import TYPE_CHECKING

import networkx as nx
from curies import Reference
from sssom_pydantic import SemanticMapping

from biomappings.resources import load_false_mappings, load_mappings, load_predictions

if TYPE_CHECKING:
    import matplotlib.axes

__all__ = [
    "get_false_graph",
    "get_predictions_graph",
    "get_true_graph",
]

logger = logging.getLogger(__name__)


def get_true_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the true mappings."""
    return _graph_from_mappings(load_mappings(), strata="correct", include=include, exclude=exclude)


def get_false_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the false mappings."""
    return _graph_from_mappings(
        load_false_mappings(), strata="incorrect", include=include, exclude=exclude
    )


def get_predictions_graph(
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the predicted mappings."""
    return _graph_from_mappings(
        load_predictions(), strata="predicted", include=include, exclude=exclude
    )


def _graph_from_mappings(
    mappings: Iterable[SemanticMapping],
    strata: str,
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> nx.Graph:
    graph = nx.Graph()

    if include is not None:
        include = set(include)
        logger.info("only including %s", include)
    if exclude is not None:
        exclude = set(exclude)
        logger.info("excluding %s", exclude)

    for mapping in mappings:
        if exclude and (mapping.predicate in exclude):
            continue
        if include and (mapping.predicate not in include):
            continue
        graph.add_edge(
            mapping.subject,
            mapping.object,
            relation=mapping.predicate.curie,
            provenance=mapping.author.curie if mapping.author else None,
            type=mapping.mapping_justification.curie,
            strata=strata,
        )
    return graph


def _countplot_list(data: list[int], ax: matplotlib.axes.Axes) -> None:
    import pandas as pd
    import seaborn as sns

    counter = Counter(data)
    for size in range(min(counter), max(counter)):
        if size not in counter:
            counter[size] = 0
    df = pd.DataFrame(counter.items(), columns=["size", "count"]).sort_values("size").reset_index()
    sns.barplot(data=df, x="size", y="count", ax=ax)
