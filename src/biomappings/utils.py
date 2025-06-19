"""Utilities."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from subprocess import CalledProcessError, check_output

from bioregistry import NormalizedNamableReference

__all__ = [
    "RESOURCE_PATH",
    "CMapping",
    "get_canonical_tuple",
    "get_git_hash",
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

DOCS = ROOT.joinpath("docs")
IMG = DOCS.joinpath("img")
DATA = DOCS.joinpath("_data")


def get_git_hash() -> str | None:
    """Get the git hash.

    :return:
        The git hash, equals 'UNHASHED' if encountered CalledProcessError, signifying that the
        code is not installed in development mode.
    """
    rv = _git("rev-parse", "HEAD")
    if not rv:
        return None
    return rv[:6]


def commit(message: str) -> str | None:
    """Make a commit with the following message."""
    return _git("commit", "-m", message, "-a")


def push(branch_name: str | None = None) -> str | None:
    """Push the git repo."""
    if branch_name is not None:
        return _git("push", "origin", branch_name)
    else:
        return _git("push")


def not_main() -> bool:
    """Return if on the master branch."""
    return "master" != _git("rev-parse", "--abbrev-ref", "HEAD")


def get_branch() -> str:
    """Return current git branch."""
    rv = _git("branch", "--show-current")
    if rv is None:
        raise RuntimeError
    return rv


def _git(*args: str) -> str | None:
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603
                ["git", *args],  # noqa:S607
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError as e:
            print(e)  # noqa:T201
            return None
        else:
            return ret.strip().decode("utf-8")


def get_script_url(fname: str) -> str:
    """Get the source path for this script.

    :param fname: Pass ``__file__`` as the argument to this function.
    :return: The script's URL to GitHub
    """
    commit_hash = get_git_hash()
    script_name = os.path.basename(fname)
    return f"https://github.com/biomappings/biomappings/blob/{commit_hash}/scripts/{script_name}"


def get_canonical_tuple(mapping) -> tuple[str, str, str, str]:
    """Get the canonical tuple from a mapping entry."""
    source = mapping.subject
    target = mapping.object
    if source > target:
        source, target = target, source
    return (*source.pair, *target.pair)


#: A filter 3-dictionary of source prefix to target prefix to source identifier to target identifier
CMapping = Mapping[str, Mapping[str, Mapping[str, str]]]

EXACT_MATCH = NormalizedNamableReference.from_curie("skos:exactMatch")
NARROW_MATCH = NormalizedNamableReference.from_curie("skos:narrowMatch")
BROAD_MATCH = NormalizedNamableReference.from_curie("skos:broadMatch")

LEXICAL_MATCHING_PROCESS = NormalizedNamableReference.from_curie("semapv:LexicalMatching")
MANUAL_MAPPING_CURATION = NormalizedNamableReference.from_curie("semapv:ManualMappingCuration")
