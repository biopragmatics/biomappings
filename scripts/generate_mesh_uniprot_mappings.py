"""Append lexical mappings between MeSH and UniProt."""

import re
from collections.abc import Iterable

import pyobo
from bioregistry import NormalizedNamableReference
from curies.vocabulary import exact_match, lexical_matching_process
from indra.databases import hgnc_client

from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url

MESH_PROTEIN_RE = re.compile(r"^(.+) protein, human$")


def get_mappings() -> Iterable[SemanticMapping]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt human proteins."""
    url = get_script_url(__file__)
    grounder = pyobo.get_grounder("hgnc")
    for mesh_id, mesh_name in pyobo.get_id_name_mapping("mesh").items():
        match = MESH_PROTEIN_RE.match(mesh_name)
        if not match:
            continue
        gene_name = match.groups()[0]

        for mm in grounder.get_matches(gene_name):
            uniprot_id = hgnc_client.get_uniprot_id(mm.identifier)
            if not uniprot_id or "," in uniprot_id:
                continue
            yield SemanticMapping(
                subject=NormalizedNamableReference(
                    prefix="mesh", identifier=mesh_id, name=mesh_name
                ),
                predicate=exact_match,
                object=NormalizedNamableReference(
                    prefix="uniprot", identifier=uniprot_id, name=mm.name
                ),
                justification=lexical_matching_process,
                confidence=mm.score,
                mapping_tool=url,
            )


if __name__ == "__main__":
    append_prediction_tuples(get_mappings())
