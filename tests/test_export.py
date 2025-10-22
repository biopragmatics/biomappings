"""Test exports and outputs."""

import unittest

from biomappings.resources.export_sssom import get_merged_ssom


class TestExport(unittest.TestCase):
    """Test exporting SSSOM."""

    def test_sssom_merge(self) -> None:
        """Test merging SSSOM files."""
        get_merged_ssom(use_tqdm=False)
