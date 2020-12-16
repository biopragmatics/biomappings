# -*- coding: utf-8 -*-

"""Biomappings resources."""

import csv
import itertools as itt
import os
from typing import Dict, Iterable, List, Mapping, Tuple

from biomappings.utils import iterate_canonical_mappings

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


def _write_helper(lod: Iterable[Mapping[str, str]], path: str, mode: str) -> None:
    with open(path, mode) as file:
        if mode == 'w':
            print(*HEADER, sep='\t', file=file)
        for line in lod:
            print(*[line[k] for k in HEADER], sep='\t', file=file)


def load_mappings() -> List[Dict[str, str]]:
    """Load the mappings table."""
    return _load_table(get_resource_file_path('mappings.tsv'))


def append_true_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the mappings table."""
    _write_helper(m, get_resource_file_path('mappings.tsv'), 'a')


def load_false_mappings() -> List[Dict[str, str]]:
    """Load the false mappings table."""
    return _load_table(get_resource_file_path('incorrect.tsv'))


def append_false_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the false mappings table."""
    _write_helper(m, get_resource_file_path('incorrect.tsv'), 'a')


def load_predictions() -> List[Dict[str, str]]:
    """Load the predictions table."""
    return _load_table(get_resource_file_path('predictions.tsv'))


def write_predictions(m: List[Mapping[str, str]]) -> None:
    """Write new content to the predictions table."""
    _write_helper(m, get_resource_file_path('predictions.tsv'), 'w')


def append_prediction_tuples(m: Iterable[Tuple[str, ...]], deduplicate: bool = True) -> None:
    """Append new lines to the predictions table that come as canonical tuples."""
    append_predictions(
        (
            dict(zip(HEADER, p))
            for p in m
        ),
        deduplicate=deduplicate,
    )


def append_predictions(m: Iterable[Mapping[str, str]], deduplicate: bool = True) -> None:
    """Append new lines to the predictions table."""
    if deduplicate:
        existing = set(iterate_canonical_mappings(itt.chain(
            load_mappings(),
            load_false_mappings(),
            load_predictions(),
        )))

        def _not_duplicate(d: Mapping[str, str]) -> bool:
            source = d['source prefix'], d['source identifier']
            target = d['target prefix'], d['target identifier']
            return (*source, *target) not in existing and (*target, *source) not in existing

        m = (
            d
            for d in m
            if _not_duplicate(d)
        )

    _write_helper(m, get_resource_file_path('predictions.tsv'), 'a')
