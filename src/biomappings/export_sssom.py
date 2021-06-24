# -*- coding: utf-8 -*-

"""Export Biomappings as SSSOM."""

import os

import click
import pandas as pd

from biomappings import load_mappings
from biomappings.utils import DATA

PATH = os.path.join(DATA, 'biomappings.sssom.tsv')


def get_sssom_df() -> pd.DataFrame:
    """Get an SSSOM dataframe."""
    rows = []
    columns = [
        'subject_id', 'predicate_id', 'object_id', 'subject_label', 'object_label', 'creator_id', 'license'
    ]
    for mapping in load_mappings():
        rows.append((
            f'{mapping["source prefix"]}:{mapping["source identifier"]}',
            f'{mapping["relation"]}',
            f'{mapping["target prefix"]}:{mapping["target identifier"]}',
            mapping["source name"],
            mapping["target name"],
            mapping["source"],
            'CC0',  # TODO fix this with URL?
        ))
    return pd.DataFrame(rows, columns=columns)


@click.command()
@click.option('--path', default=PATH)
def main(path):
    """Export SSSOM."""
    df = get_sssom_df()
    df.to_csv(path, sep='\t', index=False)


if __name__ == '__main__':
    main()
