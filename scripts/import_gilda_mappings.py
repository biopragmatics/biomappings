# -*- coding: utf-8 -*-

"""Append lexical mapping predictions from Gilda."""

import csv
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


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate lexical mappings from Gilda."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    confidence = 0.95
    with open(GILDA_MAPPINGS, 'r') as fh:
        for _, mesh_id, mesh_name, db_ns, db_id, db_name in csv.reader(fh, delimiter='\t'):
            yield (
                'mesh', mesh_id, mesh_name,
                match_type,
                db_ns_mappings[db_ns], db_id, db_name,
                mapping_type, confidence, url,
            )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
