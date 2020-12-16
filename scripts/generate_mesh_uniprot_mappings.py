# -*- coding: utf-8 -*-

"""Append lexical mappings between MeSH and UniProt."""

import os
import re
from subprocess import check_output

from indra.databases import hgnc_client, mesh_client


def get_script_url() -> str:
    """Get the source path for this script."""
    commit_hash = check_output('git rev-parse HEAD'.split()).decode('utf-8').strip()[:6]
    script_name = os.path.basename(__file__)
    return f'https://github.com/biomappings/biomappings/blob/{commit_hash}/scripts/{script_name}'


MESH_PROTEIN_RE = re.compile(r'^(.+) protein, human$')


def get_mappings():
    """Iterate high-confidence lexical mappings between MeSH and UniProt human proteins."""
    url = get_script_url()
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
