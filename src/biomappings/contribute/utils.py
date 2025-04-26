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
        if mapping["subject_id"].startswith(f"{prefix}:"):
            mappings.append(mapping)
        elif mapping["object_id"].startswith(f"{prefix}:"):
            for key in ["_id", "_label"]:
                mapping[f"subject{key}"], mapping[f"object{key}"] = (
                    mapping[f"object{key}"],
                    mapping[f"subject{key}"],
                )
            if mapping["predicate_id"] != "skos:exactMatch":
                raise NotImplementedError
            mappings.append(mapping)
    return mappings
