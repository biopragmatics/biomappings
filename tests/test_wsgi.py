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
        state = State(query="chebi")
        self.controller.count_predictions_from_state(state)
