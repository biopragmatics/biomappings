"""Append lexical mapping predictions from Gilda."""

import csv
import os
from collections.abc import Iterable

from biomappings import load_false_mappings, load_mappings
from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url

GILDA_PATH = os.environ.get("GILDA_PATH")
if GILDA_PATH:
    GILDA_MAPPINGS = os.path.join(GILDA_PATH, "gilda", "resources", "mesh_mappings.tsv")
else:
    from gilda.resources import MESH_MAPPINGS_PATH

    GILDA_MAPPINGS = MESH_MAPPINGS_PATH

db_ns_mappings = {
    "CHEBI": "chebi",
    "EFO": "efo",
    "HP": "hp",
    "DOID": "doid",
    "HGNC": "hgnc",
    "NCIT": "ncit",
    "GO": "go",
    "FPLX": "fplx",
    "UP": "uniprot",
    "MESH": "mesh",
}


def get_primary_mappings():
    """Get mappings from primary sources."""
    from indra.resources import load_resource_json

    mappings = set()
    sources = ["efo", "hp", "doid"]
    for source in sources:
        entries = load_resource_json(f"{source}.json")
        for entry in entries:
            for xref in entry.get("xrefs", []):
                if xref["namespace"] != "MESH":
                    continue
                mappings.add(("mesh", xref["id"], source, entry["id"]))
    return mappings


def get_curated_mappings():
    """Get curated mappings."""
    curated_mappings = set()
    for mapping in load_mappings() + load_false_mappings():
        mapping_tuples = {
            (
                mapping["source prefix"],
                mapping["source identifier"],
                mapping["target prefix"],
                mapping["target identifier"],
            ),
            (
                mapping["target prefix"],
                mapping["target identifier"],
                mapping["source prefix"],
                mapping["source identifier"],
            ),
        }
        curated_mappings |= mapping_tuples
    return curated_mappings


def get_mappings() -> Iterable[PredictionTuple]:
    """Iterate lexical mappings from Gilda."""
    url = get_script_url(__file__)
    mapping_type = "semapv:LexicalMatching"
    match_type = "skos:exactMatch"
    confidence = 0.95
    primary_mappings = get_primary_mappings()
    curated_mappings = get_curated_mappings()
    with open(GILDA_MAPPINGS) as fh:
        for _, mesh_id, mesh_name, db_ns, db_id, db_name in csv.reader(fh, delimiter="\t"):
            if ("mesh", mesh_id, db_ns_mappings[db_ns], db_id) in primary_mappings or (
                "mesh",
                mesh_id,
                db_ns_mappings[db_ns],
                db_id,
            ) in curated_mappings:
                continue
            yield PredictionTuple(
                "mesh",
                mesh_id,
                mesh_name,
                match_type,
                db_ns_mappings[db_ns],
                db_id,
                db_name,
                mapping_type,
                confidence,
                url,
            )


if __name__ == "__main__":
    append_prediction_tuples(get_mappings())
