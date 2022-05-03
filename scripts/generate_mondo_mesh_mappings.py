"""Generate mappings using Gilda from MONDO to MeSH."""
from collections import Counter

import gilda
import obonet
from indra.databases import mesh_client

from biomappings.resources import PredictionTuple, append_prediction_tuples

g = obonet.read_obo("http://purl.obolibrary.org/obo/mondo.obo")

mappings = {}
existing_refs_to_mesh = set()
for node, data in g.nodes(data=True):
    if not node.startswith("MONDO"):
        continue
    if 'name' not in data:
        continue
    mesh_refs = [xref[5:] for xref in data.get("xref", []) if xref.startswith("MESH")]
    if mesh_refs:
        existing_refs_to_mesh |= set(mesh_refs)
    matches = gilda.ground(data["name"], namespaces=['MESH'])
    if matches:
        for grounding in matches[0].get_groundings():
            if grounding[0] == 'MESH':
                mappings[node] = matches[0].term.id

print("Found %d MONDO->MESH mappings." % len(mappings))

mappings = {k: v for k, v in mappings.items()
            if v not in existing_refs_to_mesh}

cnt = Counter(mappings.values())

mappings = {k: v for k, v in mappings.items()
            if cnt[v] == 1}

print("Found %d MONDO->MESH mappings." % len(mappings))

predictions = []
for mondo_id, mesh_id in mappings.items():
    pred = PredictionTuple(
        source_prefix="mondo",
        source_id=mondo_id,
        source_name=g.nodes[mondo_id]["name"],
        relation="skos:exactMatch",
        target_prefix="mesh",
        target_identifier=mesh_id,
        target_name=mesh_client.get_mesh_name(mesh_id),
        type="lexical",
        confidence=0.9,
        source="generate_mondo_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
