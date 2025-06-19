"""Generate mappings from CL."""

import re

import gilda
import obonet
from bioregistry import NormalizedNamableReference
from indra.databases import mesh_client

from biomappings.resources import SemanticMapping, append_prediction_tuples

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
    pred = SemanticMapping(
        subject=NormalizedNamableReference(
            prefix="cl",
            identifier=cl_id,
            name=g.nodes[cl_id]["name"],
        ),
        predicate="skos:exactMatch",
        object=NormalizedNamableReference(
            prefix="mesh",
            identifier=mesh_id,
            name=mesh_client.get_mesh_name(mesh_id),
        ),
        mapping_justification="semapv:LexicalMatching",
        confidence=0.9,
        mapping_tool="generate_cl_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
