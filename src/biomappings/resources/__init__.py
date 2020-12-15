# -*- coding: utf-8 -*-

"""Biomappings resources."""

import csv
import os

RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_resource_file_path(fname):
    """Get a resource by its file name."""
    return os.path.join(RESOURCE_PATH, fname)


def _load_table(fname):
    with open(fname, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        header = next(reader)
        return [dict(zip(header, row)) for row in reader]


def load_mappings():
    """Load the mappings table."""
    return _load_table(get_resource_file_path('mappings.tsv'))


def load_predictions():
    """Load the predictions table."""
    return _load_table(get_resource_file_path('predictions.tsv'))
