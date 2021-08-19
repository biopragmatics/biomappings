# -*- coding: utf-8 -*-

"""Validation tests for :mod:`biomappings`."""

import itertools as itt
from collections import Counter

from biomappings import load_false_mappings, load_mappings, load_predictions, load_unsure
from biomappings.resources import mapping_sort_key
from biomappings.utils import MiriamValidator, get_canonical_tuple

mappings = load_mappings()
predictions = load_predictions()
incorrect = load_false_mappings()
unsure = load_unsure()

miriam_validator = MiriamValidator()


def test_valid_mappings():
    """Test the validity of the prefixes and identifiers in the mappings."""
    for mapping in itt.chain(mappings, incorrect, predictions):
        miriam_validator.check_valid_prefix_id(
            mapping["source prefix"],
            mapping["source identifier"],
        )
        miriam_validator.check_valid_prefix_id(
            mapping["target prefix"],
            mapping["target identifier"],
        )


def test_redundancy():
    """Test the redundancy of manually curated mappings and predicted mappings."""
    counter = Counter(get_canonical_tuple(m) for m in itt.chain(mappings, incorrect, predictions))
    redundant = [(k, v) for k, v in counter.items() if v > 1]
    if redundant:
        r = "\n".join(f"  {r}: {count}" for r, count in redundant)
        raise ValueError(f"{len(r)} are redundant: {r}")


def test_predictions_sorted():
    """Test the predictions are in a canonical order."""
    assert predictions == sorted(  # noqa:S101
        predictions, key=mapping_sort_key
    ), "Predictions are not sorted"


def test_curations_sorted():
    """Test the true curated mappings are in a canonical order."""
    assert mappings == sorted(  # noqa:S101
        mappings, key=mapping_sort_key
    ), "True curations are not sorted"


def test_false_mappings_sorted():
    """Test the false curated mappings are in a canonical order."""
    assert incorrect == sorted(  # noqa:S101
        incorrect, key=mapping_sort_key
    ), "False curations are not sorted"


def test_unsure_sorted():
    """Test the unsure mappings are in a canonical order."""
    assert unsure == sorted(  # noqa:S101
        unsure, key=mapping_sort_key
    ), "Unsure curations are not sorted"
