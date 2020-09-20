import re
import os
import csv
from subprocess import check_output

GILDA_PATH = os.environ.get('GILDA_PATH')
GILDA_MAPPINGS = os.path.join(GILDA_PATH, 'gilda', 'resources',
                              'mesh_mappings.tsv')


db_ns_mappings = {
    'CHEBI': 'chebi',
    'EFO': 'efo',
    'HP': 'hp',
    'DOID': 'doid',
    'HGNC': 'hgnc',
    'NCIT': 'ncit',
    'GO': 'go',
    'FPLX': 'fplx'
    }


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
    with open(GILDA_MAPPINGS, 'r') as fh:
        for _, mesh_id, mesh_name, db_ns, db_id, db_name \
            in csv.reader(fh, delimiter='\t'):
                yield ('mesh', mesh_id, mesh_name,
                       match_type,
                       db_ns_mappings[db_ns], db_id, db_name,
                       mapping_type, url)