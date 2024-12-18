"""Generate mappings using Gilda from UBERON to MeSH."""

import gilda
import obonet
from indra.databases import mesh_client

from biomappings.resources import PredictionTuple, append_prediction_tuples

g = obonet.read_obo("/Users/ben/src/uberon/src/ontology/uberon-edit.obo")

mappings = {}
for node, data in g.nodes(data=True):
    if not node.startswith("UBERON"):
        continue
    mesh_refs = [xref for xref in data.get("xref", []) if xref.startswith("MESH")]
    if mesh_refs:
        continue
    matches = gilda.ground(data["name"])
    if matches and matches[0].term.db == "MESH":
        mappings[node] = matches[0].term.id

print(f"Found {len(mappings)} UBERON->MESH mappings.")

predictions = []
for uberon_id, mesh_id in mappings.items():
    pred = PredictionTuple(
        source_prefix="uberon",
        source_id=uberon_id,
        source_name=g.nodes[uberon_id]["name"],
        relation="skos:exactMatch",
        target_prefix="mesh",
        target_identifier=mesh_id,
        target_name=mesh_client.get_mesh_name(mesh_id),
        type="semapv:LexicalMatching",
        confidence=0.9,
        source="generate_uberon_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
