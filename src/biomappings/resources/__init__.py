"""Biomappings resources."""

from __future__ import annotations

import csv
import getpass
import itertools as itt
import logging
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

import bioregistry
import networkx as nx
import sssom_pydantic
from bioregistry import NormalizedNamedReference
from curies import Reference
from sssom_pydantic import MappingTool, Metadata, SemanticMapping
from tqdm.auto import tqdm

from ..lexical_utils import drop_duplicates, remove_redundant_external
from ..utils import (
    CURATORS_PATH,
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    PURL_BASE,
    UNSURE_SSSOM_PATH,
)

if TYPE_CHECKING:
    import semra

__all__ = [
    "SemanticMapping",
    "append_false_mappings",
    "append_predictions",
    "append_predictions",
    "append_true_mappings",
    "append_unsure_mappings",
    "get_curated_filter",
    "get_current_curator",
    "get_false_graph",
    "get_predictions_graph",
    "get_true_graph",
    "load_curators",
    "load_false_mappings",
    "load_mappings",
    "load_mappings_subset",
    "load_predictions",
    "load_unsure",
    "mappings_from_semra",
    "write_false_mappings",
    "write_predictions",
    "write_true_mappings",
    "write_unsure_mappings",
]

logger = logging.getLogger(__name__)

COLUMNS = [
    "subject_id",
    "subject_label",
    "predicate_id",
    "object_id",
    "object_label",
    "mapping_justification",
    "author_id",
    "mapping_tool",
    "predicate_modifier",
]


def _load_table(path: str | Path) -> list[SemanticMapping]:
    path = Path(path).expanduser().resolve()
    mappings, _converter, _mapping_set = sssom_pydantic.read(
        path,
        metadata={"mapping_set_id": f"{PURL_BASE}/{path.name}"},
    )
    return mappings


def _write_helper(
    mappings: Iterable[SemanticMapping],
    path: str | Path,
    mode: Literal["w", "a"],
    metadata: Metadata | None = None,
    exclude_mappings: Iterable[SemanticMapping] | None = None,
) -> None:
    if exclude_mappings is not None:
        mappings = remove_redundant_external(mappings, exclude_mappings)
    mappings = drop_duplicates(mappings)
    mappings = sorted(mappings)
    if mode == "a":
        sssom_pydantic.append(mappings, path)
    elif mode == "w":
        sssom_pydantic.write(
            mappings, path, metadata=metadata, converter=bioregistry.get_default_converter()
        )
    else:
        raise ValueError(f"invalid mode: {mode}")


def load_mappings(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the mappings table."""
    return _load_table(path or POSITIVES_SSSOM_PATH)


def load_mappings_subset(source: str, target: str) -> Mapping[str, str]:
    """Get a dictionary of 1-1 mappings from the source prefix to the target prefix."""
    # TODO replace with SeMRA functionality?
    return {
        mapping.subject.identifier: mapping.object.identifier
        for mapping in load_mappings()
        if mapping.subject.prefix == source and mapping.object.prefix == target
    }


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
    _lint_curated_mappings(path=path or POSITIVES_SSSOM_PATH)


def _lint_curated_mappings(path: Path) -> None:
    """Lint the true mappings file."""
    sssom_pydantic.lint(
        path,
        metadata={"mapping_set_id": f"{PURL_BASE}/{path.name}"},
    )


def load_false_mappings(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the false mappings table."""
    return _load_table(path or NEGATIVES_SSSOM_PATH)


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
    _lint_curated_mappings(
        path=path or NEGATIVES_SSSOM_PATH,
    )


def load_unsure(*, path: Path | None = None) -> list[SemanticMapping]:
    """Load the unsure table."""
    return _load_table(
        path or UNSURE_SSSOM_PATH,
    )


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
    _lint_curated_mappings(
        path=path or UNSURE_SSSOM_PATH,
    )


def load_predictions(*, path: str | Path | None = None) -> list[SemanticMapping]:
    """Load the predictions table."""
    return _load_table(path or PREDICTIONS_SSSOM_PATH)


def write_predictions(
    mappings: Iterable[SemanticMapping],
    *,
    path: Path | None = None,
    exclude_mappings: Iterable[SemanticMapping] | None = None,
) -> None:
    """Write new content to the predictions table."""
    if path is None:
        path = PREDICTIONS_SSSOM_PATH
    _write_helper(
        mappings,
        path,
        mode="w",
        metadata={"mapping_set_id": f"{PURL_BASE}/{path.name}"},
        exclude_mappings=exclude_mappings,
    )


def append_predictions(
    mappings: Iterable[SemanticMapping],
    *,
    path: Path | None = None,
) -> None:
    """Append new lines to the predictions table."""
    if path is None:
        path = PREDICTIONS_SSSOM_PATH

    existing_predicted_mappings = load_predictions(path=path)

    # This line is the only difference from the lint_predictions function
    existing_predicted_mappings.extend(mappings)

    write_predictions(
        existing_predicted_mappings,
        path=path,
        exclude_mappings=[
            *load_mappings(),
            *load_false_mappings(),
            *load_unsure(),
        ],
    )


def lint_predictions(*, path: Path | None = None) -> None:
    """Lint the predictions file, excluding mappings appearing in any curated files."""
    existing_predicted_mappings = load_predictions(path=path)
    write_predictions(
        existing_predicted_mappings,
        path=path,
        exclude_mappings=[
            *load_mappings(),
            *load_false_mappings(),
            *load_unsure(),
        ],
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


def get_curated_filter() -> Mapping[str, Mapping[str, Mapping[str, str]]]:
    """Get a filter over all curated mappings."""
    d: defaultdict[str, defaultdict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    for m in itt.chain(load_mappings(), load_false_mappings(), load_unsure()):
        d[m.subject.prefix][m.object.prefix][m.subject.identifier] = m.object.identifier
    return {k: dict(v) for k, v in d.items()}


def mappings_from_semra(
    mappings: Iterable[semra.Mapping],
    *,
    confidence: float,
) -> list[SemanticMapping]:
    """Get prediction tuples from SeMRA mappings."""
    rows = []
    for mapping in mappings:
        try:
            row = _mapping_from_semra(mapping, confidence)
        except KeyError as e:
            tqdm.write(str(e))
            continue
        rows.append(row)
    return rows


def _mapping_from_semra(mapping: semra.Mapping, confidence: float) -> SemanticMapping:
    """Instantiate from a SeMRA mapping."""
    import pyobo
    import semra

    s_name = mapping.s.name or pyobo.get_name(mapping.s)
    if not s_name:
        raise KeyError(f"could not look up name for {mapping.s.curie}")
    o_name = mapping.o.name or pyobo.get_name(mapping.o)
    if not o_name:
        raise KeyError(f"could not look up name for {mapping.o.curie}")
    # Assume that each mapping has a single simple evidence with a mapping set annotation
    if len(mapping.evidence) != 1:
        raise ValueError
    evidence = mapping.evidence[0]
    if not isinstance(evidence, semra.SimpleEvidence):
        raise TypeError
    if evidence.mapping_set is None:
        raise ValueError
    # TODO what about negative?
    return SemanticMapping(
        subject=mapping.subject,
        predicate=mapping.predicate,
        object=mapping.object,
        justification=evidence.justification,
        confidence=confidence,
        mapping_tool=MappingTool(name=evidence.mapping_set.name),
    )


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
            type=mapping.justification.curie,
            strata=strata,
        )
    return graph
