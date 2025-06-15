"""Test exports and outputs."""

import unittest

from biomappings.resources.export_sssom import get_sssom_df


class TestExport(unittest.TestCase):
    """Test exporting SSSOM."""

    def test_sssom_merge(self) -> None:
        """Test merging SSSOM files."""
        get_sssom_df(use_tqdm=False)
