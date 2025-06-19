"""Generate mappings from AGRO to AGROVOC.

Note: this script requires a minimum of PyOBO v0.7.0 to run.
"""

import time

import pyobo
from bioregistry import NormalizedNamableReference
from pyobo.sources.agrovoc import ensure_agrovoc_graph
from tqdm import tqdm

from biomappings import SemanticMapping
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

AGROVOC_VERSION = "2021-12-02"
QUERY = """
SELECT ?id ?label {
    ?term skosxl:prefLabel / skosxl:literalForm ?label .
    OPTIONAL { ?term skos:scopeNote ?description } .
    FILTER (lang(?label) = 'en') .
    FILTER (strStarts(str(?term), "http://aims.fao.org/aos/agrovoc/c_")) .
    BIND(strafter(str(?term), "_") as ?id)
}
"""


def main():
    """Generate mappings from AGRO to AGROVOC."""
    provenance = get_script_url(__file__)
    grounder = pyobo.get_grounder("AGRO")
    print("got grounder for AGRO", grounder)
    t = time.time()
    graph = ensure_agrovoc_graph(AGROVOC_VERSION)
    print(
        f"got RDF graph for AGROVOC {graph} with {len(graph)} triples in {time.time() - t:.2f} seconds"
    )
    rows = []
    for identifier, name in tqdm(graph.query(QUERY)):
        for scored_match in grounder.get_matches(name):
            rows.append(
                SemanticMapping(
                    subject=NormalizedNamableReference(
                        prefix="agrovoc", identifier=identifier, name=name
                    ),
                    predicate=NormalizedNamableReference.from_curie("skos:exactMatch"),
                    object=scored_match.reference,
                    mapping_justification=NormalizedNamableReference.from_curie(
                        "semapv:LexicalMatching"
                    ),
                    confidence=scored_match.score,
                    mapping_tool=provenance,
                )
            )
    append_prediction_tuples(rows)


if __name__ == "__main__":
    main()
