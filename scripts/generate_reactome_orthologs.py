# -*- coding: utf-8 -*-

"""Generate orthologous relations between Reactome pathways."""

from collections import defaultdict
from typing import Iterable, List, Mapping

from biomappings.resources import MappingTuple, append_true_mapping_tuples
from scripts.generate_kegg_orthologs import iterate_orthologs


def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, List[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        species_to_identifiers[identifier.split('-')[-1]].append(identifier)
    return species_to_identifiers


def iterate_orthologous_lexical_matches() -> Iterable[MappingTuple]:
    """Generate orthologous relations between Reactome pathways."""
    prefix = 'reactome'
    yield from iterate_orthologs(prefix, _get_species_to_identifiers)


if __name__ == '__main__':
    append_true_mapping_tuples(iterate_orthologous_lexical_matches())
