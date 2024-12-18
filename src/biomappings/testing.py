"""Validation tests for :mod:`biomappings`."""

import unittest
from collections import defaultdict
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, Union

import bioregistry

from biomappings.resources import (
    CURATORS_PATH,
    FALSE_MAPPINGS_PATH,
    TRUE_MAPPINGS_PATH,
    UNSURE_PATH,
    Mappings,
    MappingTuple,
    PredictionTuple,
    load_curators,
    load_mappings,
    load_predictions,
    mapping_sort_key,
)
from biomappings.resources.semapv import get_semapv
from biomappings.utils import (
    InvalidIdentifierPattern,
    InvalidNormIdentifier,
    check_valid_prefix_id,
    get_canonical_tuple,
)

__all__ = [
    "IntegrityTestCase",
    "PathIntegrityTestCase",
]

semapv = get_semapv()


def _extract_redundant(counter):
    return [(key, values) for key, values in counter.items() if len(values) > 1]


def _locations_str(locations):
    return ", ".join(f"{label}:{line}" for label, line in locations)


class IntegrityTestCase(unittest.TestCase):
    """Data integrity tests."""

    mappings: Mappings
    predictions: Mappings
    incorrect: Mappings
    unsure: Mappings

    def _iter_groups(self):
        for group, label in [
            (self.mappings, "positive"),
            (self.incorrect, "negative"),
            (self.predictions, "predictions"),
            (self.unsure, "unsure"),
        ]:
            for i, mapping in enumerate(group, start=2):
                yield label, i, mapping

    def test_prediction_types(self) -> None:
        """Test that the prediction type is pulled in properly."""
        for line, mapping in enumerate(self.mappings, start=2):
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

        for label, line, mapping in self._iter_groups():
            tt = mapping["type"]
            self.assertTrue(
                tt.startswith("semapv:"),
                msg=f"[{label}] The 'type' column should be annotated with semapv on line {line}",
            )
            self.assertIn(tt[len("semapv:") :], semapv)

    def test_relations(self) -> None:
        """Test that the relation is a CURIE."""
        for label, line, mapping in self._iter_groups():
            parts = mapping["relation"].split(":")
            self.assertEqual(2, len(parts))
            prefix, identifier = parts
            self.assertNotEqual("ro", prefix, msg="RO should be capitalized")
            if prefix != "RO":
                self.assert_canonical_identifier(prefix, identifier, label, line)

    def test_canonical_prefixes(self) -> None:
        """Test that all mappings use canonical bioregistry prefixes."""
        valid_prefixes = set(bioregistry.read_registry())
        for label, line, mapping in self._iter_groups():
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

    def test_normalized_identifiers(self) -> None:
        """Test that all identifiers have been normalized (based on bioregistry definition)."""
        for label, line, mapping in self._iter_groups():
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

    def test_contributors(self) -> None:
        """Test all contributors have an entry in the curators.tsv file."""
        user_to_orcid = {row["user"]: row["orcid"] for row in load_curators()}

        # it's possible that the same ORCID appears twice
        contributor_orcids = set(user_to_orcid.values())

        files = [
            (TRUE_MAPPINGS_PATH, self.mappings),
            (FALSE_MAPPINGS_PATH, self.incorrect),
            (UNSURE_PATH, self.unsure),
        ]
        for path, mappings in files:
            for mapping in mappings:
                source = mapping["source"]
                if not source.startswith("orcid:"):
                    self.assertTrue(source.startswith("web-"))
                    user = source[len("web-") :]
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
                            2. Replace all instances of "{source}" in {path}
                               with your ORCID, properly prefixed with `orcid:`
                            """).rstrip()
                        )
                self.assertIn(source[len("orcid:") :], contributor_orcids)

    def test_cross_redundancy(self) -> None:
        """Test the redundancy of manually curated mappings and predicted mappings."""
        counter: defaultdict[tuple[str, str, str, str], defaultdict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for label, line, mapping in self._iter_groups():
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

    def assert_no_internal_redundancies(self, m: Mappings, tuple_cls) -> None:
        """Assert that the list of mappings doesn't have any redundancies."""
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

    predictions_path: ClassVar[Union[str, Path]]
    positives_path: ClassVar[Union[str, Path]]
    negatives_path: ClassVar[Union[str, Path]]
    unsure_path: ClassVar[Union[str, Path]]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        cls.predictions = load_predictions(path=cls.predictions_path)
        cls.mappings = load_mappings(path=cls.positives_path)
        cls.incorrect = load_mappings(path=cls.negatives_path)
        cls.unsure = load_mappings(path=cls.unsure_path)
