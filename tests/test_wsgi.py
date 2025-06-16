"""Test the web app."""

import tempfile
import unittest
from pathlib import Path

from biomappings import PredictionTuple
from biomappings.resources import _write_curated, write_predictions
from biomappings.wsgi import Controller, State, get_app


class TestWeb(unittest.TestCase):
    """Test the web app."""

    def setUp(self) -> None:
        """Set up the test case with a controller."""
        self.controller = Controller()

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
            PredictionTuple(
                subject_id="chebi:131408",
                subject_label="glyoxime",
                predicate_id="skos:exactMatch",
                object_id="mesh:C018305",
                object_label="glyoxal dioxime",
                mapping_justification="semapv:ManualMappingCuration",
                confidence=0.95,
                mapping_tool="test",
            )
        ]
        directory = Path(self.temporary_directory.name)
        predictions_path = directory.joinpath("predictions.tsv")
        positives_path = directory.joinpath("positives.tsv")
        negatives_path = directory.joinpath("negatives.tsv")
        unsure_path = directory.joinpath("unsure.tsv")

        write_predictions(predictions, path=predictions_path)
        _write_curated([], path=positives_path, mode="w")
        _write_curated([], path=negatives_path, mode="w")
        _write_curated([], path=unsure_path, mode="w")

        self.controller = Controller(
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
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
