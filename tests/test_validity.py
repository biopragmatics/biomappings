"""Validation tests for :mod:`biomappings`."""

from pathlib import Path
from typing import ClassVar

from sssom_curator import testing

from biomappings.utils import DEFAULT_REPO


class TestIntegrity(testing.PathIntegrityTestCase):
    """Data integrity tests."""

    predictions_path: ClassVar[Path] = DEFAULT_REPO.predictions_path
    positives_path: ClassVar[Path] = DEFAULT_REPO.positives_path
    negatives_path: ClassVar[Path] = DEFAULT_REPO.negatives_path
    unsure_path: ClassVar[Path] = DEFAULT_REPO.unsure_path
