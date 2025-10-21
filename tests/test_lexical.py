"""Test lexical mapping."""

import unittest

import pandas as pd

from biomappings.curator.lexical_core import _calculate_similarities


class TestEmbeddingSimilarity(unittest.TestCase):
    """Test embedding similarity."""

    def test_calculate_similarities(self) -> None:
        """Test calculating similarities in batch."""
        left_df = pd.DataFrame(
            [
                (0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0),
                (1.0, 0.0, 0.0),
            ],
            index=["49E2512", "48C3522 ", "49G621"],
        )
        # iconclass:49E2512 	microscope 	chmo:0000102
        right_df = pd.DataFrame(
            [
                (0.0, 1.0, 1.0),
                (1.0, 1.0, 0.0),
                (1.0, 0.0, 1.0),
                (1.0, 1.0, 1.0),
            ],
            index=["0000005", "0000102", "0000953", "0001088"],
        )

        for batch_size, cutoff in [
            (2, -1),
            (10, -1),
            (2, 0),
            (10, 0),
        ]:
            unbatched = _calculate_similarities(
                left_df, right_df, batch_size=None, cutoff=cutoff, progress=False
            )
            batched_2 = _calculate_similarities(
                left_df, right_df, batch_size=batch_size, cutoff=cutoff, progress=False
            )
            self.assertEqual(
                sorted(unbatched),
                sorted(batched_2),
            )
