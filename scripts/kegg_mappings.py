"""Generate mappings."""

from collections.abc import Iterable

import bioversions
import pyobo
from bioregistry import NormalizedNamableReference
from pyobo.sources.kegg.api import ensure_list_pathways
from tqdm import tqdm

from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url


def iterate_kegg_matches() -> Iterable[SemanticMapping]:
    """Iterate over predictions from KEGG Pathways to GO and MeSH."""
    provenance = get_script_url(__file__)
    id_name_mapping = ensure_list_pathways(bioversions.get_version("kegg", strict=True))
    grounder = pyobo.get_grounder({"go", "mesh"})
    for identifier, name in tqdm(id_name_mapping.items(), desc="Mapping KEGG Pathways"):
        for match in grounder.get_matches(name):
            if match.term.db.lower() not in {"go", "mesh"}:
                continue

            yield SemanticMapping(
                subject=NormalizedNamableReference(
                    prefix="kegg.pathway", identifier=identifier, name=name
                ),
                predicate="skos:exactMatch",
                object=match.reference,
                mapping_justification="semapv:LexicalMatching",
                confidence=match.score,
                mapping_tool=provenance,
            )


if __name__ == "__main__":
    append_prediction_tuples(iterate_kegg_matches())
