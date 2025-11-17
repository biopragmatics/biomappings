# -*- coding: utf-8 -*-

"""Append lexical mappings between MeSH and other gene/protein vocabularies."""

import collections
import re
from typing import Iterable, Mapping, Optional, Tuple

import pandas as pd
import pyobo
import pystow
from indra.databases import mesh_client

from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url

#: This is a dictionary from MeSH suffix to PyOBO prefix
#: Ellipses are left for unhandled organisms
MAP = {
    # 'human': 'hgnc',  # 13168 matches
    'mouse': 'mgi',  # 9822 matches
    'Arabidopsis': ...,  # 5068 matches
    'rat': 'rgd',  # 4681 matches
    'S cerevisiae': 'sgd',  # 3536 matches
    'Drosophila': 'fb',  # 3061 matches
    'C elegans': ...,  # 2040 matches
    'E coli': ...,  # 1984 matches
    'zebrafish': 'zfin',  # 1940 matches
    'Xenopus': ...,  # 1305 matches
    'S pombe': ...,  # 1030 matches
    # 'Bacteria': ...,  # 259 matches
    # 'bacteria': ...,  # 233 matches
    'Bacillus subtilis': ...,  # 226 matches
    'Mycobacterium tuberculosis': ...,  # 199 matches
    'Zea mays': ...,  # 152 matches
    'Pseudomonas aeruginosa': ...,  # 149 matches
    'Staphylococcus aureus': ...,  # 126 matches
    'Plasmodium falciparum': ...,  # 110 matches
    'Salmonella typhimurium': ...,  # 107 matches
    'Nicotiana tabacum': ...,  # 95 matches
    'Candida albicans': ...,  # 91 matches
    'chicken': 'cgnc',  # 91 matches
    'Trypanosoma brucei': ...,  # 90 matches
    'Gallus gallus': 'cgnc',  # 90 matches
    'Bos taurus': ...,  # 82 matches
    'Dictyostelium discoideum': ...,  # 82 matches
    'Oryza sativa': ...,  # 81 matches
}

NEED_PREFIX = {
    'mgi',
}

UNIPROT_NAMES = {
    'mgi': ('database(MGI)', 'Mus musculus (Mouse) [10090]'),
    'rgd': ('database(RGD)', 'Rattus norvegicus (Rat) [10116]'),
    'sgd': ('database(SGD)', "Saccharomyces cerevisiae (strain ATCC 204508 / S288c) (Baker's yeast) [559292]"),
    'fb': ('database(FlyBase)', "Drosophila melanogaster (Fruit fly) [7227]"),
    'zfin': ('database(ZFIN)', "Danio rerio (Zebrafish) (Brachydanio rerio) [7955]"),
    'wb': ('database(WormBase)', "..."),
    # 'cgnc': ('database(CGNC)', "Gallus gallus (Chicken) [9031]"),
}


def get_id_to_uniprot(prefix: str) -> Optional[Mapping[str, str]]:
    """Get identifier to UniProt mapping."""
    if prefix not in UNIPROT_NAMES:
        return

    column, organism = UNIPROT_NAMES[prefix]
    url = 'https://www.uniprot.org/uniprot/'
    params = {
        'format': 'tab',
        'columns': f'{column},id',
        'fil': f'organism:"{organism}"',
    }
    df = pystow.ensure_csv(
        key='biomappings',
        url=url,
        name=f'{prefix}_uniprot.tsv.gz',
        read_csv_kwargs=dict(
            sep='\t',
            compression='gzip',
            dtype=str,
        ),
        download_kwargs=dict(
            backend='requests',
            params=params,
        ),
    )
    return {
        mgi_id.rstrip(';'): uniprot_id
        for mgi_id, uniprot_id in df.values
        if pd.notna(mgi_id) and pd.notna(uniprot_id)
    }


def print_map(minimum: int = 80):
    """Print the map dictionary."""
    names = pyobo.get_name_id_mapping('mesh')
    counter = collections.Counter()
    for name in names:
        if 'protein, ' in name:
            counter[name.split('protein, ')[1]] += 1

    for key, count in counter.most_common():
        if count <= minimum:
            continue
        print(f"'{key}': ...,  # {count} matches")


def get_mappings() -> Iterable[Tuple[str, ...]]:
    """Iterate high-confidence lexical mappings between MeSH and UniProt mouse proteins."""
    url = get_script_url(__file__)
    mapping_type = 'lexical'
    match_type = 'skos:exactMatch'
    confidence = 0.999

    for suffix, key in MAP.items():
        if key is ...:
            continue
        try:
            name_to_id_mapping = pyobo.get_name_id_mapping(key)
        except ValueError:
            print('skipping', key)
            continue

        id_to_uniprot = get_id_to_uniprot(key)
        if id_to_uniprot is None:
            print('no lookup for', key)
            continue

        mesh_protein_re = re.compile(rf'^(.+) protein, {suffix}$')
        for mesh_name, mesh_id in mesh_client.mesh_name_to_id.items():
            match = mesh_protein_re.match(mesh_name)
            if not match:
                continue
            gene_name = match.groups()[0]
            identifier = name_to_id_mapping.get(gene_name)
            if not identifier:
                continue
            uniprot_id = id_to_uniprot.get(identifier)
            if uniprot_id is None:
                continue
            yield (
                'mesh', mesh_id, mesh_name,
                match_type,
                'uniprot', uniprot_id, gene_name,
                mapping_type, confidence, url,
            )


if __name__ == '__main__':
    append_prediction_tuples(get_mappings())
