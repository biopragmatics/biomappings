# -*- coding: utf-8 -*-

"""Import mappings from ComPath."""

import pandas as pd
from tqdm import tqdm

import pyobo
from biomappings.resources import append_true_mappings

URL = 'https://github.com/ComPath/compath-resources/raw/master/docs/data/compath.tsv'


def main():
    """Import mappings from ComPath."""
    df = pd.read_csv(URL, sep='\t')
    df = df[df['relation'] == 'skos:exactMatch']
    df = df[df['source prefix'] != 'decopath']
    df = df[df['target prefix'] != 'decopath']
    df['type'] = 'manual'
    df['source'] = 'orcid:0000-0002-2046-6145'  # ComPath is courtesy of Uncle Daniel

    # TODO check that species are the same

    # Make sure nomenclature is correct
    df['source name'] = [
        name if prefix == 'kegg.pathway' else pyobo.get_name(prefix, identifier)
        for prefix, identifier, name in tqdm(df[['source prefix', 'source identifier', 'source name']].values)
    ]
    df['target name'] = [
        name if prefix == 'kegg.pathway' else pyobo.get_name(prefix, identifier)
        for prefix, identifier, name in tqdm(df[['target prefix', 'target identifier', 'target name']].values)
    ]
    append_true_mappings(
        row
        for _, row in df.iterrows()
    )


if __name__ == '__main__':
    main()
