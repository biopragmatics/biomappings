"""Append lexical mappings between MeSH and UniProt."""

import re

import pyobo
from curies import NamedReference
from curies.vocabulary import exact_match, lexical_matching_process
from pyobo.struct import has_gene_product
from sssom_curator import Repository
from sssom_pydantic import MappingTool, SemanticMapping

MESH_PROTEIN_RE = re.compile(r"^(.+) protein, human$")


def append_mesh_uniprot(
    repository: Repository, mapping_tool: MappingTool | None = None
) -> list[SemanticMapping]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt human proteins."""
    grounder = pyobo.get_grounder("hgnc")
    hgnc_id_to_uniprot_id = pyobo.get_relation_mapping(
        "hgnc", relation=has_gene_product, target_prefix="uniprot"
    )
    mappings = []
    for mesh_id, mesh_name in pyobo.get_id_name_mapping("mesh").items():
        match = MESH_PROTEIN_RE.match(mesh_name)
        if not match:
            continue
        gene_name = match.groups()[0]
        for gene_reference in grounder.get_matches(gene_name):
            uniprot_id = hgnc_id_to_uniprot_id.get(gene_reference.identifier)
            if not uniprot_id or "," in uniprot_id:
                continue
            mappings.append(
                SemanticMapping(
                    subject=NamedReference(prefix="mesh", identifier=mesh_id, name=mesh_name),
                    predicate=exact_match.curie,
                    object=NamedReference(
                        prefix="uniprot", identifier=uniprot_id, name=gene_reference.name
                    ),
                    justification=lexical_matching_process,
                    confidence=gene_reference.score,
                    mapping_tool=mapping_tool,
                )
            )
    repository.append_predicted_mappings(mappings)


if __name__ == "__main__":
    from biomappings.utils import DEFAULT_REPO, get_script_url

    append_mesh_uniprot(DEFAULT_REPO, mapping_tool=MappingTool(name=get_script_url(__file__)))
