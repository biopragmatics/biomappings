"""Validation tests for :mod:`biomappings`."""

from pathlib import Path
from typing import ClassVar

from biomappings.curator import testing
from biomappings.utils import (
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
)


class TestIntegrity(testing.PathIntegrityTestCase):
    """Data integrity tests."""

    predictions_path: ClassVar[Path] = PREDICTIONS_SSSOM_PATH
    positives_path: ClassVar[Path] = POSITIVES_SSSOM_PATH
    negatives_path: ClassVar[Path] = NEGATIVES_SSSOM_PATH
    unsure_path: ClassVar[Path] = UNSURE_SSSOM_PATH
