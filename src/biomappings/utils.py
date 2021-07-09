# -*- coding: utf-8 -*-

"""Utilities."""

import os
import re
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Any, Mapping, Optional, Tuple

import bioregistry
from bioregistry.external import get_miriam

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


def push() -> Optional[str]:
    """Push the git repo."""
    return _git("push")


def not_main() -> bool:
    """Return if on the master branch."""
    return "master" != _git("rev-parse", "--abbrev-ref", "HEAD")


def _git(*args: str) -> Optional[str]:
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603,S607
                ["git", *args],
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except CalledProcessError:
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


class MiriamValidator:
    """Validate prefix/identifier pairs based on the MIRIAM database."""

    def __init__(self, force_download: bool = False):  # noqa: D107
        self.entries = self._load_identifiers_entries(force_download=force_download)

    @staticmethod
    def _load_identifiers_entries(force_download: bool = False):
        return {
            prefix: {
                "pattern": re.compile(entry["pattern"]),
                "namespace_embedded": entry["namespaceEmbeddedInLui"],
            }
            for prefix, entry in get_miriam(force_download=force_download).items()
        }

    def namespace_embedded(self, prefix: str) -> bool:
        """Return True if the namespace is embedded for the given prefix."""
        if prefix in self.entries:
            return self.entries[prefix]["namespace_embedded"]
        return bioregistry.namespace_in_lui(prefix)

    def check_valid_prefix_id(self, prefix, identifier):
        """Check the prefix/identifier pair is valid."""
        if prefix in self.entries:
            entry = self.entries[prefix]
            if not re.match(entry["pattern"], identifier):
                raise InvalidIdentifier(prefix, identifier)
        elif bioregistry.get_pattern(prefix) is None:
            if bioregistry.validate(prefix, identifier):
                raise InvalidIdentifier(prefix, identifier)
        else:
            raise InvalidPrefix(prefix)

    def get_curie(self, prefix: str, identifier: str) -> str:
        """Return CURIE for a given prefix and identifier."""
        if self.namespace_embedded(prefix):
            return identifier
        else:
            return f"{prefix}:{identifier}"

    @staticmethod
    def get_url(prefix: str, identifier: str) -> str:
        """Return URL for a given prefix and identifier."""
        return bioregistry.get_link(prefix, identifier, use_bioregistry_io=False)
