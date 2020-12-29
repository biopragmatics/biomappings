# -*- coding: utf-8 -*-

"""Upload the Biomappings to NDEx.

.. seealso:: https://www.ndexbio.org/viewer/networks/402d1fd6-49d6-11eb-9e72-0ac135e8bacf
"""

import click
import pystow
from tqdm import tqdm

from biomappings import load_mappings
from biomappings.utils import MiriamValidator, get_git_hash

BIOMAPPINGS_NDEX_UUID = '402d1fd6-49d6-11eb-9e72-0ac135e8bacf'


@click.command()
@click.option('--username')
@click.option('--password')
def ndex(username, password):
    """Upload to NDEx."""
    try:
        from ndex2 import NiceCXBuilder
    except ImportError:
        click.secho('Need to `pip install ndex2` before uploading to NDEx', fg='red')
        return

    miriam_validator = MiriamValidator()
    positive_mappings = load_mappings()
    cx = NiceCXBuilder()
    cx.set_name('Biomappings')
    cx.add_network_attribute('description', 'Manually curated mappings (skos:exactMatch) between biological entities.')
    cx.add_network_attribute('reference', 'https://github.com/biomappings/biomappings')
    cx.add_network_attribute('rights', 'Waiver-No rights reserved (CC0)')

    context = {'orcid': 'https://identifiers.org/orcid:'}
    for mapping in positive_mappings:
        for prefix in (mapping['source prefix'], mapping['target prefix']):
            if miriam_validator.namespace_embedded(prefix):
                prefix = prefix.upper()
            context[prefix] = f'https://identifiers.org/{prefix}:'
    cx.set_context(context)

    cx.add_network_attribute('version', get_git_hash())
    authors = sorted(set(
        mapping['source']
        for mapping in positive_mappings
        if mapping['source'].startswith('orcid:')
    ))
    cx.add_network_attribute('author', authors, type='list_of_string')

    for mapping in tqdm(positive_mappings, desc='Loading NiceCXBuilder'):
        source = cx.add_node(
            represents=mapping['source name'],
            name=miriam_validator.get_curie(mapping["source prefix"], mapping["source identifier"]),
        )
        target = cx.add_node(
            represents=mapping['target name'],
            name=miriam_validator.get_curie(mapping["target prefix"], mapping["target identifier"]),
        )
        edge = cx.add_edge(
            source=source,
            target=target,
            interaction=mapping['relation'],
        )
        cx.add_edge_attribute(edge, 'type', mapping['type'])
        cx.add_edge_attribute(edge, 'provenance', mapping['source'])

    nice_cx = cx.get_nice_cx()
    nice_cx.update_to(
        uuid=BIOMAPPINGS_NDEX_UUID,
        server=pystow.get_config('ndex', 'server', 'http://public.ndexbio.org'),
        username=pystow.get_config('ndex', 'username', username),
        password=pystow.get_config('ndex', 'password', password),
    )


if __name__ == '__main__':
    ndex()