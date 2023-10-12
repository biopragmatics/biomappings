# -*- coding: utf-8 -*-

"""Validation tests for :mod:`biomappings`."""

from biomappings import (
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
    testing,
)
from biomappings.resources import load_curators


class TestIntegrity(testing.IntegrityTestCase):
    """Data integrity tests."""

    mappings = load_mappings()
    predictions = load_predictions()
    incorrect = load_false_mappings()
    unsure = load_unsure()
    contributor_orcids = {row["orcid"] for row in load_curators()}
