# -*- coding: utf-8 -*-

"""Append lexical mappings between MeSH and other gene/protein vocabularies."""

import re
from typing import Iterable, Tuple

from indra.databases import mesh_client

import pyobo
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

MAP = {
    # 'human': 'hgnc',
    'mouse': 'mgi',
    'Arabidopsis': ...,
    'rat': 'rgd',
    'S cerevisiae': 'sgd',
    'Drosophila': 'fb',
    'C elegans': ...,
    'E coli': ...,
    'zebrafish': 'zfa',
}


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt mouse proteins."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    confidence = 0.999

    for suffix, key in MAP.items():
        if key is ...:
            continue
        try:
            name_to_id_mapping = pyobo.get_name_id_mapping(key)
        except ValueError:
            print('skipping', key)
            continue
        mesh_protein_re = re.compile(rf'^(.+) protein, {suffix}$')
        for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
            match = mesh_protein_re.match(mesh_name)
            if not match:
                continue
            gene_name = match.groups()[0]
            identifier = name_to_id_mapping.get(gene_name)
            if not identifier:
                continue
            # uniprot_id = hgnc_client.get_uniprot_id(mgi_id)
            # if not uniprot_id or ',' in uniprot_id:
            #    continue
            yield (
                'mesh', mesh_id, mesh_name,
                match_type,
                key, identifier, gene_name,
                mapping_type, confidence, url,
            )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
