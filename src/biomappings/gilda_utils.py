# -*- coding: utf-8 -*-

"""Utilities for generating predictions with pyobo/gilda."""

import logging
from typing import Iterable, Optional, Tuple, Union

from gilda.grounder import Grounder
from pyobo import get_xref
from pyobo.gilda_utils import get_grounder, iter_gilda_prediction_tuples

from biomappings.resources import PredictionTuple, append_prediction_tuples

logger = logging.getLogger(__name__)


def append_gilda_predictions(
    prefix: str,
    target_prefixes: Union[str, Iterable[str]],
    provenance: str,
    relation: str = "skos:exactMatch",
) -> None:
    """Add gilda predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    """
    grounder = get_grounder(target_prefixes)
    it = iter_prediction_tuples(prefix, relation=relation, grounder=grounder, provenance=provenance)
    it = filter_premapped(it, prefix, target_prefixes)
    it = sorted(it, key=_key)
    append_prediction_tuples(it)


def iter_prediction_tuples(
    prefix: str,
    relation: str,
    provenance: str,
    grounder: Optional[Grounder] = None,
) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    for t in iter_gilda_prediction_tuples(prefix=prefix, relation=relation, grounder=grounder):
        yield PredictionTuple(*t, provenance)


def filter_premapped(
    predictions: Iterable[PredictionTuple],
    source_prefixes: Union[str, Iterable[str]],
    target_prefixes: Union[str, Iterable[str]],
) -> Iterable[PredictionTuple]:
    """Filter pre-mapped predictions."""
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
