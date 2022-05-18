# -*- coding: utf-8 -*-

"""Utilities."""

import os
import re
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Any, Mapping, Optional, Tuple

import bioregistry

HERE = os.path.dirname(os.path.abspath(__file__))
RESOURCE_PATH = os.path.abspath(os.path.join(HERE, "resources"))
DOCS = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "docs"))
IMG = os.path.join(DOCS, "img")
DATA = os.path.join(DOCS, "_data")


def get_git_hash() -> Optional[str]:
    """Get the git hash.

    :return:
        The git hash, equals 'UNHASHED' if encountered CalledProcessError, signifying that the
        code is not installed in development mode.
    """
    rv = _git("rev-parse", "HEAD")
    if rv:
        return rv[:6]


def commit(message: str) -> Optional[str]:
    """Make a commit with the following message."""
    return _git("commit", "-m", message, "-a")


def push(branch_name: str = None) -> Optional[str]:
    """Push the git repo."""
    if branch_name:
        return _git("push", "origin", branch_name)
    else:
        return _git("push")


def not_main() -> bool:
    """Return if on the master branch."""
    return "master" != _git("rev-parse", "--abbrev-ref", "HEAD")


def get_branch() -> str:
    """Return current git branch."""
    return _git("branch", "--show-current")


def _git(*args: str) -> Optional[str]:
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603,S607
                ["git", *args],
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError as e:
            print(e)
            return
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


def get_canonical_tuple(mapping: Mapping[str, Any]) -> Tuple[str, str, str, str]:
    """Get the canonical tuple from a mapping entry."""
    source = mapping["source prefix"], mapping["source identifier"]
    target = mapping["target prefix"], mapping["target identifier"]
    if source > target:
        source, target = target, source
    return (*source, *target)


class InvalidPrefix(ValueError):
    """Raised for an invalid prefix."""


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

    def __str__(self) -> str:  # noqa:D105
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

    def __str__(self) -> str:  # noqa:D105
        return f"{self.prefix}:{self.identifier} does not match normalized CURIE {self.prefix}:{self.norm_identifier}"


def check_valid_prefix_id(prefix, identifier):
    """Check the prefix/identifier pair is valid."""
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        raise InvalidPrefix(prefix)
    if prefix not in {"ncit"}:
        norm_identifier = resource.miriam_standardize_identifier(identifier)
        if norm_identifier != identifier:
            raise InvalidNormIdentifier(prefix, identifier, norm_identifier)
        return
    miriam_pattern = resource.miriam.get("pattern") if resource.miriam else None
    if not miriam_pattern:
        pattern = resource.get_pattern_re()
    else:
        pattern = re.compile(miriam_pattern)
    if pattern is not None and not pattern.match(identifier):
        raise InvalidIdentifierPattern(prefix, identifier, pattern)


def get_curie(prefix: str, identifier: str) -> str:
    """Get a normalized curie from a pre-parsed prefix/identifier pair."""
    p, i = bioregistry.normalize_parsed_curie(prefix, identifier)
    if p is None or i is None:
        raise ValueError
    return f"{p}:{i}"
