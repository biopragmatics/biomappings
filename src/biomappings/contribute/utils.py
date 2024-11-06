"""Utilities for contributing back to upstream resources."""

from typing import Any

from biomappings import load_mappings

__all__ = [
    "get_curated_mappings",
]


def get_curated_mappings(prefix: str) -> list[dict[str, Any]]:
    """Get mappings for a given prefix."""
    mappings = []
    for mapping in load_mappings():
        if mapping["source prefix"] == prefix:
            mappings.append(mapping)
        elif mapping["target prefix"] == prefix:
            for key in ["prefix", "name", "identifier"]:
                mapping[f"source {key}"], mapping[f"target {key}"] = (
                    mapping[f"target {key}"],
                    mapping[f"source {key}"],
                )
            if mapping["relation"] != "skos:exactMatch":
                raise NotImplementedError
            mappings.append(mapping)
    return mappings
