"""Biomappings resources."""

from __future__ import annotations

import csv
import getpass
import itertools as itt
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, overload

import bioregistry
import sssom_pydantic
from bioregistry import NormalizedNamedReference
from curies import NamableReference
from sssom_pydantic.api import CoreSemanticMapping as SemanticMapping
from tqdm.auto import tqdm
from typing_extensions import Literal

from biomappings.utils import (
    CURATORS_PATH,
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
    get_canonical_tuple,
)

if TYPE_CHECKING:
    import semra

__all__ = [
    "SemanticMapping",
    "append_false_mappings",
    "append_prediction_tuples",
    "append_predictions",
    "append_true_mapping_tuples",
    "append_true_mappings",
    "append_unsure_mappings",
    "filter_predictions",
    "get_curated_filter",
    "get_current_curator",
    "load_curators",
    "load_false_mappings",
    "load_mappings",
    "load_mappings_subset",
    "load_predictions",
    "load_unsure",
    "prediction_tuples_from_semra",
    "remove_mappings",
    "write_false_mappings",
    "write_predictions",
    "write_true_mappings",
    "write_unsure_mappings",
]

logger = logging.getLogger(__name__)


class _CuratedTuple(NamedTuple):
    """A tuple for writing manual curations to SSSOM TSV."""

    subject_id: str
    subject_label: str
    predicate_id: str
    object_id: str
    object_label: str
    mapping_justification: str
    author_id: str
    mapping_tool: str
    predicate_modifier: str


class _PredictedTuple(NamedTuple):
    """A tuple for writing predictions to SSSOM TSV."""

    subject_id: str
    subject_label: str
    predicate_id: str
    object_id: str
    object_label: str
    mapping_justification: str
    confidence: str
    mapping_tool: str


def _load_table(path: str | Path, *, standardize: bool) -> list[SemanticMapping]:
    mapping_set_id = f"https://w3id.org/biopragmatics/unresolvable/biomappings/{path.name}"
    rv, _converter = sssom_pydantic.read(
        path,
        metadata={"mapping_set_id": mapping_set_id},
        converter=bioregistry.get_default_converter(),
    )
    reference_cls: type[NamableReference]
    if standardize:
        logger.warning("not implemented yet")
    else:
        pass
    return rv


def _write_helper(
    mappings: Iterable[SemanticMapping],
    path: str | Path,
    mode: Literal["w", "a"],
) -> None:
    mappings = sorted(set(mappings))
    sssom_pydantic.write(mappings, path=path, mode=mode)


def load_mappings(
    *, path: str | Path | None = None, standardize: bool = False
) -> list[SemanticMapping]:
    """Load the mappings table."""
    return _load_table(path or POSITIVES_SSSOM_PATH, standardize=standardize)


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
    standardize: bool = False,
) -> None:
    """Append new lines to the mappings table."""
    if path is None:
        path = POSITIVES_SSSOM_PATH
    _write_helper(mappings, path=path, mode="a")
    if sort:
        lint_true_mappings(path=path, standardize=standardize)


def append_true_mapping_tuples(mappings: Iterable[SemanticMapping]) -> None:
    """Append new lines to the mappings table."""
    append_true_mappings(mappings)


def write_true_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappigns to the true mappings file."""
    _write_helper(mappings, path=path or POSITIVES_SSSOM_PATH, mode="w")


def lint_true_mappings(*, path: Path | None = None, standardize: bool) -> None:
    """Lint the true mappings file."""
    _lint_curated_mappings(path=path or POSITIVES_SSSOM_PATH, standardize=standardize)


def _lint_curated_mappings(path: Path, *, standardize: bool) -> None:
    """Lint the true mappings file."""
    mapping_list = _load_table(path, standardize=standardize)
    mappings = _remove_redundant(mapping_list)
    _write_helper(mappings, path, mode="w")


def load_false_mappings(
    *, path: Path | None = None, standardize: bool = False
) -> list[SemanticMapping]:
    """Load the false mappings table."""
    return _load_table(path or NEGATIVES_SSSOM_PATH, standardize=standardize)


def append_false_mappings(
    mappings: Iterable[SemanticMapping],
    *,
    sort: bool = True,
    path: Path | None = None,
    standardize: bool = False,
) -> None:
    """Append new lines to the false mappings table."""
    if path is None:
        path = NEGATIVES_SSSOM_PATH
    _write_helper(mappings=mappings, path=path, mode="a")
    if sort:
        lint_false_mappings(path=path, standardize=standardize)


def write_false_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappings to the false mappings file."""
    _write_helper(mappings, path or NEGATIVES_SSSOM_PATH, mode="w")


def lint_false_mappings(*, path: Path | None = None, standardize: bool) -> None:
    """Lint the false mappings file."""
    _lint_curated_mappings(path=path or NEGATIVES_SSSOM_PATH, standardize=standardize)


def load_unsure(*, path: Path | None = None, standardize: bool = False) -> list[SemanticMapping]:
    """Load the unsure table."""
    return _load_table(path or UNSURE_SSSOM_PATH, standardize=standardize)


def append_unsure_mappings(
    mappings: Iterable[SemanticMapping],
    *,
    sort: bool = True,
    path: Path | None = None,
    standardize: bool = False,
) -> None:
    """Append new lines to the "unsure" mappings table."""
    if path is None:
        path = UNSURE_SSSOM_PATH
    _write_helper(mappings, path=path, mode="a")
    if sort:
        lint_unsure_mappings(path=path, standardize=standardize)


def write_unsure_mappings(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write mappings to the unsure mappings file."""
    _write_helper(mappings, path or UNSURE_SSSOM_PATH, mode="w")


def lint_unsure_mappings(*, standardize: bool, path: Path | None = None) -> None:
    """Lint the unsure mappings file."""
    _lint_curated_mappings(path=path or UNSURE_SSSOM_PATH, standardize=standardize)


def load_predictions(
    *, path: str | Path | None = None, standardize: bool = False
) -> list[SemanticMapping]:
    """Load the predictions table."""
    return _load_table(path or PREDICTIONS_SSSOM_PATH, standardize=standardize)


def write_predictions(mappings: Iterable[SemanticMapping], *, path: Path | None = None) -> None:
    """Write new content to the predictions table."""
    _write_helper(mappings, path or PREDICTIONS_SSSOM_PATH, mode="w")


def append_prediction_tuples(
    prediction_tuples: Iterable[SemanticMapping],
    *,
    deduplicate: bool = True,
    sort: bool = True,
    path: Path | None = None,
    standardize: bool = False,
) -> None:
    """Append new lines to the predictions table that come as canonical tuples."""
    append_predictions(
        prediction_tuples, deduplicate=deduplicate, sort=sort, path=path, standardize=standardize
    )


def append_predictions(
    mappings: Iterable[SemanticMapping],
    *,
    deduplicate: bool = True,
    sort: bool = True,
    path: Path | None = None,
    standardize: bool = True,
) -> None:
    """Append new lines to the predictions table."""
    if deduplicate:
        existing_mappings = {
            get_canonical_tuple(existing_mapping)
            for existing_mapping in itt.chain(
                load_mappings(),
                load_false_mappings(),
                load_unsure(),
                load_predictions(),
            )
        }
        mappings = (
            mapping for mapping in mappings if get_canonical_tuple(mapping) not in existing_mappings
        )

    if path is None:
        path = PREDICTIONS_SSSOM_PATH
    _write_helper(mappings, path, mode="a")
    if sort:
        lint_predictions(path=path, standardize=standardize)


def lint_predictions(
    *,
    path: Path | None = None,
    additional_curated_mappings: Iterable[SemanticMapping] | None = None,
    standardize: bool,
) -> None:
    """Lint the predictions file.

    1. Make sure there are no redundant rows
    2. Make sure no rows in predictions match a row in the curated files
    3. Make sure it's sorted

    :param path: The path to the predicted mappings
    :param additional_curated_mappings: A list of additional mappings
    """
    mappings = remove_mappings(
        load_predictions(path=path, standardize=standardize),
        itt.chain(
            load_mappings(standardize=standardize),
            load_false_mappings(standardize=standardize),
            load_unsure(standardize=standardize),
            additional_curated_mappings or [],
        ),
    )
    mappings = _remove_redundant(mappings)
    mappings = sorted(mappings)
    write_predictions(mappings, path=path)


def remove_mappings(
    mappings: Iterable[SemanticMapping], mappings_to_remove: Iterable[SemanticMapping]
) -> Iterable[SemanticMapping]:
    """Remove the first set of mappings from the second."""
    skip_tuples = {get_canonical_tuple(mtr) for mtr in mappings_to_remove}
    return (mapping for mapping in mappings if get_canonical_tuple(mapping) not in skip_tuples)


def _remove_redundant(mappings: Iterable[SemanticMapping]) -> Iterable[SemanticMapping]:
    dd = defaultdict(list)
    for mapping in mappings:
        dd[get_canonical_tuple(mapping)].append(mapping)
    return (max(mappings, key=_pick_best) for mappings in dd.values())


def _pick_best(mapping: SemanticMapping) -> int:
    """Assign a value for this mapping.

    :param mapping: A mapping dictionary

    :returns: An integer, where higher means a better choice.

    This function is currently simple, but can later be extended to account for several
    other things including:

    - confidence in the curator
    - prediction methodology
    - date of prediction/curation (to keep the earliest)
    """
    if mapping.author and mapping.author.prefix == "orcid":
        return 1
    return 0


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


def filter_predictions(custom_filter: Mapping[str, Mapping[str, Mapping[str, str]]]) -> None:
    """Filter all the predictions by removing what's in the custom filter then re-write.

    :param custom_filter: A filter 3-dictionary of source prefix to target prefix to
        source identifier to target identifier
    """
    predictions = load_predictions()
    predictions = [
        prediction for prediction in predictions if _check_filter(prediction, custom_filter)
    ]
    write_predictions(predictions)


def _check_filter(
    prediction: SemanticMapping,
    custom_filter: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> bool:
    v = (
        custom_filter.get(prediction.subject.prefix, {})
        .get(prediction.object.prefix, {})
        .get(prediction.subject.identifier)
    )
    return prediction.object.identifier != v


def get_curated_filter() -> Mapping[str, Mapping[str, Mapping[str, str]]]:
    """Get a filter over all curated mappings."""
    d: defaultdict[str, defaultdict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    for m in itt.chain(load_mappings(), load_false_mappings(), load_unsure()):
        d[m.subject.prefix][m.object.prefix][m.subject.identifier] = m.object.identifier
    return {k: dict(v) for k, v in d.items()}


def prediction_tuples_from_semra(
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
    return SemanticMapping(  # type:ignore
        subject=mapping.subject,
        predicate=mapping.predicate,
        object=mapping.object,
        mapping_justification=evidence.justification,
        confidence=confidence,
        mapping_tool=evidence.mapping_set.name,
    )
