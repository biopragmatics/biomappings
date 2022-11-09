# -*- coding: utf-8 -*-

"""Utilities for generating predictions with pyobo/gilda."""

import logging
from typing import Iterable, Mapping, Optional, Tuple, Union

from gilda.grounder import Grounder
from pyobo import get_xref
from pyobo.gilda_utils import get_grounder, iter_gilda_prediction_tuples

from biomappings.resources import PredictionTuple, append_prediction_tuples

logger = logging.getLogger(__name__)

CMapping = Mapping[str, Mapping[str, Mapping[str, str]]]


def append_gilda_predictions(
    prefix: str,
    target_prefixes: Union[str, Iterable[str]],
    provenance: str,
    *,
    relation: str = "skos:exactMatch",
    custom_filter: Optional[CMapping] = None,
    unnamed: Optional[Iterable[str]] = None,
    identifiers_are_names: bool = False,
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
    """
    grounder = get_grounder(target_prefixes, unnamed=unnamed)
    predictions = iter_prediction_tuples(
        prefix,
        relation=relation,
        grounder=grounder,
        provenance=provenance,
        identifiers_are_names=identifiers_are_names,
    )
    if custom_filter is not None:
        predictions = filter_custom(predictions, custom_filter)
    predictions = filter_pyobo(predictions, prefix, target_prefixes)
    predictions = sorted(predictions, key=_key)
    append_prediction_tuples(predictions)


def iter_prediction_tuples(
    prefix: str,
    provenance: str,
    *,
    relation: str = "skos:exactMatch",
    grounder: Optional[Grounder] = None,
    identifiers_are_names: bool = False,
) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    for t in iter_gilda_prediction_tuples(
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


def filter_pyobo(
    predictions: Iterable[PredictionTuple],
    source_prefixes: Union[str, Iterable[str]],
    target_prefixes: Union[str, Iterable[str]],
) -> Iterable[PredictionTuple]:
    """Filter predictions that match xrefs already loaded through PyOBO."""
    source_prefixes = (
        {source_prefixes} if isinstance(source_prefixes, str) else set(source_prefixes)
    )
    target_prefixes = (
        {target_prefixes} if isinstance(target_prefixes, str) else set(target_prefixes)
    )
    counter = 0
    for prediction in predictions:
        if (
            prediction.source_prefix in source_prefixes
            and prediction.target_prefix in target_prefixes
            and isinstance(prediction.source_id, str)
            and has_mapping(
                prediction.source_prefix, prediction.source_id, prediction.target_prefix
            )
        ):
            counter += 1
            continue
        yield prediction
    logger.info("filtered out %d pre-mapped matches", counter)


def has_mapping(prefix: str, identifier: str, target_prefix: str) -> bool:
    """Check if there's already a mapping available for this entity in a target namespace."""
    return get_xref(prefix, identifier, target_prefix) is not None


def _key(t: PredictionTuple) -> Tuple[str, str]:
    return t.source_prefix, t.source_name
