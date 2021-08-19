# -*- coding: utf-8 -*-

"""Generate orthologous relations between KEGG pathways."""

from collections import defaultdict
from typing import Iterable, List, Mapping

from biomappings.orthologs import iterate_orthologs
from biomappings.resources import MappingTuple, append_true_mapping_tuples


def iterate_orthologous_lexical_matches() -> Iterable[MappingTuple]:
    """Generate orthologous relations between KEGG pathways."""
    prefix = "kegg.pathway"
    yield from iterate_orthologs(prefix, _get_species_to_identifiers)


def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, List[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        if identifier.startswith("map"):
            continue
        species_to_identifiers[_get_kegg_id(identifier)].append(identifier)
    return species_to_identifiers


def _get_kegg_id(identifier: str) -> str:
    pos = min(i for i, c in enumerate(identifier) if c.isnumeric())
    return identifier[pos:]


if __name__ == "__main__":
    append_true_mapping_tuples(iterate_orthologous_lexical_matches())
