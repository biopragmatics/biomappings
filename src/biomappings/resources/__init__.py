"""Biomappings resources."""

from __future__ import annotations

import csv
import getpass
import itertools as itt
import logging
import warnings
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast, overload

from ..utils import CURATORS_PATH, DEFAULT_REPO

if TYPE_CHECKING:
    import networkx
    from bioregistry import NormalizedNamedReference
    from curies import Reference
    from sssom_pydantic import SemanticMapping

__all__ = [
    "append_false_mappings",
    "append_predictions",
    "append_true_mappings",
    "get_curator_names",
    "get_current_curator",
    "get_true_graph",
    "load_curators",
    "load_false_mappings",
    "load_mappings",
    "load_predictions",
    "load_unsure",
]

logger = logging.getLogger(__name__)


def load_mappings() -> list[SemanticMapping]:
    """Load the positive mappings."""
    return DEFAULT_REPO.read_positive_mappings()


def load_false_mappings() -> list[SemanticMapping]:
    """Load the negative mappings."""
    return DEFAULT_REPO.read_negative_mappings()


def load_unsure() -> list[SemanticMapping]:
    """Load the unsure mappings."""
    return DEFAULT_REPO.read_unsure_mappings()


def load_predictions() -> list[SemanticMapping]:
    """Load the predicted mappings."""
    return DEFAULT_REPO.read_predicted_mappings()


def append_true_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Append new lines to the positive mappings document."""
    DEFAULT_REPO.append_positive_mappings(mappings)


def append_false_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Append new lines to the negative mappings document."""
    DEFAULT_REPO.append_negative_mappings(mappings)


def append_predictions(
    new_mappings: Iterable[SemanticMapping],
) -> None:
    """Append new lines to the predicted mappings document."""
    import sssom_pydantic

    path = DEFAULT_REPO.predictions_path

    mappings, converter, metadata = sssom_pydantic.read(path)

    prefixes: set[str] = set()
    for mapping in new_mappings:
        prefixes.update(mapping.get_prefixes())
        mappings.append(mapping)

    for prefix in prefixes:
        if not converter.standardize_prefix(prefix):
            raise NotImplementedError("amending prefixes not yet implemented")

    exclude_mappings = itt.chain.from_iterable(
        sssom_pydantic.read(path)[0] for path in DEFAULT_REPO.curated_paths
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
    from bioregistry import NormalizedNamedReference

    with CURATORS_PATH.open() as file:
        return {
            record["user"]: NormalizedNamedReference(
                prefix="orcid", identifier=record["orcid"], name=record["name"]
            )
            for record in csv.DictReader(file, delimiter="\t")
        }


def get_curator_names() -> dict[str, str]:
    """Get ORCID to name."""
    return {r.identifier: cast(str, r.name) for r in load_curators().values()}


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
    warnings.warn(
        "this function is deprecated, please construct the mappings graph yourself",
        DeprecationWarning,
        stacklevel=2,
    )

    from sssom_curator.export.charts import _graph_from_mappings

    return _graph_from_mappings(load_mappings(), strata="correct", include=include, exclude=exclude)
