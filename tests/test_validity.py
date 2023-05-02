# -*- coding: utf-8 -*-

"""Validation tests for :mod:`biomappings`."""

import itertools as itt
import unittest
from collections import defaultdict

import bioregistry

from biomappings import (
    load_false_mappings,
    load_mappings,
    load_predictions,
    load_unsure,
)
from biomappings.resources import (
    MappingTuple,
    PredictionTuple,
    load_curators,
    mapping_sort_key,
)
from biomappings.resources.semapv import get_semapv
from biomappings.utils import (
    InvalidIdentifierPattern,
    InvalidNormIdentifier,
    check_valid_prefix_id,
    get_canonical_tuple,
)

mappings = load_mappings()
predictions = load_predictions()
incorrect = load_false_mappings()
unsure = load_unsure()
semapv = get_semapv()


def _iter_groups():
    for group, label in [
        (mappings, "positive"),
        (incorrect, "negative"),
        (predictions, "predictions"),
        (unsure, "unsure"),
    ]:
        for i, mapping in enumerate(group, start=2):
            yield label, i, mapping


class TestIntegrity(unittest.TestCase):
    """Data integrity tests."""

    def test_prediction_types(self):
        """Test that the prediction type is pulled in properly."""
        for line, mapping in enumerate(mappings, start=2):
            pt = mapping.get("prediction_type", "".strip())
            if not pt:
                continue
            self.assertTrue(
                pt.startswith("semapv:"),
                msg=f"Prediction type should be annotated with semapv on line {line}",
            )
            self.assertIn(pt[len("semapv:") :], semapv)
            self.assertNotEqual(
                "semapv:ManualMappingCuration",
                pt,
                msg="Prediction can not be annotated with manual curation",
            )

        for label, line, mapping in _iter_groups():
            tt = mapping["type"]
            self.assertTrue(
                tt.startswith("semapv:"),
                msg=f"[{label}] The 'type' column should be annotated with semapv on line {line}",
            )
            self.assertIn(tt[len("semapv:") :], semapv)

    def test_canonical_prefixes(self):
        """Test that all mappings use canonical bioregistry prefixes."""
        valid_prefixes = set(bioregistry.read_registry())
        for label, line, mapping in _iter_groups():
            source_prefix, target_prefix = mapping["source prefix"], mapping["target prefix"]
            self.assertIn(
                source_prefix,
                valid_prefixes,
                msg=f"Invalid prefix: {source_prefix} on {label}:{line}",
            )
            self.assertIn(
                target_prefix,
                valid_prefixes,
                msg=f"Invalid prefix: {target_prefix} on {label}:{line}",
            )

    def test_normalized_identifiers(self):
        """Test that all identifiers have been normalized (based on bioregistry definition)."""
        for label, line, mapping in _iter_groups():
            self.assert_canonical_identifier(
                mapping["source prefix"], mapping["source identifier"], label, line
            )
            self.assert_canonical_identifier(
                mapping["target prefix"], mapping["target identifier"], label, line
            )

    def assert_canonical_identifier(
        self, prefix: str, identifier: str, label: str, line: int
    ) -> None:
        """Assert a given identifier is canonical.

        :param prefix: The prefix to check
        :param identifier: The identifier in the semantic space for the prefix
        :param label: The label of the mapping file
        :param line: The line number of the mapping
        """
        try:
            check_valid_prefix_id(prefix, identifier)
        except InvalidNormIdentifier as e:
            self.fail(f"[{label}:{line}] {e}")
        except InvalidIdentifierPattern as e:
            self.fail(f"[{label}:{line}] {e}")

    def test_contributors(self):
        """Test all contributors have an entry in the curators.tsv file."""
        contributor_orcids = {row["orcid"] for row in load_curators()}
        for mapping in itt.chain(mappings, incorrect, unsure):
            source = mapping["source"]
            if not source.startswith("orcid:"):
                continue
            self.assertIn(source[len("orcid:") :], contributor_orcids)


def _extract_redundant(counter):
    return [(key, values) for key, values in counter.items() if len(values) > 1]


def test_cross_redundancy():
    """Test the redundancy of manually curated mappings and predicted mappings."""
    counter = defaultdict(lambda: defaultdict(list))
    for label, line, mapping in _iter_groups():
        counter[get_canonical_tuple(mapping)][label].append(line)

    redundant = []
    for mapping, label_to_lines in counter.items():
        if len(label_to_lines) <= 1:
            continue
        redundant.append((mapping, sorted(label_to_lines.items())))

    if redundant:
        msg = "".join(
            f"\n  {mapping}: {_locations_str(locations)}" for mapping, locations in redundant
        )
        raise ValueError(f"{len(redundant)} are redundant: {msg}")


def _locations_str(locations):
    return ", ".join(f"{label}:{line}" for label, line in locations)


def _assert_no_internal_redundancies(m, tuple_cls):
    counter = defaultdict(list)
    for line, mapping in enumerate(m, start=1):
        counter[tuple_cls.from_dict(mapping)].append(line)
    redundant = _extract_redundant(counter)
    if redundant:
        msg = "".join(
            f"\n  {mapping.source_curie}/{mapping.target_curie}: {locations}"
            for mapping, locations in redundant
        )
        raise ValueError(f"{len(redundant)} are redundant: {msg}")


def test_predictions_sorted():
    """Test the predictions are in a canonical order."""
    assert predictions == sorted(  # noqa:S101
        predictions, key=mapping_sort_key
    ), "Predictions are not sorted"
    _assert_no_internal_redundancies(predictions, PredictionTuple)


def test_curations_sorted():
    """Test the true curated mappings are in a canonical order."""
    assert mappings == sorted(  # noqa:S101
        mappings, key=mapping_sort_key
    ), "True curations are not sorted"
    _assert_no_internal_redundancies(mappings, MappingTuple)


def test_false_mappings_sorted():
    """Test the false curated mappings are in a canonical order."""
    assert incorrect == sorted(  # noqa:S101
        incorrect, key=mapping_sort_key
    ), "False curations are not sorted"
    _assert_no_internal_redundancies(incorrect, MappingTuple)


def test_unsure_sorted():
    """Test the unsure mappings are in a canonical order."""
    assert unsure == sorted(  # noqa:S101
        unsure, key=mapping_sort_key
    ), "Unsure curations are not sorted"
    _assert_no_internal_redundancies(unsure, MappingTuple)
