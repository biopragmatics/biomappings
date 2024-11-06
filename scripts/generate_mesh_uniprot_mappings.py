"""Append lexical mappings between MeSH and UniProt."""

import re
from collections.abc import Iterable

from indra.databases import hgnc_client, mesh_client

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url

MESH_PROTEIN_RE = re.compile(r"^(.+) protein, human$")


def get_mappings() -> Iterable[PredictionTuple]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt human proteins."""
    url = get_script_url(__file__)
    mapping_type = "semapv:LexicalMatching"
    match_type = "skos:exactMatch"
    confidence = 0.999
    for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
        match = MESH_PROTEIN_RE.match(mesh_name)
        if not match:
            continue
        gene_name = match.groups()[0]
        hgnc_id = hgnc_client.get_hgnc_id(gene_name)
        if not hgnc_id:
            continue
        uniprot_id = hgnc_client.get_uniprot_id(hgnc_id)
        if not uniprot_id or "," in uniprot_id:
            continue
        yield PredictionTuple(
            "mesh",
            mesh_id,
            mesh_name,
            match_type,
            "uniprot",
            uniprot_id,
            gene_name,
            mapping_type,
            confidence,
            url,
        )


if __name__ == "__main__":
    append_prediction_tuples(get_mappings())
