"""Biomappings resources."""

from __future__ import annotations

import csv
import getpass
import itertools as itt
import logging
from collections.abc import Collection, Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

import bioregistry
import sssom_pydantic
from bioregistry import NormalizedNamedReference
from curies import Reference
from sssom_pydantic import SemanticMapping

from ..utils import (
    CURATORS_PATH,
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
)
from ..wsgi_utils import insert

if TYPE_CHECKING:
    import networkx

__all__ = [
    "append_false_mappings",
    "append_predictions",
    "append_true_mappings",
    "get_current_curator",
    "get_false_graph",
    "get_predictions_graph",
    "get_true_graph",
    "load_curators",
    "load_false_mappings",
    "load_mappings",
    "load_predictions",
    "load_unsure",
]

logger = logging.getLogger(__name__)


def load_mappings(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the mappings table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or POSITIVES_SSSOM_PATH)
    return mappings


def _append_helper(
    mappings: Iterable[SemanticMapping], path: Path | None, default_path: Path
) -> None:
    if path is None:
        path = default_path
    insert(path, converter=bioregistry.get_converter(), include_mappings=mappings)


def append_true_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Append new lines to the mappings table."""
    _append_helper(mappings, path, POSITIVES_SSSOM_PATH)


def append_false_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Append new lines to the false mappings table."""
    _append_helper(mappings, path, NEGATIVES_SSSOM_PATH)


def load_false_mappings(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the false mappings table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or NEGATIVES_SSSOM_PATH)
    return mappings


def load_unsure(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the unsure table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or UNSURE_SSSOM_PATH)
    return mappings


def load_predictions(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the predictions table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or PREDICTIONS_SSSOM_PATH)
    return mappings


def append_predictions(
    new_mappings: Iterable[SemanticMapping],
    *,
    path: Path | None = None,
) -> None:
    """Append new lines to the predictions table."""
    if path is None:
        path = PREDICTIONS_SSSOM_PATH

    mappings, converter, metadata = sssom_pydantic.read(path)

    prefixes: set[str] = set()
    for mapping in new_mappings:
        prefixes.update(mapping.get_prefixes())
        mappings.append(mapping)

    for prefix in prefixes:
        if not converter.standardize_prefix(prefix):
            raise NotImplementedError("amending prefixes not yet implemented")

    curated_paths = [POSITIVES_SSSOM_PATH, NEGATIVES_SSSOM_PATH, UNSURE_SSSOM_PATH]

    exclude_mappings = itt.chain.from_iterable(
        sssom_pydantic.read(path)[0] for path in curated_paths
    )

    sssom_pydantic.write(
        mappings,
        path,
        metadata=metadata,
        converter=converter,
        drop_duplicates=True,
        sort=True,
        exclude_mappings=exclude_mappings,
    )


def load_curators() -> dict[str, NormalizedNamedReference]:
    """Load the curators table."""
    with CURATORS_PATH.open() as file:
        return {
            record["user"]: NormalizedNamedReference(
                prefix="orcid", identifier=record["orcid"], name=record["name"]
            )
            for record in csv.DictReader(file, delimiter="\t")
        }


class MissingCuratorError(KeyError):
    """Raised when the current user's login is not listed in the curators file."""


# docstr-coverage:excused `overload`
@overload
def get_current_curator(*, strict: Literal[True] = True) -> NormalizedNamedReference: ...


# docstr-coverage:excused `overload`
@overload
def get_current_curator(*, strict: Literal[False] = False) -> NormalizedNamedReference | None: ...


def get_current_curator(*, strict: bool = True) -> NormalizedNamedReference | None:
    """Get the current curator, based on the current user's login name."""
    current_user = getpass.getuser()
    curators = load_curators()
    if current_user in curators:
        return curators[current_user]
    elif strict:
        raise MissingCuratorError
    else:
        return None


def get_true_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> networkx.Graph:
    """Get a graph of the true mappings."""
    return _graph_from_mappings(load_mappings(), strata="correct", include=include, exclude=exclude)


def get_false_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> networkx.Graph:
    """Get a graph of the false mappings."""
    return _graph_from_mappings(
        load_false_mappings(), strata="incorrect", include=include, exclude=exclude
    )


def get_predictions_graph(
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> networkx.Graph:
    """Get a graph of the predicted mappings."""
    return _graph_from_mappings(
        load_predictions(), strata="predicted", include=include, exclude=exclude
    )


def _graph_from_mappings(
    mappings: Iterable[SemanticMapping],
    strata: str,
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> networkx.Graph:
    import networkx as nx

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
            type=mapping.justification.curie,
            strata=strata,
        )
    return graph
