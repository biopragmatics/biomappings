import os
import csv

RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_resource_file_path(fname):
    return os.path.join(RESOURCE_PATH, fname)


def _load_table(fname):
    with open(fname, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        header = next(reader)
        return [{h: c for h, c in zip(header, row)} for row in reader]


def load_mappings():
    return _load_table(get_resource_file_path('mappings.tsv'))


def load_predictions():
    return _load_table(get_resource_file_path('predictions.tsv'))
