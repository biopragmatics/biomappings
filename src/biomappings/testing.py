"""Validation tests for :mod:`biomappings`."""

from __future__ import annotations

import unittest
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, TypeVar

import bioregistry
from bioregistry import NormalizedReference

from biomappings.resources import (
    CURATORS_PATH,
    MappingTuple,
    PredictionTuple,
    SemanticMappings,
    load_curators,
    load_mappings,
    load_predictions,
    mapping_sort_key,
)
from biomappings.resources.semapv import get_semapv
from biomappings.utils import (
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
    get_canonical_tuple,
    get_prefix,
)

__all__ = [
    "IntegrityTestCase",
    "PathIntegrityTestCase",
]

semapv = get_semapv()

TPL = TypeVar("TPL", MappingTuple, PredictionTuple)
X = TypeVar("X")
Y = TypeVar("Y")


def _extract_redundant(counter: dict[X, list[Y]]) -> list[tuple[X, list[Y]]]:
    return [(key, values) for key, values in counter.items() if len(values) > 1]


def _locations_str(locations) -> str:
    return ", ".join(f"{label}:{line}" for label, line in locations)


class IntegrityTestCase(unittest.TestCase):
    """Data integrity tests."""

    mappings: SemanticMappings
    predictions: SemanticMappings
    incorrect: SemanticMappings
    unsure: SemanticMappings

    def _iter_groups(self) -> Iterable[tuple[str, int, MappingTuple]]:
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
            mapping_justification = mapping["mapping_justification"]
            self.assertTrue(
                mapping_justification.startswith("semapv:"),
                msg=f"[{label}] The 'mapping_justification' column should be annotated with semapv on line {line}",
            )
            self.assertIn(mapping_justification[len("semapv:") :], semapv)

    def test_prediction_not_manual(self) -> None:
        """Test that predicted mappings don't use manual mapping justification."""
        for _line, mapping in enumerate(self.predictions, start=2):
            self.assertNotEqual(
                "semapv:ManualMappingCuration",
                mapping["mapping_justification"],
                msg="Prediction can not be annotated with manual curation",
            )

    def test_relations(self) -> None:
        """Test that the relation is a CURIE."""
        for label, line, mapping in self._iter_groups():
            parts = mapping["predicate_id"].split(":")
            self.assertEqual(2, len(parts))
            prefix, identifier = parts
            if prefix != "RO":
                self.assert_canonical_identifier(mapping["predicate_id"], label, line)

    def test_canonical_prefixes(self) -> None:
        """Test that all mappings use canonical bioregistry prefixes."""
        valid_prefixes = set(bioregistry.read_registry())
        for label, line, mapping in self._iter_groups():
            source_prefix, target_prefix = (
                get_prefix(mapping["subject_id"]),
                get_prefix(mapping["object_id"]),
            )
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

    def test_normalized_identifiers(self) -> None:
        """Test that all identifiers have been normalized (based on bioregistry definition)."""
        for label, line, mapping in self._iter_groups():
            self.assert_canonical_identifier(mapping["subject_id"], label, line)
            self.assert_canonical_identifier(mapping["object_id"], label, line)

    def assert_canonical_identifier(self, curie: str, label: str, line: int) -> None:
        """Assert a given identifier is canonical.

        :param curie: The CURIE to check
        :param label: The label of the mapping file
        :param line: The line number of the mapping
        """
        try:
            NormalizedReference.from_curie(curie)
        except Exception as e:
            self.fail(f"[{label}:{line}] {e}")

    def test_contributors(self) -> None:
        """Test all contributors have an entry in the curators.tsv file."""
        user_to_orcid = {row["user"]: row["orcid"] for row in load_curators()}

        # it's possible that the same ORCID appears twice
        contributor_orcids = set(user_to_orcid.values())

        files = [
            (POSITIVES_SSSOM_PATH, self.mappings),
            (NEGATIVES_SSSOM_PATH, self.incorrect),
            (UNSURE_SSSOM_PATH, self.unsure),
        ]
        for path, mappings in files:
            for mapping in mappings:
                author_curie = mapping["author_id"]
                if not author_curie.startswith("orcid:"):
                    self.assertTrue(author_curie.startswith("web-"))
                    user = author_curie[len("web-") :]
                    orcid = user_to_orcid.get(user)
                    if orcid:
                        self.fail(
                            msg=dedent(f"""

                            There are some curations that don't have the right metadata
                            in {path}.

                            You can fix this by running `biomappings lint` from the console
                            """).rstrip()
                        )
                    else:
                        self.fail(
                            msg=dedent(f"""

                            There are some curations that don't have the right metadata.
                            This probably happened because you are curating locally and
                            haven't added the right metadata to the curators.tsv file at
                            {CURATORS_PATH}.

                            You can fix this with the following steps:

                            1. Add a row to the curators.tsv file with your local machine's
                               username "{user}" in the first column, your ORCID in
                               the second column, and your full name in the third column
                            2. Replace all instances of "{author_curie}" in {path}
                               with your ORCID, properly prefixed with `orcid:`
                            """).rstrip()
                        )
                self.assertIn(author_curie[len("orcid:") :], contributor_orcids)

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

    def assert_no_internal_redundancies(
        self, mappings: SemanticMappings, tuple_cls: type[TPL]
    ) -> None:
        """Assert that the list of mappings doesn't have any redundancies."""
        counter: defaultdict[TPL, list[int]] = defaultdict(list)
        for line_number, mapping in enumerate(mappings, start=1):
            counter[tuple_cls.model_validate(mapping)].append(line_number)
        redundant = _extract_redundant(counter)
        if redundant:
            msg = "".join(
                f"\n  {mapping.subject_id}/{mapping.object_id}: {locations}"
                for mapping, locations in redundant
            )
            raise ValueError(f"{len(redundant)} are redundant: {msg}")

    def test_predictions_sorted(self) -> None:
        """Test the predictions are in a canonical order."""
        self.assertEqual(
            self.predictions,
            sorted(self.predictions, key=mapping_sort_key),
            msg="Predictions are not sorted",
        )
        self.assert_no_internal_redundancies(self.predictions, PredictionTuple)

    def test_curations_sorted(self) -> None:
        """Test the true curated mappings are in a canonical order."""
        self.assertEqual(
            self.mappings,
            sorted(self.mappings, key=mapping_sort_key),
            msg="True curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.mappings, MappingTuple)

    def test_false_mappings_sorted(self) -> None:
        """Test the false curated mappings are in a canonical order."""
        self.assertEqual(
            self.incorrect,
            sorted(self.incorrect, key=mapping_sort_key),
            msg="False curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.incorrect, MappingTuple)

    def test_unsure_sorted(self) -> None:
        """Test the unsure mappings are in a canonical order."""
        self.assertEqual(
            self.unsure,
            sorted(self.unsure, key=mapping_sort_key),
            msg="Unsure curations are not sorted",
        )
        self.assert_no_internal_redundancies(self.unsure, MappingTuple)


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
