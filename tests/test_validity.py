"""Validation tests for :mod:`biomappings`."""

from typing import ClassVar

from biomappings import (
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
    testing,
)


class TestIntegrity(testing.GetterIntegrityTestCase):
    """Data integrity tests."""

    positive_mappings_getter: ClassVar[testing.MappingGetter] = load_mappings
    predictions_getter: ClassVar[testing.MappingGetter] = load_predictions
    negative_mappings_getter: ClassVar[testing.MappingGetter] = load_false_mappings
    unsure_mappings_getter: ClassVar[testing.MappingGetter] = load_unsure
