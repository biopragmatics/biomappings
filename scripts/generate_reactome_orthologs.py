# -*- coding: utf-8 -*-

"""Generate orthologous relations between Reactome pathways."""

from collections import defaultdict

from biomappings.resources import append_true_mapping_tuples
import itertools as itt
from typing import Callable, Iterable, List, Mapping
import click
import pyobo
from tqdm import tqdm

from biomappings.resources import MappingTuple
from biomappings.utils import get_script_url

def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, List[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        species_to_identifiers[identifier.split("-")[-1]].append(identifier)
    return species_to_identifiers


def iterate_orthologous_lexical_matches() -> Iterable[MappingTuple]:
    """Generate orthologous relations between Reactome pathways."""
    yield from iterate_orthologs("reactome", _get_species_to_identifiers)


def iterate_orthologs(
    prefix: str,
    f: Callable[[Mapping[str, str]], Mapping[str, List[str]]],
) -> Iterable[MappingTuple]:
    """Iterate over orthologs based on identifier matching."""
    provenance = get_script_url(__file__)
    names = pyobo.get_id_name_mapping(prefix)
    parent_identifier_to_species_identifier = f(names)
    count = 0
    for identifiers in tqdm(parent_identifier_to_species_identifier.values()):
        for source_id, target_id in itt.product(identifiers, repeat=2):
            if source_id >= target_id:
                continue
            count += 1
            yield MappingTuple(
                prefix,
                source_id,
                names[source_id],
                "RO:HOM0000017",
                prefix,
                target_id,
                names[target_id],
                "calculated",
                provenance,
            )
    click.echo(f"[{prefix}] Identified {count} orthologs")


if __name__ == "__main__":
    append_true_mapping_tuples(iterate_orthologous_lexical_matches())
