# -*- coding: utf-8 -*-

"""Generate orthologous relations between KEGG pathways."""

import itertools as itt
from collections import defaultdict
from typing import Callable, Iterable, List, Mapping

import pyobo
from tqdm import tqdm

from biomappings.resources import MappingTuple, append_true_mapping_tuples
from biomappings.utils import get_script_url


def iterate_orthologous_lexical_matches() -> Iterable[MappingTuple]:
    """Generate orthologous relations between KEGG pathways."""
    prefix = 'kegg.pathway'
    yield from iterate_orthologs(prefix, _get_species_to_identifiers)


def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, List[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        if identifier.startswith('map'):
            continue
        species_to_identifiers[_get_kegg_id(identifier)].append(identifier)
    return species_to_identifiers


def _get_kegg_id(identifier: str) -> str:
    pos = min(i for i, c in enumerate(identifier) if c.isnumeric())
    return identifier[pos:]


def iterate_orthologs(
    prefix: str,
    f: Callable[[Mapping[str, str]], Mapping[str, List[str]]],
) -> Iterable[MappingTuple]:
    """Iterate over orthologs based on identifier matching."""
    provenance = get_script_url(__file__)
    names = pyobo.get_id_name_mapping(prefix)
    species_to_identifiers = f(names)
    count = 0
    for identifiers in tqdm(species_to_identifiers.values()):
        for source_id, target_id in itt.product(identifiers, identifiers):
            if source_id >= target_id:
                continue
            count += 1
            yield MappingTuple(
                prefix,
                source_id,
                names[source_id],
                'orthologous',
                prefix,
                target_id,
                names[target_id],
                'calculated',
                provenance,
            )
    print(f'Identified {count} orthologs')


if __name__ == '__main__':
    append_true_mapping_tuples(iterate_orthologous_lexical_matches())
