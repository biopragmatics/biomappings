"""Utilities for automated curation."""

import logging
from collections.abc import Mapping

from biomappings.resources import (
    append_true_mappings,
    load_predictions,
    write_predictions,
)
from biomappings.utils import get_script_url

logger = logging.getLogger(__name__)

provenance = get_script_url(__file__)


def bulk_accept_same_text(source: str, target: str) -> None:
    """Accept exact matches in bulk between these two resources if labels are the same."""
    accept = []
    leave = []
    for p in load_predictions():
        if _accept_same_name(source, target, p):
            p["source"] = provenance
            p["type"] = "semapv:LexicalSimilarityThresholdMatching"
            accept.append(p)
        else:
            leave.append(p)

    logger.info(f"Accepting {len(accept):,} exact text matches from {source} to {target}")
    write_predictions(leave)
    append_true_mappings(accept)


def _accept_same_name(s, t, p: Mapping[str, str]) -> bool:
    if not p["relation"] == "skos:exactMatch":
        return False
    if not (
        (p["source prefix"] == s and p["target prefix"] == t)
        or (p["source prefix"] == t and p["target prefix"] == s)
    ):
        return False
    return p["source name"].casefold() == p["target name"].casefold()


def _main():
    bulk_accept_same_text("chebi", "mesh")
    bulk_accept_same_text("mesh", "ncit")
    bulk_accept_same_text("mesh", "umls")
    bulk_accept_same_text("mesh", "hp")
    bulk_accept_same_text("mesh", "efo")
    bulk_accept_same_text("doid", "umls")
    bulk_accept_same_text("doid", "mesh")
    bulk_accept_same_text("doid", "efo")


if __name__ == "__main__":
    _main()
