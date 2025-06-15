"""Test the web app."""

import unittest

from biomappings.wsgi import Controller, State


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
