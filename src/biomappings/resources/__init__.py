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
import curies
import sssom_pydantic
from bioregistry import NormalizedNamedReference
from curies import Reference
from sssom_pydantic import MappingSet, Metadata, SemanticMapping

from ..utils import (
    CURATORS_PATH,
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
)

if TYPE_CHECKING:
    import networkx

__all__ = [
    "SemanticMapping",
    "append_false_mappings",
    "append_predictions",
    "append_true_mappings",
    "append_unsure_mappings",
    "get_current_curator",
    "get_false_graph",
    "get_predictions_graph",
    "get_true_graph",
    "load_curators",
    "load_false_mappings",
    "load_mappings",
    "load_predictions",
    "load_unsure",
    "write_false_mappings",
    "write_predictions",
    "write_true_mappings",
    "write_unsure_mappings",
]

logger = logging.getLogger(__name__)


def _write_helper(
    mappings: Iterable[SemanticMapping],
    path: str | Path,
    mode: Literal["w", "a"],
    metadata: Metadata | MappingSet | None = None,
    exclude_mappings: Iterable[SemanticMapping] | None = None,
    converter: curies.Converter | None = None,
) -> None:
    if mode == "a":
        sssom_pydantic.append(mappings, path)
    elif mode == "w":
        if converter is None:
            converter = bioregistry.get_default_converter()
        sssom_pydantic.write(
            mappings,
            path,
            metadata=metadata,
            converter=converter,
            exclude_mappings=exclude_mappings,
            drop_duplicates=True,
            sort=True,
        )
    else:
        raise ValueError(f"invalid mode: {mode}")


def load_mappings(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the mappings table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or POSITIVES_SSSOM_PATH)
    return mappings


def append_true_mappings(
    mappings: Iterable[SemanticMapping],
    *,
    sort: bool = True,
    path: Path | None = None,
) -> None:
    """Append new lines to the mappings table."""
    if path is None:
        path = POSITIVES_SSSOM_PATH
    _write_helper(mappings, path=path, mode="a")
    if sort:
        lint_true_mappings(path=path)


def write_true_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappings to the true mappings file."""
    _write_helper(mappings, path or POSITIVES_SSSOM_PATH, mode="w")


def lint_true_mappings(*, path: Path | None = None) -> None:
    """Lint the true mappings file."""
    sssom_pydantic.lint(path or POSITIVES_SSSOM_PATH)


def load_false_mappings(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the false mappings table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or NEGATIVES_SSSOM_PATH)
    return mappings


def append_false_mappings(
    mappings: Iterable[SemanticMapping],
    *,
    sort: bool = True,
    path: Path | None = None,
) -> None:
    """Append new lines to the false mappings table."""
    if path is None:
        path = NEGATIVES_SSSOM_PATH
    _write_helper(mappings, path=path, mode="a")
    if sort:
        lint_false_mappings(
            path=path,
        )


def write_false_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappings to the false mappings file."""
    _write_helper(mappings, path or NEGATIVES_SSSOM_PATH, mode="w")


def lint_false_mappings(*, path: Path | None = None) -> None:
    """Lint the false mappings file."""
    sssom_pydantic.lint(path or NEGATIVES_SSSOM_PATH)


def load_unsure(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the unsure table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or UNSURE_SSSOM_PATH)
    return mappings


def append_unsure_mappings(
    mappings: Iterable[SemanticMapping],
    *,
    sort: bool = True,
    path: Path | None = None,
) -> None:
    """Append new lines to the "unsure" mappings table."""
    if path is None:
        path = UNSURE_SSSOM_PATH
    _write_helper(mappings, path=path, mode="a")
    if sort:
        lint_unsure_mappings(path=path)


def write_unsure_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappings to the unsure mappings file."""
    _write_helper(mappings, path or UNSURE_SSSOM_PATH, mode="w")


def lint_unsure_mappings(*, path: Path | None = None) -> None:
    """Lint the unsure mappings file."""
    sssom_pydantic.lint(path or UNSURE_SSSOM_PATH)


def load_predictions(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the predictions table."""
    mappings, _converter, _mapping_set = sssom_pydantic.read(path or PREDICTIONS_SSSOM_PATH)
    return mappings


def write_predictions(
    mappings: Iterable[SemanticMapping],
    *,
    path: Path | None = None,
    exclude_mappings: Iterable[SemanticMapping] | None = None,
    metadata: Metadata | MappingSet | None = None,
    converter: curies.Converter | None = None,
) -> None:
    """Write new content to the predictions table."""
    if path is None:
        path = PREDICTIONS_SSSOM_PATH
    _write_helper(
        mappings,
        path,
        metadata=metadata,
        converter=converter,
        mode="w",
        exclude_mappings=exclude_mappings,
    )


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


def lint_predictions(*, path: Path | None = None) -> None:
    """Lint the predictions file, excluding mappings appearing in any curated files."""
    sssom_pydantic.lint(
        path or PREDICTIONS_SSSOM_PATH,
        exclude_mappings=[
            *load_mappings(),
            *load_false_mappings(),
            *load_unsure(),
        ],
        drop_duplicates=True,
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
