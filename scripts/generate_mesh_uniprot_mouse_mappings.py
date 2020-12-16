# -*- coding: utf-8 -*-

"""Append lexical mappings between MeSH and UniProt for mouse genes."""

import re
from typing import Iterable, Tuple

import pyobo
from indra.databases import mesh_client

from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

mgi_name_to_id = pyobo.get_name_id_mapping('mgi')


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt mouse proteins."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    confidence = 0.999
    mesh_protein_re = re.compile(r'^(.+) protein, mouse$')
    for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
        match = mesh_protein_re.match(mesh_name)
        if not match:
            continue
        gene_name = match.groups()[0]
        mgi_id = mgi_name_to_id.get(gene_name)
        if not mgi_id:
            continue
        # uniprot_id = hgnc_client.get_uniprot_id(mgi_id)
        # if not uniprot_id or ',' in uniprot_id:
        #    continue
        yield (
            'mesh', mesh_id, mesh_name,
            match_type,
            'mgi', mgi_id, gene_name,
            mapping_type, confidence, url,
        )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
