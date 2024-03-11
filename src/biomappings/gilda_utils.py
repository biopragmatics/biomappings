# -*- coding: utf-8 -*-

"""Utilities for generating predictions with pyobo/gilda."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

import bioregistry
import pyobo
import pyobo.gilda_utils
from gilda.grounder import Grounder

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import CMapping

__all__ = [
    "append_gilda_predictions",
    "iter_prediction_tuples",
    "filter_custom",
    "filter_existing_xrefs",
    "has_mapping",
]

logger = logging.getLogger(__name__)


def append_gilda_predictions(
    prefix: str,
    target_prefixes: Union[str, Iterable[str]],
    provenance: str,
    *,
    relation: str = "skos:exactMatch",
    custom_filter: Optional[CMapping] = None,
    unnamed: Optional[Iterable[str]] = None,
    identifiers_are_names: bool = False,
    path: Optional[Path] = None,
) -> None:
    """Add gilda predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param custom_filter: A triple nested dictionary from source prefix to target prefix to source id to target id.
        Any source prefix, target prefix, source id combinations in this dictionary will be filtered.
    :param unnamed: An optional list of prefixes whose identifiers should be considered as names (e.g., CCLE, FPLX)
    :param identifiers_are_names: The source prefix's identifiers should be considered as names
    :param path: A custom path to predictions TSV file
    """
    if isinstance(target_prefixes, str):
        target_prefixes = [target_prefixes]
    grounder = pyobo.gilda_utils.get_grounder(target_prefixes, unnamed=unnamed)
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
    predictions = sorted(predictions, key=_key)
    append_prediction_tuples(predictions, path=path)


def iter_prediction_tuples(
    prefix: str,
    provenance: str,
    *,
    relation: str = "skos:exactMatch",
    grounder: Optional[Grounder] = None,
    identifiers_are_names: bool = False,
) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    for t in pyobo.gilda_utils.iter_gilda_prediction_tuples(
        prefix=prefix,
        relation=relation,
        grounder=grounder,
        identifiers_are_names=identifiers_are_names,
    ):
        yield PredictionTuple(*t, provenance)  # type: ignore


def filter_custom(
    predictions: Iterable[PredictionTuple],
    custom_filter: CMapping,
) -> Iterable[PredictionTuple]:
    """Filter out custom mappings."""
    counter = 0
    for p in predictions:
        if custom_filter.get(p.source_prefix, {}).get(p.target_prefix, {}).get(p.source_id):
            counter += 1
            continue
        yield p
    logger.info("filtered out %d custom mapped matches", counter)


def filter_existing_xrefs(
    predictions: Iterable[PredictionTuple], prefixes: Iterable[str]
) -> Iterable[PredictionTuple]:
    """Filter predictions that match xrefs already loaded through PyOBO."""
    prefixes = set(prefixes)

    entity_to_mapped_prefixes = defaultdict(set)
    for prefix in prefixes:
        for source_id, target_prefix, target_id in pyobo.get_xrefs_df(prefix).values:
            entity_to_mapped_prefixes[prefix, source_id].add(target_prefix)
            entity_to_mapped_prefixes[target_prefix, target_id].add(prefix)

    counter = 0
    for prediction in predictions:
        source_id = bioregistry.standardize_identifier(
            prediction.source_prefix, prediction.source_id
        )
        target_id = bioregistry.standardize_identifier(
            prediction.target_prefix, prediction.target_identifier
        )
        if (
            prediction.target_prefix
            in entity_to_mapped_prefixes[prediction.source_prefix, source_id]
            or prediction.source_prefix
            in entity_to_mapped_prefixes[prediction.target_prefix, target_id]
        ):
            counter += 1
            continue
        yield prediction
    logger.info("filtered out %d pre-mapped matches", counter)


def has_mapping(prefix: str, identifier: str, target_prefix: str) -> bool:
    """Check if there's already a mapping available for this entity in a target namespace."""
    return pyobo.get_xref(prefix, identifier, target_prefix) is not None


def _key(t: PredictionTuple) -> Tuple[str, str]:
    return t.source_prefix, t.source_name
