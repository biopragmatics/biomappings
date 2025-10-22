"""Test exports and outputs."""

import unittest

from biomappings.curator.merge import get_merged_sssom
from biomappings.utils import DEFAULT_REPO


class TestExport(unittest.TestCase):
    """Test exporting SSSOM."""

    def test_sssom_merge(self) -> None:
        """Test merging SSSOM files."""
        get_merged_sssom(DEFAULT_REPO, use_tqdm=False)
