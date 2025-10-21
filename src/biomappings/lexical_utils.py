"""Utilities for working with semantic mappings."""

from __future__ import annotations

import itertools as itt
from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast

from sssom_pydantic import SemanticMapping

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison

__all__ = [
    "CanonicalMappingTuple",
    "SemanticMappingHasher",
    "drop_duplicates",
    "get_canonical_tuple",
    "remove_redundant_external",
]

#: A canonical mapping tuple
CanonicalMappingTuple: TypeAlias = tuple[str, str, str, str]

X = TypeVar("X")

#: A function that constructs a hashable object from a semantic mapping
SemanticMappingHasher: TypeAlias = Callable[[SemanticMapping], X]

#: A function that makes a comparable score for a semantic mapping
SemanticMappingScorer: TypeAlias = Callable[[SemanticMapping], "SupportsRichComparison"]


def drop_duplicates(
    mappings: Iterable[SemanticMapping],
    *,
    key: SemanticMappingHasher[X] | None = None,
    scorer: SemanticMappingScorer | None = None,
) -> list[SemanticMapping]:
    """Remove redundant mappings.

    :param mappings: An iterable of mappings
    :param key: A function that hashes the mappings. If not given, will
        only use the subject/object to has the mapping.
    :param scorer: A function that gives a score to a given mapping,
        where a higher score means it's more likely to be kept.
        Any function returning a comparable value can be used, but
        int/float are the easiest to understand.

    :returns: A list of mappings that have had duplicates dropped. This
        does not necessarily maintain order, since dictionary-based
        aggregation happens in the implementation.
    """
    if key is None:
        key = cast(SemanticMappingHasher[X], get_canonical_tuple)

    if scorer is None:
        scorer = _score_mapping

    key_to_mappings: defaultdict[X, list[SemanticMapping]] = defaultdict(list)
    for mapping in mappings:
        key_to_mappings[key(mapping)].append(mapping)
    return [max(mappings, key=scorer) for mappings in key_to_mappings.values()]


def _score_mapping(mapping: SemanticMapping) -> int:
    """Assign a value for this mapping, where higher is better.

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


def get_canonical_tuple(mapping: SemanticMapping) -> CanonicalMappingTuple:
    """Get the canonical tuple from a mapping entry."""
    source, target = sorted([mapping.subject, mapping.object])
    return source.prefix, source.identifier, target.prefix, target.identifier


def remove_redundant_external(
    mappings: Iterable[SemanticMapping],
    *others: Iterable[SemanticMapping],
    key: SemanticMappingHasher[X] | None = None,
) -> list[SemanticMapping]:
    """Remove mappings with same S/O pairs in other given mappings."""
    keep_mapping_predicate = _get_predicate_helper(*others, key=key)
    return [m for m in mappings if keep_mapping_predicate(m)]


def _get_predicate_helper(
    *mappings: Iterable[SemanticMapping],
    key: SemanticMappingHasher[X] | None = None,
) -> Callable[[SemanticMapping], bool]:
    """Construct a predicate for mapping membership.

    :param mappings: A variadic number of mapping lists, which are all indexed
    :param key: A function that hashes a given semantic mapping. If not given, one
        that uses the combination of subject + object will be used.
    :returns: A predicate that can be used to check if new mappings are already
        in the given mapping list(s)
    """
    if key is None:
        key = cast(SemanticMappingHasher[X], get_canonical_tuple)

    skip_tuples: set[X] = {key(mapping) for mapping in itt.chain.from_iterable(mappings)}

    def _keep_mapping(mapping: SemanticMapping) -> bool:
        return key(mapping) not in skip_tuples

    return _keep_mapping
