import logging
from typing import Iterable, Optional, Tuple, Union

from biomappings.resources import PredictionTuple, append_prediction_tuples
from gilda.grounder import Grounder
from pyobo import get_xref
from pyobo.gilda_utils import get_grounder, iter_gilda_prediction_tuples

logger = logging.getLogger(__name__)


def iter_prediction_tuples(
    prefix: str,
    relation: str,
    provenance: str,
    grounder: Optional[Grounder] = None,
) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    for t in iter_gilda_prediction_tuples(prefix=prefix, relation=relation, grounder=grounder):
        yield PredictionTuple(*t, provenance)


def has_mapping(prefix: str, identifier: str, target_prefix: str) -> bool:
    return get_xref(prefix, identifier, target_prefix) is not None


def filter_premapped(
    tups: Iterable[PredictionTuple],
    source_prefixes: Union[str, Iterable[str]],
    target_prefixes: Union[str, Iterable[str]],
) -> Iterable[PredictionTuple]:
    source_prefixes = {source_prefixes} if isinstance(source_prefixes, str) else set(source_prefixes)
    target_prefixes = {target_prefixes} if isinstance(target_prefixes, str) else set(target_prefixes)
    counter = 0
    for t in tups:
        if (
            t.source_prefix in source_prefixes
            and t.target_prefix in target_prefixes
            and has_mapping(t.source_prefix, t.source_id, t.target_prefix)
        ):
            counter += 1
            continue
        yield t
    logger.info('filtered out %d pre-mapped matches', counter)


def append_gilda_predictions(
    prefix: str, target_prefixes: Union[str, Iterable[str]], provenance, rel="skos:exactMatch"
) -> None:
    grounder = get_grounder(target_prefixes)
    it = iter_prediction_tuples(
        prefix, relation=rel, grounder=grounder, provenance=provenance
    )
    it = filter_premapped(it, prefix, target_prefixes)
    it = sorted(it, key=_key)
    append_prediction_tuples(it)


def _key(t: PredictionTuple) -> Tuple[str, str]:
    return t.source_prefix, t.source_name
