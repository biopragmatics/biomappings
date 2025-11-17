"""Generate orthologous relations between Reactome pathways."""

import itertools as itt
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping

import click
import pyobo
from curies import NamableReference, Reference
from curies.vocabulary import structural_matching
from sssom_pydantic import SemanticMapping
from tqdm import tqdm

from biomappings import append_predictions, get_script_url


def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, list[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        species_to_identifiers[identifier.split("-")[-1]].append(identifier)
    return species_to_identifiers


def iterate_orthologous_lexical_matches() -> Iterable[SemanticMapping]:
    """Generate orthologous relations between Reactome pathways."""
    yield from iterate_orthologs("reactome", _get_species_to_identifiers)


def iterate_orthologs(
    prefix: str,
    f: Callable[[Mapping[str, str]], Mapping[str, list[str]]],
) -> Iterable[SemanticMapping]:
    """Iterate over orthologs based on identifier matching."""
    get_script_url(__file__)
    names = pyobo.get_id_name_mapping(prefix)
    parent_identifier_to_species_identifier = f(names)
    count = 0
    for identifiers in tqdm(parent_identifier_to_species_identifier.values()):
        for source_id, target_id in itt.product(identifiers, repeat=2):
            if source_id >= target_id:
                continue
            count += 1
            yield SemanticMapping(
                subject=NamableReference(
                    prefix=prefix, identifier=source_id, name=names[source_id]
                ),
                predicate=Reference.from_curie("RO:HOM0000017"),
                object=NamableReference(prefix=prefix, identifier=target_id, name=names[target_id]),
                justification=structural_matching,
            )
    click.echo(f"[{prefix}] Identified {count} orthologs")


if __name__ == "__main__":
    append_predictions(iterate_orthologous_lexical_matches())
