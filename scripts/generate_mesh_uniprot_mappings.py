import re
import os
from subprocess import check_output
from indra.databases import mesh_client, hgnc_client


def get_script_url():
    commit_hash = check_output('git rev-parse HEAD'.split()).\
        decode('utf-8').strip()[:6]
    script_name = os.path.basename(__file__)
    return (f'https://github.com/biomappings/biomappings/blob/{commit_hash}/'
            f'scripts/{script_name}')


def get_mappings():
    url = get_script_url()
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
        match = re.match(r'^(.+) protein, human$', mesh_name)
        if match:
            gene_name = match.groups()[0]
            hgnc_id = hgnc_client.get_hgnc_id(gene_name)
            if hgnc_id:
                uniprot_id = hgnc_client.get_uniprot_id(hgnc_id)
                if uniprot_id:
                    yield ('mesh', mesh_id, mesh_name,
                           match_type,
                           'uniprot', uniprot_id, gene_name,
                           mapping_type, url)