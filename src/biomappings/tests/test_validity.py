"""Validation tests for :mod:`biomappings`."""

import itertools as itt
from collections import Counter

from biomappings import load_false_mappings, load_mappings, load_predictions
from biomappings.utils import MiriamValidator, get_canonical_tuple

mappings = load_mappings()
predictions = load_predictions()
incorrect = load_false_mappings()


miriam_validator = MiriamValidator()


def test_valid_mappings():
    """Test the validity of the prefixes and identifiers in the mappings."""
    for mapping in itt.chain(mappings, incorrect, predictions):
        miriam_validator.check_valid_prefix_id(
            mapping['source prefix'],
            mapping['source identifier'],
        )
        miriam_validator.check_valid_prefix_id(
            mapping['target prefix'],
            mapping['target identifier'],
        )


def test_redundancy():
    """Test the redundancy of manually curated mappings and predicted mappings."""
    counter = Counter(
        get_canonical_tuple(m)
        for m in itt.chain(mappings, incorrect, predictions)
    )
    redundant = [(k, v) for k, v in counter.items() if v > 1]
    if redundant:
        r = '\n'.join(f'  {r}: {count}' for r, count in redundant)
        raise ValueError(f'Redundant: {r}')
