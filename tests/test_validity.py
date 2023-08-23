# -*- coding: utf-8 -*-

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

    def setUp(self) -> None:
        """Set up the test case."""
        self.mappings = load_mappings()
        self.predictions = load_predictions()
        self.incorrect = load_false_mappings()
        self.unsure = load_unsure()
