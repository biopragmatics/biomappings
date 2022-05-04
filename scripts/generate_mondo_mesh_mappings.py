"""Generate mappings using Gilda from MONDO to MeSH."""
from collections import Counter

import gilda
import obonet
from indra.databases import mesh_client
from indra.ontology.standardize import standardize_db_refs

from biomappings.resources import PredictionTuple, append_prediction_tuples

g = obonet.read_obo("http://purl.obolibrary.org/obo/mondo.obo")

mappings = {}
existing_refs_to_mesh = set()
already_mappable = set()
for node, data in g.nodes(data=True):
    if not node.startswith("MONDO"):
        continue
    if "name" not in data:
        continue
    xrefs = [xref.split(':', maxsplit=1) for xref in data.get("xref", [])]
    xrefs_dict = dict(xrefs)
    standard_refs = standardize_db_refs(xrefs_dict)
    if 'MESH' in standard_refs:
        already_mappable.add(node)
    existing_refs_to_mesh |= {id for ns, id in standard_refs.items() if ns == 'MESH'}
    matches = gilda.ground(data["name"], namespaces=["MESH"])
    if matches:
        for grounding in matches[0].get_groundings():
            if grounding[0] == "MESH":
                mappings[node] = matches[0].term.id

print("Found %d MONDO->MESH mappings." % len(mappings))

mappings = {k: v for k, v in mappings.items() if v not in existing_refs_to_mesh
            and k not in already_mappable}

cnt = Counter(mappings.values())

mappings = {k: v for k, v in mappings.items() if cnt[v] == 1}

print("Found %d MONDO->MESH mappings." % len(mappings))

predictions = []
for mondo_id, mesh_id in mappings.items():
    pred = PredictionTuple(
        source_prefix="mondo",
        source_id=mondo_id[6:],
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
