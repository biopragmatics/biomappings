# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

import itertools as itt
from typing import Iterable

import gilda
import gilda.grounder
import pyobo
from tqdm import tqdm

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url


def iter_gilda_prediction_tuples(prefix: str, relation: str) -> Iterable[PredictionTuple]:
    """Iterate over prediction tuples for a given prefix."""
    provenance = get_script_url(__file__)
    id_name_mapping = pyobo.get_id_name_mapping(prefix)
    for identifier, name in tqdm(id_name_mapping.items(), desc=f'Mapping {prefix}'):
        for scored_match in gilda.ground(name):
            yield PredictionTuple(
                prefix,
                identifier,
                name,
                relation,
                scored_match.term.db.lower(),
                scored_match.term.id,
                scored_match.term.entry_name,
                'lexical',
                scored_match.score,
                provenance,
            )


if __name__ == '__main__':
    append_prediction_tuples(itt.chain.from_iterable(
        sorted(iter_gilda_prediction_tuples(prefix, 'speciesSpecific'), key=lambda t: (t[0], t[2]))
        for prefix in ['reactome', 'wikipathways']
    ))
