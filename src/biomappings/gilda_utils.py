"""Utilities for generating predictions with lexical predictions."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pyobo
import ssslm
from curies import ReferenceTuple
from tqdm import tqdm

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import CMapping

__all__ = [
    "append_gilda_predictions",
    "filter_custom",
    "filter_existing_xrefs",
    "iter_prediction_tuples",
]

logger = logging.getLogger(__name__)


def append_gilda_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str,
    *,
    relation: str | None = None,
    custom_filter: CMapping | None = None,
    identifiers_are_names: bool = False,
    path: Path | None = None,
) -> None:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param custom_filter: A triple nested dictionary from source prefix to target prefix to source id to target id.
        Any source prefix, target prefix, source id combinations in this dictionary will be filtered.
    :param identifiers_are_names: The source prefix's identifiers should be considered as names
    :param path: A custom path to predictions TSV file
    """
    if isinstance(target_prefixes, str):
        target_prefixes = [target_prefixes]
    grounder = pyobo.get_grounder(target_prefixes)
    predictions = iter_prediction_tuples(
        prefix,
        relation=relation,
        grounder=grounder,
        provenance=provenance,
        identifiers_are_names=identifiers_are_names,
    )
    if custom_filter is not None:
        predictions = filter_custom(predictions, custom_filter)
    predictions = filter_existing_xrefs(predictions, [prefix, *target_prefixes])
    predictions = sorted(predictions, key=lambda t: (t.subject.prefix, t.subject_label))
    tqdm.write(f"[{prefix}] generated {len(predictions):,} predictions")
    append_prediction_tuples(predictions, path=path)


def iter_prediction_tuples(
    prefix: str,
    provenance: str,
    *,
    relation: str | None = None,
    grounder: ssslm.Grounder,
    identifiers_are_names: bool = False,
    strict: bool = False,
) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    if relation is None:
        relation = "skos:exactMatch"
    id_name_mapping = pyobo.get_id_name_mapping(prefix, strict=strict)
    it = tqdm(
        id_name_mapping.items(), desc=f"[{prefix}] lexical tuples", unit_scale=True, unit="name"
    )
    name_prediction_count = 0
    for identifier, name in it:
        for scored_match in grounder.get_matches(name):
            name_prediction_count += 1
            yield PredictionTuple(
                subject_id=f"{prefix}:{identifier}",
                subject_label=name,
                predicate_id=relation,
                object_id=scored_match.curie,
                object_label=cast(str, scored_match.name),
                mapping_justification="semapv:LexicalMatching",
                confidence=round(scored_match.score, 3),
                mapping_tool=provenance,
            )

    tqdm.write(f"[{prefix}] generated {name_prediction_count:,} predictions from names")

    if identifiers_are_names:
        it = tqdm(
            pyobo.get_ids(prefix), desc=f"[{prefix}] lexical tuples", unit_scale=True, unit="id"
        )
        identifier_prediction_count = 0
        for identifier in it:
            for scored_match in grounder.get_matches(identifier):
                name_prediction_count += 1
                yield PredictionTuple(
                    subject_id=f"{prefix}:{identifier}",
                    subject_label=identifier,
                    predicate_id=relation,
                    object_id=scored_match.curie,
                    object_label=cast(str, scored_match.name),
                    mapping_justification="semapv:LexicalMatching",
                    confidence=round(scored_match.score, 3),
                    mapping_tool=provenance,
                )
        tqdm.write(
            f"[{prefix}] generated {identifier_prediction_count:,} predictions from identifiers"
        )


def filter_custom(
    predictions: Iterable[PredictionTuple],
    custom_filter: CMapping,
) -> Iterable[PredictionTuple]:
    """Filter out custom mappings."""
    counter = 0
    for p in predictions:
        if (
            custom_filter.get(p.subject.prefix, {})
            .get(p.object.prefix, {})
            .get(p.subject.identifier)
        ):
            counter += 1
            continue
        yield p
    logger.info("filtered out %d custom mapped matches", counter)


def filter_existing_xrefs(
    predictions: Iterable[PredictionTuple], prefixes: Iterable[str]
) -> Iterable[PredictionTuple]:
    """Filter predictions that match xrefs already loaded through PyOBO."""
    prefixes = set(prefixes)

    entity_to_mapped_prefixes: defaultdict[ReferenceTuple, set[str]] = defaultdict(set)
    for subject_prefix in prefixes:
        for subject_id, target_prefix, object_id in pyobo.get_xrefs_df(subject_prefix).values:
            entity_to_mapped_prefixes[ReferenceTuple(subject_prefix, subject_id)].add(target_prefix)
            entity_to_mapped_prefixes[ReferenceTuple(target_prefix, object_id)].add(subject_prefix)

    n_predictions = 0
    for prediction in tqdm(predictions, desc="filtering predictions"):
        if (
            prediction.object.prefix in entity_to_mapped_prefixes[prediction.subject]
            or prediction.subject.prefix in entity_to_mapped_prefixes[prediction.object]
        ):
            n_predictions += 1
            continue
        yield prediction

    tqdm.write(
        f"filtered out {n_predictions:,} pre-mapped matches",
    )
