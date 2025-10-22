"""Utilities."""

from __future__ import annotations

import os
from pathlib import Path

from curies.vocabulary import charlie
from sssom_curator import Repository
from sssom_pydantic import MappingSet

from .version import get_git_hash, get_version

__all__ = [
    "BIOMAPPINGS_NDEX_UUID",
    "CURATORS_PATH",
    "DATA_DIRECTORY",
    "DEFAULT_REPO",
    "IMG_DIRECTORY",
    "NEGATIVES_SSSOM_PATH",
    "POSITIVES_SSSOM_PATH",
    "PREDICTIONS_SSSOM_PATH",
    "PURL_BASE",
    "RESOURCE_PATH",
    "UNSURE_SSSOM_PATH",
    "get_script_url",
]

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.resolve()
RESOURCE_PATH = HERE.joinpath("resources")

POSITIVES_SSSOM_PATH = RESOURCE_PATH.joinpath("positive.sssom.tsv")
NEGATIVES_SSSOM_PATH = RESOURCE_PATH.joinpath("negative.sssom.tsv")
UNSURE_SSSOM_PATH = RESOURCE_PATH.joinpath("unsure.sssom.tsv")
PREDICTIONS_SSSOM_PATH = RESOURCE_PATH.joinpath("predictions.sssom.tsv")
CURATORS_PATH = RESOURCE_PATH.joinpath("curators.tsv")
PURL_BASE = "https://w3id.org/biopragmatics/biomappings/sssom"

DOCS_DIRECTORY = ROOT.joinpath("docs")
IMG_DIRECTORY = DOCS_DIRECTORY.joinpath("img")
DATA_DIRECTORY = DOCS_DIRECTORY.joinpath("_data")


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

META = MappingSet.model_validate(
    {
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "mapping_provider": "https://github.com/biopragmatics/biomappings",
        "mapping_set_description": "Biomappings is a repository of community curated and predicted equivalences and "
        "related mappings between named biological entities that are not available from primary sources. It's also a "
        "place where anyone can contribute curations of predicted mappings or their own novel mappings.",
        "mapping_set_id": f"{PURL_BASE}/biomappings.sssom.tsv",
        "mapping_set_title": "Biomappings",
        "mapping_set_version": get_version(with_git_hash=True),
        "creator_id": [charlie],
    }
)

DEFAULT_REPO = Repository(
    predictions_path=PREDICTIONS_SSSOM_PATH,
    positives_path=POSITIVES_SSSOM_PATH,
    negatives_path=NEGATIVES_SSSOM_PATH,
    unsure_path=UNSURE_SSSOM_PATH,
    basename="biomappings",
    purl_base=PURL_BASE,
    mapping_set=META,
    ndex_uuid=BIOMAPPINGS_NDEX_UUID,
)
