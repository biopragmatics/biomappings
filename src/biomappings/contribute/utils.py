"""Utilities for contributing back to upstream resources."""

from __future__ import annotations

from biomappings import SemanticMapping, load_mappings

__all__ = [
    "get_curated_mappings",
]


def get_curated_mappings(prefix: str) -> list[SemanticMapping]:
    """Get mappings for a given prefix."""
    mappings = []
    for mapping in load_mappings():
        if mapping.subject.prefix == prefix:
            mappings.append(mapping)
        elif mapping.object.prefix == prefix:
            mappings.append(mapping.flip())
    return mappings
