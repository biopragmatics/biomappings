"""Generate mappings using Gilda from UBERON to MeSH."""

from collections import Counter

from gilda.api import grounder
from indra.ontology.bio import bio_ontology

from biomappings.resources import PredictionTuple, append_prediction_tuples

if __name__ == "__main__":
    grounder.ground("x")
    ambigs = {
        k: v for k, v in grounder.grounder.entries.items() if len({(vv.db, vv.id) for vv in v}) > 1
    }
    mesh_chebi = [
        v for v in ambigs.values() if len(v) == 2 and {vv.db for vv in v} == {"MESH", "CHEBI"}
    ]
    entries = []
    for mesh_chebi_pair in mesh_chebi:
        for term in mesh_chebi_pair:
            entries.append((term.db, term.id))
    cnt = Counter(entries)
    mesh_chebi_simple = []
    for mesh_chebi_pair in mesh_chebi:
        if any(cnt[(term.db, term.id)] > 1 for term in mesh_chebi_pair):
            continue
        mesh_chebi_simple.append(mesh_chebi_pair)

    print(f"Found {len(mesh_chebi_simple)} CHEBI-MESH mappings.")

    predictions = []
    n_redundant = 0
    for pair in mesh_chebi_simple:
        chebi_term = next(term for term in pair if term.db == "CHEBI")
        mesh_term = next(term for term in pair if term.db == "MESH")

        mappings = bio_ontology.get_mappings("MESH", mesh_term.id)
        if ("CHEBI", chebi_term.id) in mappings:
            n_redundant += 1

        pred = PredictionTuple(
            source_prefix="chebi",
            source_id=chebi_term.id,
            source_name=chebi_term.entry_name,
            relation="skos:exactMatch",
            target_prefix="mesh",
            target_identifier=mesh_term.id,
            target_name=mesh_term.entry_name,
            type="semapv:LexicalMatching",
            confidence=0.95,
            source="generate_chebi_mesh_mappings.py",
        )
        predictions.append(pred)

    print(
        f"A total of {n_redundant} mappings could be indirectly inferred fromINDRA ontology xrefs"
    )
    append_prediction_tuples(predictions, deduplicate=True, sort=True)
