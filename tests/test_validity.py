"""Validation tests for :mod:`biomappings`."""

from biomappings import (
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
    testing,
)


class TestIntegrity(testing.IntegrityTestCase):
    """Data integrity tests."""

    mappings = load_mappings()
    predictions = load_predictions()
    incorrect = load_false_mappings()
    unsure = load_unsure()
