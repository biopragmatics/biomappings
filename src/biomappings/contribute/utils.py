"""Utilities for contributing back to upstream resources."""

from typing import Any, List, Mapping

from biomappings import load_mappings

__all__ = [
    "get_mappings",
]


def get_mappings(prefix: str) -> List[Mapping[str, Any]]:
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
