# -*- coding: utf-8 -*-

"""Import mappings from ComPath."""

from tqdm import tqdm

import pyobo
from biomappings.resources import append_true_mappings
from compath_resources import get_df


def main():
    """Import mappings from ComPath."""
    df = get_df()

    # Remove partOf relations
    df = df[df['Mapping Type'] == 'equivalentTo']
    del df['Mapping Type']

    # Fix column names
    df.rename(
        columns={
            'Source Resource': 'source prefix',
            'Source ID': 'source identifier',
            'Source Name': 'source name',
            'Target Resource': 'target prefix',
            'Target ID': 'target identifier',
            'Target Name': 'target name',
        },
        inplace=True,
    )

    # Add metadata
    df['relation'] = 'skos:exactMatch'
    df['type'] = 'manual'
    df['source'] = 'orcid:0000-0002-2046-6145' # ComPath is courtesy of Uncle Daniel

    # Fix incorrect prefix for KEGG Pathways
    for key in ('source prefix', 'target prefix'):
        df[key] = df[key].map(lambda x: 'kegg.pathway' if x == 'kegg' else x)

    # Remove prefix from KEGG Pathway identifiers
    df['source identifier'] = [
        identifier if prefix != 'kegg.pathway' else identifier.removeprefix('path:')
        for prefix, identifier in tqdm(df[['source prefix', 'source identifier']].values)
    ]
    df['target identifier'] = [
        identifier if prefix != 'kegg.pathway' else identifier.removeprefix('path:')
        for prefix, identifier in tqdm(df[['target prefix', 'target identifier']].values)
    ]

    # TODO check that species are the same

    # Make sure nomenclature is correct
    df['source name'] = [
        pyobo.get_name(prefix, identifier)
        for prefix, identifier in tqdm(df[['source prefix', 'source identifier']].values)
    ]
    df['target name'] = [
        pyobo.get_name(prefix, identifier)
        for prefix, identifier in tqdm(df[['target prefix', 'target identifier']].values)
    ]
    append_true_mappings(
        row
        for _, row in df.iterrows()
    )


if __name__ == '__main__':
    main()
