"""Utilities for the web app."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from ._git_utils import _git

if TYPE_CHECKING:
    import curies
    from sssom_pydantic import SemanticMapping

__all__ = [
    "commit",
    "get_branch",
    "insert",
    "not_main",
    "push",
]

X = TypeVar("X")
Y = TypeVar("Y")


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


def insert(
    path: Path,
    *,
    converter: curies.Converter | None = None,
    include_mappings: Iterable[SemanticMapping] | None = None,
) -> None:
    """Append eagerly with linting at the same time."""
    import sssom_pydantic

    mappings, converter_processed, metadata = sssom_pydantic.read(path, converter=converter)

    if include_mappings is not None:
        prefixes: set[str] = set()
        for mapping in include_mappings:
            prefixes.update(mapping.get_prefixes())
            mappings.append(mapping)

        for prefix in prefixes:
            if not converter_processed.standardize_prefix(prefix):
                raise NotImplementedError("amending prefixes not yet implemented")

    sssom_pydantic.write(
        mappings,
        path,
        converter=converter_processed,
        metadata=metadata,
        sort=True,
        drop_duplicates=True,
    )
