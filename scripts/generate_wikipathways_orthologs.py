"""Generate orthologous relations between WikiPathways."""

import itertools as itt
from collections.abc import Iterable

import pyobo
from bioregistry import NormalizedNamableReference
from gilda.process import normalize
from tqdm import tqdm

from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url


def _lexical_exact_match(name1: str, name2: str) -> bool:
    return normalize(name1) == normalize(name2)


def iterate_orthologous_lexical_matches(prefix: str = "wikipathways") -> Iterable[SemanticMapping]:
    """Generate orthologous relations between lexical matches from different species."""
    names = pyobo.get_id_name_mapping(prefix)
    species = pyobo.get_id_species_mapping(prefix)
    provenance = get_script_url(__file__)

    count = 0
    it = itt.combinations(sorted(names.items()), 2)
    it = tqdm(
        it,
        unit_scale=True,
        unit="pair",
        total=len(names) * (len(names) - 1) / 2,
    )
    for (source_id, source_name), (target_id, target_name) in sorted(it):
        source_species = species[source_id]
        target_species = species[target_id]
        if source_species == target_species:
            continue
        if _lexical_exact_match(source_name, target_name):
            count += 1
            yield SemanticMapping(
                subject=NormalizedNamableReference(
                    prefix=prefix, identifier=source_id, name=source_name
                ),
                predicate="RO:HOM0000017",
                object=NormalizedNamableReference(
                    prefix=prefix,
                    identifier=target_id,
                    name=target_name,
                ),
                mapping_justification="semapv:LexicalMatching",
                confidence=0.95,
                mapping_tool=provenance,
            )
    tqdm.write(f"Identified {count:,} orthologs")


if __name__ == "__main__":
    append_prediction_tuples(iterate_orthologous_lexical_matches())
