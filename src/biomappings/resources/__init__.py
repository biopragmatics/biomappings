# -*- coding: utf-8 -*-

"""Biomappings resources."""

import csv
import itertools as itt
import os
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Sequence

from biomappings.utils import RESOURCE_PATH, get_canonical_tuple

MAPPINGS_HEADER = [
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
PREDICTIONS_HEADER = [
    'source prefix',
    'source identifier',
    'source name',
    'relation',
    'target prefix',
    'target identifier',
    'target name',
    'type',
    'confidence',
    'source',
]


class MappingTuple(NamedTuple):
    """A named tuple class for mappings."""

    source_prefix: str
    source_id: str
    source_name: str
    relation: str
    target_prefix: str
    target_identifier: str
    target_name: str
    type: str
    source: str

    def as_dict(self) -> Mapping[str, str]:
        """Get the mapping tuple as a dictionary."""
        return dict(zip(MAPPINGS_HEADER, self))

    @classmethod
    def from_dict(cls, mapping: Mapping[str, str]) -> 'MappingTuple':
        """Get the mapping tuple from a dictionary."""
        return cls(*[mapping[key] for key in MAPPINGS_HEADER])


class PredictionTuple(NamedTuple):
    """A named tuple class for predictions."""

    source_prefix: str
    source_id: str
    source_name: str
    relation: str
    target_prefix: str
    target_identifier: str
    target_name: str
    type: str
    confidence: float
    source: str

    def as_dict(self) -> Mapping[str, Any]:
        """Get the prediction tuple as a dictionary."""
        return dict(zip(PREDICTIONS_HEADER, self))

    @classmethod
    def from_dict(cls, mapping: Mapping[str, str]) -> 'PredictionTuple':
        """Get the prediction tuple from a dictionary."""
        return cls(*[mapping[key] for key in PREDICTIONS_HEADER])


def get_resource_file_path(fname) -> str:
    """Get a resource by its file name."""
    return os.path.join(RESOURCE_PATH, fname)


def _load_table(fname) -> List[Dict[str, str]]:
    with open(fname, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        header = next(reader)
        return [dict(zip(header, row)) for row in reader]


def _write_helper(header: Sequence[str], lod: Iterable[Mapping[str, str]], path: str, mode: str) -> None:
    with open(path, mode) as file:
        if mode == 'w':
            print(*header, sep='\t', file=file)
        for line in lod:
            print(*[line[k] for k in header], sep='\t', file=file)


def load_mappings() -> List[Dict[str, str]]:
    """Load the mappings table."""
    return _load_table(get_resource_file_path('mappings.tsv'))


def append_true_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the mappings table."""
    _write_helper(MAPPINGS_HEADER, m, get_resource_file_path('mappings.tsv'), 'a')


def append_true_mapping_tuples(mappings: Iterable[MappingTuple]) -> None:
    """Append new lines to the mappings table."""
    append_true_mappings(
        mapping.as_dict()
        for mapping in mappings
    )


def load_false_mappings() -> List[Dict[str, str]]:
    """Load the false mappings table."""
    return _load_table(get_resource_file_path('incorrect.tsv'))


def append_false_mappings(m: Iterable[Mapping[str, str]]) -> None:
    """Append new lines to the false mappings table."""
    _write_helper(MAPPINGS_HEADER, m, get_resource_file_path('incorrect.tsv'), 'a')


def load_predictions() -> List[Dict[str, str]]:
    """Load the predictions table."""
    return _load_table(get_resource_file_path('predictions.tsv'))


def write_predictions(m: List[Mapping[str, str]]) -> None:
    """Write new content to the predictions table."""
    _write_helper(PREDICTIONS_HEADER, m, get_resource_file_path('predictions.tsv'), 'w')


def append_prediction_tuples(prediction_tuples: Iterable[PredictionTuple], deduplicate: bool = True) -> None:
    """Append new lines to the predictions table that come as canonical tuples."""
    append_predictions(
        (
            prediction_tuple.as_dict()
            for prediction_tuple in prediction_tuples
        ),
        deduplicate=deduplicate,
    )


def append_predictions(mappings: Iterable[Mapping[str, str]], deduplicate: bool = True) -> None:
    """Append new lines to the predictions table."""
    if deduplicate:
        existing_mappings = {
            get_canonical_tuple(existing_mapping)
            for existing_mapping in itt.chain(
                load_mappings(),
                load_false_mappings(),
                load_predictions(),
            )
        }
        mappings = (
            mapping
            for mapping in mappings
            if get_canonical_tuple(mapping) not in existing_mappings
        )

    _write_helper(PREDICTIONS_HEADER, mappings, get_resource_file_path('predictions.tsv'), 'a')
