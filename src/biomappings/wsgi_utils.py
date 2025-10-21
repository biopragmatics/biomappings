"""Utilities for the web app."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

import curies
import sssom_pydantic
from sssom_pydantic import MappingSet, Metadata, SemanticMapping
from sssom_pydantic.process import Hasher

from ._git_utils import _git

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
    metadata_path: str | Path | None = None,
    metadata: MappingSet | Metadata | None = None,
    converter: curies.Converter | None = None,
    include_mappings: Iterable[SemanticMapping] | None = None,
    exclude_mappings: Iterable[SemanticMapping] | None = None,
    exclude_mappings_key: Hasher[SemanticMapping, X] | None = None,
    drop_duplicates: bool = False,
    drop_duplicates_key: Hasher[SemanticMapping, Y] | None = None,
) -> None:
    """Append eagerly with linting at the same time."""
    mappings, converter_processed, _mapping_set = sssom_pydantic.read(
        path, metadata_path=metadata_path, metadata=metadata, converter=converter
    )

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
        exclude_mappings=exclude_mappings,
        exclude_mappings_key=exclude_mappings_key,
        drop_duplicates=drop_duplicates,
        drop_duplicates_key=drop_duplicates_key,
        sort=True,
    )
