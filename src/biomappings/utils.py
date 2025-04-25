"""Utilities."""

import os
from collections.abc import Mapping
from pathlib import Path
from subprocess import CalledProcessError, check_output
from typing import Any, Optional

import bioregistry

__all__ = [
    "CMapping",
    "InvalidIdentifier",
    "InvalidIdentifierPattern",
    "InvalidNormIdentifier",
    "UnregisteredPrefix",
    "UnstandardizedPrefix",
    "check_valid_prefix_id",
    "get_canonical_tuple",
    "get_curie",
    "get_git_hash",
    "get_script_url",
]

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.resolve()
RESOURCE_PATH = HERE.joinpath("resources")
DOCS = ROOT.joinpath("docs")
IMG = DOCS.joinpath("img")
DATA = DOCS.joinpath("_data")


def get_git_hash() -> Optional[str]:
    """Get the git hash.

    :return:
        The git hash, equals 'UNHASHED' if encountered CalledProcessError, signifying that the
        code is not installed in development mode.
    """
    rv = _git("rev-parse", "HEAD")
    if not rv:
        return None
    return rv[:6]


def commit(message: str) -> Optional[str]:
    """Make a commit with the following message."""
    return _git("commit", "-m", message, "-a")


def push(branch_name: Optional[str] = None) -> Optional[str]:
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


def _git(*args: str) -> Optional[str]:
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


def get_canonical_tuple(mapping: Mapping[str, Any]) -> tuple[str, str, str, str]:
    """Get the canonical tuple from a mapping entry."""
    source = mapping["source prefix"], mapping["source identifier"]
    target = mapping["target prefix"], mapping["target identifier"]
    if source > target:
        source, target = target, source
    return (*source, *target)


class UnregisteredPrefix(ValueError):
    """Raised for an invalid prefix."""


class UnstandardizedPrefix(ValueError):
    """Raised for an unstandardized prefix."""

    def __init__(self, prefix: str, norm_prefix: str):
        """Initialize the error.

        :param prefix: A CURIE's prefix
        :param norm_prefix: The normalized prefid
        """
        self.prefix = prefix
        self.norm_prefix = norm_prefix

    def __str__(self) -> str:
        return f"{self.prefix} should be standardized to {self.norm_prefix}"


class InvalidIdentifier(ValueError):
    """Raised for an invalid identifier."""

    def __init__(self, prefix: str, identifier: str):
        """Initialize the error.

        :param prefix: A CURIE's prefix
        :param identifier: A CURIE's identifier
        """
        self.prefix = prefix
        self.identifier = identifier


class InvalidIdentifierPattern(InvalidIdentifier):
    """Raised for an identifier that doesn't match the pattern."""

    def __init__(self, prefix: str, identifier: str, pattern):
        """Initialize the error.

        :param prefix: A CURIE's prefix
        :param identifier: A CURIE's identifier
        :param pattern: A regular expression pattern
        """
        super().__init__(prefix, identifier)
        self.pattern = pattern

    def __str__(self) -> str:
        return f"{self.prefix}:{self.identifier} does not match pattern {self.pattern}"


class InvalidNormIdentifier(InvalidIdentifier):
    """Raised for an invalid normalized identifier."""

    def __init__(self, prefix: str, identifier: str, norm_identifier: str):
        """Initialize the error.

        :param prefix: A CURIE's prefix
        :param identifier: A CURIE's identifier
        :param norm_identifier: The normalized version of the identifier
        """
        super().__init__(prefix, identifier)
        self.norm_identifier = norm_identifier

    def __str__(self) -> str:
        return f"{self.prefix}:{self.identifier} does not match normalized CURIE {self.prefix}:{self.norm_identifier}"


def check_valid_prefix_id(prefix: str, identifier: str):
    """Check the prefix/identifier pair is valid.

    :param prefix:
        The prefix from a CURIE
    :param identifier:
        The local unique identifier from a CURIE
    :raises UnregisteredPrefix:
        if the prefix is not registered with the Bioregistry
    :raises UnstandardizedPrefix:
        if the prefix is not standardized w.r.t. the Bioregistry
    :raises InvalidNormIdentifier:
        if the identifier is not standardized, either against the MIRIAM
        standard, if available, or against the Bioregistry standard
    :raises InvalidIdentifierPattern:
        if the does not match the appropriate regular expression for MIRIAM
        (if available) or for the Bioregistry. If no regular expression is
        available, then this check is not applied.
    :raises RuntimeError:
        If the preconditions for bioregistry standardization aren't met. However,
        this shouldn't be possible in practice, and this documentation is
        merely a formality.
    """
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        raise UnregisteredPrefix(prefix)
    if prefix != resource.prefix:
        raise UnstandardizedPrefix(prefix, resource.prefix)

    norm_id = resource.standardize_identifier(identifier)
    if norm_id != identifier:
        raise InvalidNormIdentifier(prefix, identifier, norm_id)
    pattern = resource.get_pattern_re()
    if pattern is not None and not pattern.match(identifier):
        raise InvalidIdentifierPattern(prefix, identifier, pattern)


def get_curie(prefix: str, identifier: str, *, preferred: bool = False) -> str:
    """Get a normalized curie from a pre-parsed prefix/identifier pair."""
    prefix_norm, identifier_norm = bioregistry.normalize_parsed_curie(prefix, identifier)
    if prefix_norm is None or identifier_norm is None:
        raise ValueError(f"could not normalize {prefix}:{identifier}")
    if preferred:
        prefix_norm = bioregistry.get_preferred_prefix(prefix_norm) or prefix_norm
    return f"{prefix_norm}:{identifier_norm}"


#: A filter 3-dictionary of source prefix to target prefix to source identifier to target identifier
CMapping = Mapping[str, Mapping[str, Mapping[str, str]]]
