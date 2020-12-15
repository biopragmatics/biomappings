# -*- coding: utf-8 -*-

"""Biomappings resources."""

import csv
import itertools as itt
import os
from typing import Dict, Iterable, List, Mapping

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


def _load_table(fname) -> List[Dict[str, str]]:
    with open(fname, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        header = next(reader)
        return [dict(zip(header, row)) for row in reader]


def _write_table(lod: Iterable[Mapping[str, str]], header, path: str) -> None:
    with open(path, 'w') as file:
        print(*header, sep='\t', file=file)
        for line in lod:
            try:
                parts = [line[k] for k in header]
            except KeyError as e:
                print(e)
                print(line)
                print(header)
                print('\n\n\n\n')
            else:
                print(*parts, sep='\t', file=file)


def load_mappings() -> List[Dict[str, str]]:
    """Load the mappings table."""
    return _load_table(get_resource_file_path('mappings.tsv'))


def write_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Write new content to the mappings table."""
    _write_table(m, HEADER, get_resource_file_path('mappings.tsv'))


def append_true_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the mappings table."""
    write_mappings(itt.chain(load_mappings(), m))


def load_false_mappings() -> List[Dict[str, str]]:
    """Load the false mappings table."""
    return _load_table(get_resource_file_path('incorrect.tsv'))


def write_false_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Write new content to the false mappings table."""
    _write_table(m, HEADER, get_resource_file_path('incorrect.tsv'))


def append_false_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the false mappings table."""
    write_false_mappings(itt.chain(load_false_mappings(), m))


def load_predictions() -> List[Dict[str, str]]:
    """Load the predictions table."""
    return _load_table(get_resource_file_path('predictions.tsv'))


def write_predictions(m: List[Mapping[str, str]]) -> None:
    """Write new content to the predictions table."""
    _write_table(m, HEADER, get_resource_file_path('predictions.tsv'))
