"""Validation tests for :mod:`biomappings`."""

from __future__ import annotations

import getpass
import unittest
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, TypeVar, cast

import bioregistry
from bioregistry import NormalizedNamableReference
from curies import NamableReference

from biomappings.resources import (
    CURATORS_PATH,
    SemanticMapping,
    _CuratedTuple,
    _PredictedTuple,
    load_mappings,
    load_predictions,
    mapping_sort_key,
)
from biomappings.resources.semapv import get_semapv_id_to_name
from biomappings.utils import (
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
    get_canonical_tuple,
)

__all__ = [
    "IntegrityTestCase",
    "PathIntegrityTestCase",
]


SEMAPV_ID_TO_NAME = get_semapv_id_to_name()

TPL = TypeVar("TPL", _CuratedTuple, _PredictedTuple)
X = TypeVar("X")
Y = TypeVar("Y")


def _extract_redundant(counter: dict[X, list[Y]]) -> list[tuple[X, list[Y]]]:
    return [(key, values) for key, values in counter.items() if len(values) > 1]


def _locations_str(locations) -> str:
    return ", ".join(f"{label}:{line}" for label, line in locations)


class IntegrityTestCase(unittest.TestCase):
    """Data integrity tests."""

    mappings: list[SemanticMapping]
    predictions: list[SemanticMapping]
    incorrect: list[SemanticMapping]
    unsure: list[SemanticMapping]

    def _iter_groups(self) -> Iterable[tuple[str, int, SemanticMapping]]:
        for group, label in [
            (self.mappings, "positive"),
            (self.incorrect, "negative"),
            (self.predictions, "predictions"),
            (self.unsure, "unsure"),
        ]:
            for i, mapping in enumerate(group, start=2):
                yield label, i, mapping

    def test_mapping_justifications(self) -> None:
        """Test that the prediction type is pulled in properly."""
        for label, line, mapping in self._iter_groups():
            self.assertEqual(
                "semapv",
                mapping.mapping_justification.prefix,
                msg=f"[{label}] The 'mapping_justification' column should be annotated with semapv on line {line}",
            )
            self.assertIn(mapping.mapping_justification.identifier, SEMAPV_ID_TO_NAME)

    def test_prediction_not_manual(self) -> None:
        """Test that predicted mappings don't use manual mapping justification."""
        for _line, mapping in enumerate(self.predictions, start=2):
            self.assertNotEqual(
                "ManualMappingCuration",
                mapping.mapping_justification.identifier,
                msg="Prediction can not be annotated with manual curation",
            )

    def test_valid_curies(self) -> None:
        """Test that all mappings use canonical bioregistry prefixes."""
        for label, line, mapping in self._iter_groups():
            self.assert_valid(label, line, mapping.subject)
            self.assert_valid(label, line, mapping.predicate)
            self.assert_valid(label, line, mapping.object)
            self.assert_valid(label, line, mapping.mapping_justification)
            if mapping.author is not None:
                self.assert_valid(label, line, mapping.author)

    def assert_valid(self, label: str, line: int, reference: NamableReference) -> None:
        """Assert a reference is valid and normalized to the Bioregistry."""
        norm_prefix = bioregistry.normalize_prefix(reference.prefix)
        self.assertIsNotNone(
            norm_prefix, msg=f"Unknown prefix: {reference.prefix} on {label}:{line}"
        )
        self.assertEqual(
            norm_prefix,
            reference.prefix,
            msg=f"Non-normalized prefix: {reference.prefix} on {label}:{line}",
        )
        self.assertEqual(
            bioregistry.standardize_identifier(reference.prefix, reference.identifier),
            reference.identifier,
            msg=f"Invalid identifier: {reference.curie} on {label}:{line}",
        )

    def test_contributors(self) -> None:
        """Test all contributors have an entry in the curators.tsv file."""
        files = [
            (POSITIVES_SSSOM_PATH, self.mappings),
            (NEGATIVES_SSSOM_PATH, self.incorrect),
            (UNSURE_SSSOM_PATH, self.unsure),
        ]
        for path, mappings in files:
            for mapping in mappings:
                self.assertIsNotNone(mapping.author)
                author = cast(NormalizedNamableReference, mapping.author)
                self.assertEqual(
                    "orcid",
                    author.prefix,
                    msg=dedent(f"""
                    There are some curations that don't have the right metadata.
                    This probably happened because you are curating locally and
                    haven't added the right metadata to the curators.tsv file at
                    {CURATORS_PATH}.

                    You can fix this with the following steps:

                    1. Add a row to the curators.tsv file with your local machine's
                       username "{getpass.getuser()}" in the first column, your ORCID in
                       the second column, and your full name in the third column
                    2. Replace all instances of "{author.curie}" in {path}
                       with your ORCID, properly prefixed with `orcid:`
                    """).rstrip(),
                )

    def test_cross_redundancy(self) -> None:
        """Test the redundancy of manually curated mappings and predicted mappings."""
        counter: defaultdict[tuple[str, str, str, str], defaultdict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for label, line, mapping in self._iter_groups():
            counter[get_canonical_tuple(mapping)][label].append(line)

        redundant = []
        for mapping_key, label_to_lines in counter.items():
            if len(label_to_lines) <= 1:
                continue
            redundant.append((mapping_key, sorted(label_to_lines.items())))

        if redundant:
            msg = "".join(
                f"\n  {mapping}: {_locations_str(locations)}" for mapping, locations in redundant
            )
            raise ValueError(f"{len(redundant)} are redundant: {msg}")

    def assert_no_internal_redundancies(self, mappings: list[SemanticMapping]) -> None:
        """Assert that the list of mappings doesn't have any redundancies."""
        counter: defaultdict[tuple[NamableReference, NamableReference], list[int]] = defaultdict(
            list
        )
        for line_number, mapping in enumerate(mappings, start=1):
            counter[mapping.subject, mapping.object].append(line_number)
        redundant = _extract_redundant(counter)
        if redundant:
            msg = "".join(
                f"\n  {subject.curie}/{obj.curie}: {locations}"
                for (subject, obj), locations in redundant
            )
            raise ValueError(f"{len(redundant)} are redundant: {msg}")

    def test_predictions_sorted(self) -> None:
        """Test the predictions are in a canonical order."""
        self.assertEqual(
            self.predictions,
            sorted(self.predictions, key=mapping_sort_key),
            msg="Predictions are not sorted",
        )
        self.assert_no_internal_redundancies(self.predictions)

    def test_curations_sorted(self) -> None:
        """Test the true curated mappings are in a canonical order."""
        self.assertEqual(
            self.mappings,
            sorted(self.mappings, key=mapping_sort_key),
            msg="True curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.mappings)

    def test_false_mappings_sorted(self) -> None:
        """Test the false curated mappings are in a canonical order."""
        self.assertEqual(
            self.incorrect,
            sorted(self.incorrect, key=mapping_sort_key),
            msg="False curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.incorrect)

    def test_unsure_sorted(self) -> None:
        """Test the unsure mappings are in a canonical order."""
        self.assertEqual(
            self.unsure,
            sorted(self.unsure, key=mapping_sort_key),
            msg="Unsure curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.unsure)


class PathIntegrityTestCase(IntegrityTestCase):
    """A test case that can be configured with paths.

    For example, in this might be used in a custom instance of Biomappings
    like in the following:

    .. code-block:: python

        from biomappings.testing import PathIntegrityTestCase

        HERE = Path(__file__).parent.resolve()


        class TestCustom(PathIntegrityTestCase):
            predictions_path = HERE.joinpath("predictions.tsv")
            positives_path = HERE.joinpath("positive.tsv")
            negatives_path = HERE.joinpath("negative.tsv")
            unsure_path = HERE.joinpath("unsure.tsv")
    """

    predictions_path: ClassVar[str | Path]
    positives_path: ClassVar[str | Path]
    negatives_path: ClassVar[str | Path]
    unsure_path: ClassVar[str | Path]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        cls.predictions = load_predictions(path=cls.predictions_path)
        cls.mappings = load_mappings(path=cls.positives_path)
        cls.incorrect = load_mappings(path=cls.negatives_path)
        cls.unsure = load_mappings(path=cls.unsure_path)
