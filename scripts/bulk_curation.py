"""Utilities for automated curation."""

import logging

from curies.vocabulary import exact_match, lexical_similarity_threshold_based_matching_process
from sssom_pydantic import MappingTool, SemanticMapping

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
    for mapping in load_predictions():
        if _accept_same_name(source, target, mapping):
            update = {
                "mapping_tool": MappingTool(name=provenance),
                "justification": lexical_similarity_threshold_based_matching_process,
            }
            accept.append(mapping.model_copy(update=update))
        else:
            leave.append(mapping)

    logger.info(f"Accepting {len(accept):,} exact text matches from {source} to {target}")
    write_predictions(leave)
    append_true_mappings(accept)


def _accept_same_name(subject_prefix: str, object_prefix: str, mapping: SemanticMapping) -> bool:
    if not mapping.predicate == exact_match:
        return False
    if not (
        (mapping.subject.prefix == subject_prefix and mapping.object.prefix == object_prefix)
        or (mapping.subject.prefix == object_prefix and mapping.object.prefix == subject_prefix)
    ):
        return False

    return (
        mapping.subject_name is not None
        and mapping.object_name is not None
        and mapping.subject_name.casefold() == mapping.object_name.casefold()
    )


def _main() -> None:
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
