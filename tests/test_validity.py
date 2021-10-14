# -*- coding: utf-8 -*-

"""Validation tests for :mod:`biomappings`."""

import itertools as itt
import unittest
from collections import Counter

import bioregistry

from biomappings import load_false_mappings, load_mappings, load_predictions, load_unsure
from biomappings.resources import load_curators, mapping_sort_key
from biomappings.utils import check_valid_prefix_id, get_canonical_tuple

mappings = load_mappings()
predictions = load_predictions()
incorrect = load_false_mappings()
unsure = load_unsure()


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

        .. warning::

            NCIT is skipped for now, since it has an OBO Foundry definition but explicitly
            does not have namespace embedded in LUI. See also:
            https://github.com/biopragmatics/bioregistry/issues/208
        """
        if prefix in {"ncit"}:
            return
        resource = bioregistry.get_resource(prefix)
        self.assertIsNotNone(resource)
        norm_id = resource.normalize_identifier(identifier)
        self.assertIsNotNone(norm_id)
        self.assertEqual(
            identifier,
            norm_id,
            msg=f"Normalization of {prefix}:{identifier} failed on {label}:{line}",
        )

    def test_contributors(self):
        """Test all contributors have an entry in the curators.tsv file."""
        contributor_orcids = {row["orcid"] for row in load_curators()}
        for mapping in itt.chain(mappings, incorrect, unsure):
            source = mapping["source"]
            if not source.startswith("orcid:"):
                continue
            self.assertIn(source[len("orcid:") :], contributor_orcids)


def test_valid_mappings():
    """Test the validity of the prefixes and identifiers in the mappings."""
    for mapping in itt.chain(mappings, incorrect, predictions):
        check_valid_prefix_id(
            mapping["source prefix"],
            mapping["source identifier"],
        )
        check_valid_prefix_id(
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
