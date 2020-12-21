# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

import itertools as itt
from typing import Iterable, List, Tuple

import click
import gilda
import gilda.grounder
import pyobo

from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url


@click.command()
@click.option('--prefix', dest='prefixes', multiple=True)
def main(prefixes: List[str]):
    """Append predictions made by Gilda for the given prefix(es)."""
    append_prediction_tuples(itt.chain.from_iterable(
        iter_gilda_prediction_tuples(prefix)
        for prefix in prefixes
    ))


def iter_gilda_prediction_tuples(prefix: str) -> Iterable[Tuple[str, ...]]:
    """Iterate over prediction tuples for a given prefix."""
    provenance = get_script_url(__file__)
    id_name_mapping = pyobo.get_id_name_mapping(prefix)
    for identifier, name in id_name_mapping.items():
        for scored_match in gilda.ground(name):
            yield (
                prefix,
                identifier,
                name,
                'skos:exactMatch',
                scored_match.term.db.lower(),
                scored_match.term.id,
                scored_match.term.entry_name,
                'lexical',
                scored_match.score,
                provenance,
            )


if __name__ == '__main__':
    main()
