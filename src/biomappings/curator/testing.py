"""Validation tests for :mod:`biomappings`."""

from __future__ import annotations

import unittest
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, TypeVar, cast

if TYPE_CHECKING:
    from curies import Reference
    from sssom_pydantic import SemanticMapping

__all__ = [
    "GetterIntegrityTestCase",
    "IntegrityTestCase",
    "MappingGetter",
    "PathIntegrityTestCase",
]

X = TypeVar("X")
Y = TypeVar("Y")


def _extract_redundant(counter: dict[X, list[Y]]) -> list[tuple[X, list[Y]]]:
    return [(key, values) for key, values in counter.items() if len(values) > 1]


def _locations_str(locations: Iterable[tuple[Any, Any]]) -> str:
    return ", ".join(f"{label}:{line}" for label, line in locations)


#: A function that gets mappings
MappingGetter: TypeAlias = Callable[[], list["SemanticMapping"]]


class IntegrityTestCase(unittest.TestCase):
    """Data integrity tests."""

    mappings: ClassVar[list[SemanticMapping]]
    predictions: ClassVar[list[SemanticMapping]]
    incorrect: ClassVar[list[SemanticMapping]]
    unsure: ClassVar[list[SemanticMapping]]

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
        from curies.vocabulary import matching_processes

        for label, line, mapping in self._iter_groups():
            self.assertEqual(
                "semapv",
                mapping.justification.prefix,
                msg=f"[{label}] The 'mapping_justification' column should be annotated with semapv on line {line}",
            )
            self.assertIn(mapping.justification, matching_processes)

    def test_prediction_not_manual(self) -> None:
        """Test that predicted mappings don't use manual mapping justification."""
        for _line, mapping in enumerate(self.predictions, start=2):
            self.assertNotEqual(
                "ManualMappingCuration",
                mapping.justification.identifier,
                msg="Prediction can not be annotated with manual curation",
            )

    def test_valid_curies(self) -> None:
        """Test that all mappings use canonical bioregistry prefixes."""
        for label, line, mapping in self._iter_groups():
            self.assert_valid(label, line, mapping.subject)
            self.assert_valid(label, line, mapping.predicate)
            self.assert_valid(label, line, mapping.object)
            self.assert_valid(label, line, mapping.justification)
            if mapping.author is not None:
                self.assert_valid(label, line, mapping.author)

    def assert_valid(self, label: str, line: int, reference: Reference) -> None:
        """Assert a reference is valid and normalized to the Bioregistry."""
        import bioregistry

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
        from bioregistry import NormalizedNamableReference

        files = [
            ("positive", self.mappings),
            ("negative", self.incorrect),
            ("unsure", self.unsure),
        ]
        for label, mappings in files:
            for mapping in mappings:
                self.assertIsNotNone(mapping.author)
                author = cast(NormalizedNamableReference, mapping.author)
                self.assertEqual(
                    "orcid",
                    author.prefix,
                    msg=f"ORCID prefixes are required for authors in the {label} group",
                )

    def test_cross_redundancy(self) -> None:
        """Test the redundancy of manually curated mappings and predicted mappings."""
        from sssom_pydantic.process import CanonicalMappingTuple, get_canonical_tuple

        counter: defaultdict[CanonicalMappingTuple, defaultdict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for label, line, mapping in self._iter_groups():
            counter[get_canonical_tuple(mapping)][label].append(line)

        redundant: list[tuple[CanonicalMappingTuple, list[tuple[str, list[int]]]]] = []
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
        counter: defaultdict[tuple[Reference, Reference], list[int]] = defaultdict(list)
        for line_number, mapping in enumerate(mappings, start=1):
            counter[mapping.subject, mapping.object].append(line_number)
        redundant = _extract_redundant(counter)
        if redundant:
            msg = "".join(
                f"\n  {subject.curie}/{obj.curie}: {locations}"
                for (subject, obj), locations in redundant
            )
            self.fail(f"{len(redundant)} are redundant: {msg}")

    def test_predictions_sorted(self) -> None:
        """Test the predictions are in a canonical order."""
        self.assertEqual(
            self.predictions,
            sorted(self.predictions),
            msg="Predictions are not sorted",
        )
        self.assert_no_internal_redundancies(self.predictions)

    def test_curations_sorted(self) -> None:
        """Test the true curated mappings are in a canonical order."""
        self.assertEqual(
            self.mappings,
            sorted(self.mappings),
            msg="True curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.mappings)

    def test_false_mappings_sorted(self) -> None:
        """Test the false curated mappings are in a canonical order."""
        self.assertEqual(
            self.incorrect,
            sorted(self.incorrect),
            msg="False curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.incorrect)

    def test_unsure_sorted(self) -> None:
        """Test the unsure mappings are in a canonical order."""
        self.assertEqual(
            self.unsure,
            sorted(self.unsure),
            msg="Unsure curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.unsure)


class GetterIntegrityTestCase(IntegrityTestCase):
    """Data integrity tests."""

    positive_mappings_getter: ClassVar[MappingGetter]
    predictions_getter: ClassVar[MappingGetter]
    negative_mappings_getter: ClassVar[MappingGetter]
    unsure_mappings_getter: ClassVar[MappingGetter]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        cls.mappings = cls.positive_mappings_getter()
        cls.predictions = cls.predictions_getter()
        cls.incorrect = cls.negative_mappings_getter()
        cls.unsure = cls.unsure_mappings_getter()


class PathIntegrityTestCase(IntegrityTestCase):
    """A test case that can be configured with paths.

    For example, in this might be used in a custom instance of Biomappings like in the
    following:

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
        import sssom_pydantic

        cls.predictions = sssom_pydantic.read(cls.predictions_path)[0]
        cls.mappings = sssom_pydantic.read(cls.positives_path)[0]
        cls.incorrect = sssom_pydantic.read(cls.negatives_path)[0]
        cls.unsure = sssom_pydantic.read(cls.unsure_path)[0]
