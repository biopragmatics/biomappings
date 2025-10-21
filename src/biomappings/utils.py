"""Utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

from ._git_utils import _git

__all__ = [
    "BIOMAPPINGS_NDEX_UUID",
    "CURATED_PATHS",
    "CURATORS_PATH",
    "NEGATIVES_SSSOM_PATH",
    "POSITIVES_SSSOM_PATH",
    "PREDICTIONS_SSSOM_PATH",
    "PURL_BASE",
    "RESOURCE_PATH",
    "UNSURE_SSSOM_PATH",
    "get_git_hash",
    "get_script_url",
]

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.resolve()
RESOURCE_PATH = HERE.joinpath("resources")

POSITIVES_SSSOM_PATH = RESOURCE_PATH.joinpath("positive.sssom.tsv")
NEGATIVES_SSSOM_PATH = RESOURCE_PATH.joinpath("negative.sssom.tsv")
UNSURE_SSSOM_PATH = RESOURCE_PATH.joinpath("unsure.sssom.tsv")
CURATED_PATHS = [POSITIVES_SSSOM_PATH, NEGATIVES_SSSOM_PATH, UNSURE_SSSOM_PATH]
PREDICTIONS_SSSOM_PATH = RESOURCE_PATH.joinpath("predictions.sssom.tsv")
CURATORS_PATH = RESOURCE_PATH.joinpath("curators.tsv")
PURL_BASE = "https://w3id.org/biopragmatics/biomappings/sssom"

DOCS = ROOT.joinpath("docs")
IMG = DOCS.joinpath("img")
DATA = DOCS.joinpath("_data")


class Repository(NamedTuple):
    """A quadruple of paths."""

    predictions_path: Path
    positives_path: Path
    negatives_path: Path
    unsure_path: Path


DEFAULT_REPO = Repository(
    predictions_path=PREDICTIONS_SSSOM_PATH,
    positives_path=POSITIVES_SSSOM_PATH,
    negatives_path=NEGATIVES_SSSOM_PATH,
    unsure_path=UNSURE_SSSOM_PATH,
)


def get_git_hash() -> str | None:
    """Get the git hash.

    :returns: The git hash, equals 'UNHASHED' if encountered CalledProcessError,
        signifying that the code is not installed in development mode.
    """
    rv = _git("rev-parse", "HEAD")
    if not rv:
        return None
    return rv[:6]


def get_script_url(fname: str) -> str:
    """Get the source path for this script.

    :param fname: Pass ``__file__`` as the argument to this function.

    :returns: The script's URL to GitHub
    """
    commit_hash = get_git_hash()
    script_name = os.path.basename(fname)
    return f"https://github.com/biomappings/biomappings/blob/{commit_hash}/scripts/{script_name}"


#: THe NDEx UUID
BIOMAPPINGS_NDEX_UUID = "402d1fd6-49d6-11eb-9e72-0ac135e8bacf"
