# -*- coding: utf-8 -*-

"""Append lexical mapping predictions from Gilda."""

import csv
import json
import os
from typing import Iterable, Tuple

from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

GILDA_PATH = os.environ.get('GILDA_PATH')
GILDA_MAPPINGS = os.path.join(GILDA_PATH, 'gilda', 'resources', 'mesh_mappings.tsv')

db_ns_mappings = {
    'CHEBI': 'chebi',
    'EFO': 'efo',
    'HP': 'hp',
    'DOID': 'doid',
    'HGNC': 'hgnc',
    'NCIT': 'ncit',
    'GO': 'go',
    'FPLX': 'fplx',
}


def get_primary_mappings():
    """Get mappings from primary sources"""
    from indra.resources import load_resource_json
    mappings = set()
    sources = ['efo', 'hp', 'doid']
    for source in sources:
        entries = load_resource_json(f'{source}.json')
        for entry in entries:
            for xref in entry.get('xrefs', []):
                if xref['namespace'] != 'MESH':
                    continue
                mappings.add(('mesh', xref['id'], source, entry['id']))
    return mappings


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate lexical mappings from Gilda."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    confidence = 0.95
    primary_mappings = get_primary_mappings()
    with open(GILDA_MAPPINGS, 'r') as fh:
        for _, mesh_id, mesh_name, db_ns, db_id, db_name in csv.reader(fh, delimiter='\t'):
            if ('mesh', mesh_id, db_ns, db_id) in primary_mappings:
                continue
            yield (
                'mesh', mesh_id, mesh_name,
                match_type,
                db_ns_mappings[db_ns], db_id, db_name,
                mapping_type, confidence, url,
            )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
