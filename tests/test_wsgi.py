"""Test the web app."""

import tempfile
import unittest
from pathlib import Path

from bioregistry import NormalizedNamableReference as Reference
from sssom_pydantic import MappingTool

from biomappings import SemanticMapping
from biomappings.resources import COLUMNS, write_predictions
from biomappings.wsgi import Controller, State, get_app

TEST_USER = Reference(prefix="orcid", identifier="0000-0000-0000-0000", name="Max Mustermann")


class TestWeb(unittest.TestCase):
    """Test the web app."""

    def setUp(self) -> None:
        """Set up the test case with a controller."""
        self.controller = Controller(user=TEST_USER)

    def test_query(self) -> None:
        """Test making a query."""
        self.controller.count_predictions_from_state(State(query="chebi"))
        self.controller.count_predictions_from_state(State(prefix="chebi"))
        self.controller.count_predictions_from_state(State(source_prefix="chebi"))
        self.controller.count_predictions_from_state(State(source_query="chebi"))
        self.controller.count_predictions_from_state(State(target_prefix="chebi"))
        self.controller.count_predictions_from_state(State(target_query="chebi"))
        self.controller.count_predictions_from_state(State(provenance="orcid"))
        self.controller.count_predictions_from_state(State(provenance="mira"))
        self.controller.count_predictions_from_state(State(sort="desc"))
        self.controller.count_predictions_from_state(State(sort="asc"))
        self.controller.count_predictions_from_state(State(sort="object"))
        self.controller.count_predictions_from_state(State(same_text=True))
        self.controller.count_predictions_from_state(State(same_text=False))
        self.controller.count_predictions_from_state(State(show_relations=True))
        self.controller.count_predictions_from_state(State(show_relations=False))
        self.controller.count_predictions_from_state(State(show_lines=True))
        self.controller.count_predictions_from_state(State(show_lines=False))
        self.controller.count_predictions_from_state(State(limit=5))
        self.controller.count_predictions_from_state(State(limit=5_000_000))
        self.controller.count_predictions_from_state(State(offset=0))
        self.controller.count_predictions_from_state(State(offset=5_000_000))


class TestFull(unittest.TestCase):
    """Test a curation app."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.temporary_directory = tempfile.TemporaryDirectory()

        predictions = [
            SemanticMapping(
                subject=Reference.from_curie("chebi:131408", name="glyoxime"),
                predicate="skos:exactMatch",
                object=Reference.from_curie("mesh:C018305", name="glyoxal dioxime"),
                justification="semapv:ManualMappingCuration",
                confidence=0.95,
                mapping_tool=MappingTool(name="test"),
            )
        ]
        directory = Path(self.temporary_directory.name)
        predictions_path = directory.joinpath("predictions.tsv")
        positives_path = directory.joinpath("positives.tsv")
        negatives_path = directory.joinpath("negatives.tsv")
        unsure_path = directory.joinpath("unsure.tsv")

        write_predictions(predictions, path=predictions_path)
        for path in [positives_path, negatives_path, unsure_path]:
            with path.open("w") as file:
                print("#curie_map:", file=file)
                print("#  chebi: http://purl.obolibrary.org/obo/CHEBI_", file=file)
                print("#  mesh:  http://id.nlm.nih.gov/mesh/", file=file)
                print(*COLUMNS, sep="\t", file=file)

        self.controller = Controller(
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
            user=TEST_USER,
        )
        self.app = get_app(controller=self.controller)
        self.app.testing = True

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.temporary_directory.cleanup()

    def test_mark_out_of_bounds(self) -> None:
        """Test trying to mark a number that's too big."""
        self.assertEqual(1, len(self.controller._predictions))
        self.assertEqual(0, len(self.controller._marked))

        # can't pop a number too big!
        with self.app.test_client() as client, self.assertRaises(IndexError):
            client.get("/mark/10000/yup")

        self.assertEqual(1, len(self.controller._predictions))
        self.assertEqual(0, len(self.controller._marked))

    def test_mark_correct(self) -> None:
        """A self-contained scenario for marking an entry correct."""
        self.assertEqual(1, len(self.controller._predictions))
        self.assertEqual(0, len(self.controller._marked))

        with self.app.test_client() as client:
            res = client.get("/mark/0/yup", follow_redirects=True)
            self.assertEqual(200, res.status_code, msg=res.text)

        # now, we have one less than before~
        self.assertEqual(0, len(self.controller._predictions))
