# -*- coding: utf-8 -*-

"""Utilities for generating ortholog predictions."""

import itertools as itt
import logging
from typing import Callable, Iterable, List, Mapping

import pyobo
from tqdm import tqdm

from .resources import MappingTuple
from .utils import get_script_url

__all__ = [
    "iterate_orthologs",
]

logger = logging.getLogger(__name__)


def iterate_orthologs(
    prefix: str,
    f: Callable[[Mapping[str, str]], Mapping[str, List[str]]],
) -> Iterable[MappingTuple]:
    """Iterate over orthologs based on identifier matching."""
    provenance = get_script_url(__file__)
    names = pyobo.get_id_name_mapping(prefix)
    parent_identifier_to_species_identifier = f(names)
    count = 0
    for identifiers in tqdm(parent_identifier_to_species_identifier.values()):
        for source_id, target_id in itt.product(identifiers, repeat=2):
            if source_id >= target_id:
                continue
            count += 1
            yield MappingTuple(
                prefix,
                source_id,
                names[source_id],
                "RO:HOM0000017",
                prefix,
                target_id,
                names[target_id],
                "calculated",
                provenance,
            )
    logger.info(f"[{prefix}] Identified {count} orthologs")
