"""Generate mappings using Gilda from EFO to MeSH."""
from collections import Counter

import bioregistry
import gilda
import obonet
from indra.databases import mesh_client
from indra.ontology.standardize import standardize_db_refs
from indra.tools.fix_invalidities import fix_invalidities_db_refs

from biomappings import load_false_mappings, load_mappings, load_unsure
from biomappings.resources import PredictionTuple, append_prediction_tuples

# Get the EFO ontology
g = obonet.read_obo(bioregistry.get_obo_download("EFO"))

# Make sure we know which mappings have already been curated
curated_mappings = set()
for m in list(load_mappings()) + list(load_unsure()) + list(load_false_mappings()):
    if m["source prefix"] == "efo" and m["target prefix"] == "mesh":
        curated_mappings.add(m["source identifier"])
    elif m["target prefix"] == "efo" and m["source prefix"] == "mesh":
        curated_mappings.add(m["target identifier"])


# We now iterate over all efo entries and check for possible mappings
mappings = {}
existing_refs_to_mesh = set()
already_mappable = set()
for node, data in g.nodes(data=True):
    # Skip external entries
    if not node.startswith("EFO"):
        continue
    # Make sure we have a name
    if "name" not in data:
        continue
    # Skip if already curated
    if node in curated_mappings:
        continue
    # Get existing xrefs as a standardized dict
    xrefs = [xref.split(":", maxsplit=1) for xref in data.get("xref", []) if ':' in xref]
    xrefs_dict = fix_invalidities_db_refs(dict(xrefs))
    standard_refs = standardize_db_refs(xrefs_dict)
    # If there are already MESH mappings, we keep track of that
    if "MESH" in standard_refs:
        already_mappable.add(node)
    existing_refs_to_mesh |= {id for ns, id in standard_refs.items() if ns == "MESH"}
    # We can now ground the name and specifically look for MESH matches
    matches = gilda.ground(data["name"], namespaces=["MESH"])
    # If we got a match, we add the MESH ID as a mapping
    if matches:
        for grounding in matches[0].get_groundings():
            if grounding[0] == "MESH":
                mappings[node] = matches[0].term.id


print("Found %d EFO->MESH mappings." % len(mappings))

# We makes sure that (i) the node is not already mappable to MESH and that
# (ii) there isn't some other node that was not already mapped to the
# given MESH ID
mappings = {
    k: v
    for k, v in mappings.items()
    if v not in existing_refs_to_mesh and k not in already_mappable
}

# We now need to make sure that we don't reuse the same MESH ID across
# multiple predicted mappings
cnt = Counter(mappings.values())
mappings = {k: v for k, v in mappings.items() if cnt[v] == 1}

print("Found %d filtered EFO->MESH mappings." % len(mappings))

# We can now add the predictions
predictions = []
for efo_id, mesh_id in mappings.items():
    target_name = g.nodes[efo_id]["name"]
    source_name = mesh_client.get_mesh_name(mesh_id)
    if not source_name or not target_name:
        continue
    pred = PredictionTuple(
        target_prefix="efo",
        target_identifier=efo_id.lower().removeprefix("efo:"),
        target_name=target_name,
        relation="skos:exactMatch",
        source_prefix="mesh",
        source_id=mesh_id,
        source_name=source_name,
        type="semapv:LexicalMatching",
        confidence=0.9,
        source="generate_efo_mesh_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
