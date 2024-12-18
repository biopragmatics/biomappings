"""Generate mappings using Gilda from CL to MeSH."""

import re

import gilda
import obonet
from indra.databases import mesh_client

from biomappings.resources import PredictionTuple, append_prediction_tuples

g = obonet.read_obo(
    "https://raw.githubusercontent.com/obophenotype/cell-ontology/master/cl-basic.obo"
)

mesh_tree_pattern = re.compile(r"MESH:[A-Z][0-9]+\.[0-9.]+")
mesh_id_pattern = re.compile(r"MESH:[CD][0-9]+")

mappings = {}
for node, data in g.nodes(data=True):
    if not node.startswith("CL:"):
        continue

    has_mesh_id = False
    for value in [data.get("def", ""), *data.get("synonym", []), *data.get("xref", [])]:
        if re.findall(mesh_tree_pattern, value) or re.findall(mesh_id_pattern, value):
            has_mesh_id = True
            break

    if has_mesh_id:
        continue

    matches = gilda.ground(data["name"])
    if not matches:
        if data["name"].endswith(" cells"):
            matches = gilda.ground(data["name"].replace(" cells", ""))
        elif data["name"].endswith(" cell"):
            matches = gilda.ground(data["name"].replace(" cell", ""))
    if not matches:
        continue

    mesh_ids = set()
    for match in matches:
        groundings = match.get_groundings()
        mesh_ids |= {id for ns, id in groundings if ns == "MESH"}
    if len(mesh_ids) > 1:
        print(f"Multiple MESH IDs for {node}")
    elif len(mesh_ids) == 1:
        mesh_id = next(iter(mesh_ids))
        mappings[node] = mesh_id


print(f"Found {len(mappings)} CL->MESH mappings.")

predictions = []
for cl_id, mesh_id in mappings.items():
    pred = PredictionTuple(
        source_prefix="cl",
        source_id=cl_id,
        source_name=g.nodes[cl_id]["name"],
        relation="skos:exactMatch",
        target_prefix="mesh",
        target_identifier=mesh_id,
        target_name=mesh_client.get_mesh_name(mesh_id),
        type="semapv:LexicalMatching",
        confidence=0.9,
        source="generate_cl_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
