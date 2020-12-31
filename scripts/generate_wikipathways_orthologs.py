# -*- coding: utf-8 -*-

"""Generate orthologous relations between WikiPathways."""

from typing import Iterable

import pyobo
from gilda.process import normalize
from tqdm.contrib.itertools import product

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url


def _lexical_exact_match(name1: str, name2: str) -> bool:
    return normalize(name1) == normalize(name2)


def iterate_orthologous_lexical_matches(prefix: str = 'wikipathways') -> Iterable[PredictionTuple]:
    """Generate orthologous relations between lexical matches from different species."""
    names = pyobo.get_id_name_mapping(prefix)
    species = pyobo.get_id_species_mapping(prefix)
    provenance = get_script_url(__file__)

    count = 0
    for (source_id, source_name), (target_id, target_name) in product(names.items(), names.items(), unit_scale=True):
        if species[source_id] == species[target_id]:
            continue
        if source_id > target_id:  # make canonical order
            continue
        if _lexical_exact_match(source_name, target_name):
            count += 1
            yield PredictionTuple(
                prefix, source_id, source_name,
                'orthologous',
                prefix, target_id, target_name,
                'lexical',
                0.99,
                provenance,
            )
    print(f'Identified {count} orthologs')


if __name__ == '__main__':
    append_prediction_tuples(iterate_orthologous_lexical_matches())
