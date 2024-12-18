"""Generate mappings using Gilda from MONDO to MeSH."""

from collections import Counter

import gilda
import obonet
from indra.databases import mesh_client
from indra.ontology.standardize import standardize_db_refs
from indra.tools.fix_invalidities import fix_invalidities_db_refs

from biomappings import load_mappings
from biomappings.resources import PredictionTuple, append_prediction_tuples

g = obonet.read_obo("http://purl.obolibrary.org/obo/mondo.obo")


curated_mappings = {
    m["source identifier"] for m in load_mappings() if m["source prefix"] == "mondo"
}

mappings = {}
existing_refs_to_mesh = set()
already_mappable = set()
for node, data in g.nodes(data=True):
    if not node.startswith("MONDO"):
        continue
    if "name" not in data:
        continue
    mondo_id = node.split(":", maxsplit=1)[1]
    if mondo_id in curated_mappings:
        continue
    xrefs = [xref.split(":", maxsplit=1) for xref in data.get("xref", [])]
    xrefs_dict = fix_invalidities_db_refs(dict(xrefs))
    standard_refs = standardize_db_refs(xrefs_dict)
    if "MESH" in standard_refs:
        already_mappable.add(node)
    existing_refs_to_mesh |= {id for ns, id in standard_refs.items() if ns == "MESH"}
    matches = gilda.ground(data["name"], namespaces=["MESH"])
    if matches:
        for grounding in matches[0].get_groundings():
            if grounding[0] == "MESH":
                mappings[node] = matches[0].term.id


print(f"Found {len(mappings)} MONDO->MESH mappings.")

mappings = {
    k: v
    for k, v in mappings.items()
    if v not in existing_refs_to_mesh and k not in already_mappable
}

cnt = Counter(mappings.values())

mappings = {k: v for k, v in mappings.items() if cnt[v] == 1}

print(f"Found {len(mappings)} MONDO->MESH mappings.")

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
        type="semapv:LexicalMatching",
        confidence=0.9,
        source="generate_mondo_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
