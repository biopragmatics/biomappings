"""Generate orthologous relations between Reactome pathways."""

import itertools as itt
from collections import defaultdict
from collections.abc import Iterable, Mapping

import pyobo
from curies import NamableReference
from curies.vocabulary import orthologous_to, structural_matching
from sssom_pydantic import SemanticMapping
from tqdm import tqdm

from biomappings import append_predictions, get_script_url


def iterate_orthologs() -> Iterable[SemanticMapping]:
    """Iterate over Reactome orthologs based on identifier matching."""
    get_script_url(__file__)
    names = pyobo.get_id_name_mapping("reactome")
    parent_identifier_to_species_identifier = _get_species_to_identifiers(names)
    count = 0
    for identifiers in tqdm(parent_identifier_to_species_identifier.values()):
        for source_id, target_id in itt.product(identifiers, repeat=2):
            if source_id >= target_id:
                continue
            count += 1
            yield SemanticMapping(
                subject=NamableReference(
                    prefix="reactome", identifier=source_id, name=names[source_id]
                ),
                predicate=orthologous_to,
                object=NamableReference(
                    prefix="reactome", identifier=target_id, name=names[target_id]
                ),
                justification=structural_matching,
            )


def _get_species_to_identifiers(names: Mapping[str, str]) -> Mapping[str, list[str]]:
    species_to_identifiers = defaultdict(list)
    for identifier in names:
        species_to_identifiers[identifier.split("-")[-1]].append(identifier)
    return species_to_identifiers


if __name__ == "__main__":
    append_predictions(iterate_orthologs())
