# -*- coding: utf-8 -*-

"""Append lexical mappings between MeSH and UniProt."""

import re
from typing import Iterable, Tuple

from indra.databases import hgnc_client, mesh_client

from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

MESH_PROTEIN_RE = re.compile(r'^(.+) protein, human$')


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt human proteins."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
        match = MESH_PROTEIN_RE.match(mesh_name)
        if not match:
            continue
        gene_name = match.groups()[0]
        hgnc_id = hgnc_client.get_hgnc_id(gene_name)
        if not hgnc_id:
            continue
        uniprot_id = hgnc_client.get_uniprot_id(hgnc_id)
        if not uniprot_id or ',' in uniprot_id:
            continue
        yield (
            'mesh', mesh_id, mesh_name,
            match_type,
            'uniprot', uniprot_id, gene_name,
            mapping_type, url,
        )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
