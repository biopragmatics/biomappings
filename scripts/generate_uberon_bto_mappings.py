"""Generate mappings using Gilda from UBERON to BTO."""

import obonet
from gilda import Term, make_grounder
from gilda.process import normalize

from biomappings.resources import PredictionTuple, append_prediction_tuples

uberon_graph = obonet.read_obo("/Users/ben/src/uberon/src/ontology/uberon-edit.obo")
bto_graph = obonet.read_obo("/Users/ben/src/BTO/bto.obo")


terms = []
for node, data in bto_graph.nodes(data=True):
    prefix, id_stub = node.split(":", maxsplit=1)
    identifier = node
    term = Term(
        normalize(data["name"]), data["name"], prefix, identifier, data["name"], "name", "bto"
    )
    terms.append(term)

grounder = make_grounder(terms)

mappings = {}
bto_used = set()
for node, data in uberon_graph.nodes(data=True):
    if not node.startswith("UBERON"):
        continue
    bto_refs = [xref for xref in data.get("xref", []) if xref.startswith("BTO")]
    bto_used |= set(bto_refs)
    if bto_refs:
        continue
    matches = grounder.ground(data["name"])
    if matches and matches[0].term.db == "BTO":
        mappings[node] = matches[0].term.id

print("Found %d existing UBERON->BTO mappings." % len(bto_used))
print("Predicted %d new UBERON->BTO mappings." % len(mappings))

predictions = []
for uberon_id, bto_id in mappings.items():
    if bto_id in bto_used:
        continue
    pred = PredictionTuple(
        source_prefix="uberon",
        source_id=uberon_id,
        source_name=uberon_graph.nodes[uberon_id]["name"],
        relation="skos:exactMatch",
        target_prefix="bto",
        target_identifier=bto_id,
        target_name=bto_graph.nodes[bto_id]["name"],
        type="semapv:LexicalMatching",
        confidence=0.9,
        source="generate_uberon_bto_mappings.py",
    )
    predictions.append(pred)

append_prediction_tuples(predictions, deduplicate=True, sort=True)
