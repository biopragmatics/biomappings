# -*- coding: utf-8 -*-

"""Biomappings resources."""

import csv
import os
from typing import List, Mapping

RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))
HEADER = [
    'source prefix',
    'source identifier',
    'source name',
    'relation',
    'target prefix',
    'target identifier',
    'target name',
    'type',
    'source',
]


def get_resource_file_path(fname) -> str:
    """Get a resource by its file name."""
    return os.path.join(RESOURCE_PATH, fname)


def _load_table(fname) -> List[Mapping[str, str]]:
    with open(fname, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        header = next(reader)
        return [dict(zip(header, row)) for row in reader]


def _write_table(lod: List[Mapping[str, str]], path: str) -> None:
    with open(path, 'w') as file:
        print(*HEADER, sep='\t', file=file)
        for line in lod:
            print(*[line[k] for k in HEADER], sep='\t', file=file)


def write_mappings(m) -> List[Mapping[str, str]]:
    _write_table(m, get_resource_file_path('mappings.tsv'))


def load_mappings() -> List[Mapping[str, str]]:
    """Load the mappings table."""
    return _load_table(get_resource_file_path('mappings.tsv'))


def load_predictions() -> List[Mapping[str, str]]:
    """Load the predictions table."""
    return _load_table(get_resource_file_path('predictions.tsv'))


def write_predictions(m: List[Mapping[str, str]]) -> None:
    _write_table(m, get_resource_file_path('predictions.tsv'))
