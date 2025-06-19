"""Utilities for generating predictions with lexical predictions."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import click
import pyobo
import ssslm
from bioregistry import NormalizedNamedReference, NormalizedReference
from curies import Reference
from more_click import verbose_option
from tqdm import tqdm

from biomappings import SemanticMapping
from biomappings.mapping_graph import get_mutual_mapping_filter
from biomappings.resources import append_prediction_tuples, mapping_sort_key
from biomappings.utils import EXACT_MATCH, LEXICAL_MATCHING_PROCESS, CMapping, get_script_url

__all__ = [
    "append_lexical_predictions",
    "filter_custom",
    "filter_existing_xrefs",
    "lexical_prediction_cli",
    "predict_lexical_mappings",
]

logger = logging.getLogger(__name__)


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str,
    *,
    relation: str | None | Reference = None,
    custom_filter: CMapping | None = None,
    identifiers_are_names: bool = False,
    path: Path | None = None,
) -> None:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param custom_filter: A triple nested dictionary from source prefix to target prefix to source id to target id.
        Any source prefix, target prefix, source id combinations in this dictionary will be filtered.
    :param identifiers_are_names: The source prefix's identifiers should be considered as names
    :param path: A custom path to predictions TSV file
    """
    if isinstance(target_prefixes, str):
        target_prefixes = [target_prefixes]
    # by default, PyOBO wraps a gilda grounder, but
    # can be configured to use other NER/NEN systems
    grounder = pyobo.get_grounder(target_prefixes)
    predictions = predict_lexical_mappings(
        prefix,
        predicate=relation,
        grounder=grounder,
        provenance=provenance,
        identifiers_are_names=identifiers_are_names,
    )
    if custom_filter is not None:
        predictions = filter_custom(predictions, custom_filter)
    predictions = filter_existing_xrefs(predictions, [prefix, *target_prefixes])
    predictions = sorted(predictions, key=mapping_sort_key)
    tqdm.write(f"[{prefix}] generated {len(predictions):,} predictions")
    # since the function that constructs the predictions already
    # pre-standardizes, we don't have to worry about standardizing again
    append_prediction_tuples(predictions, path=path, standardize=False)


def predict_lexical_mappings(
    prefix: str,
    provenance: str,
    *,
    predicate: str | Reference | None = None,
    grounder: ssslm.Grounder,
    identifiers_are_names: bool = False,
    strict: bool = False,
) -> Iterable[SemanticMapping]:
    """Iterate over prediction tuples for a given prefix."""
    if predicate is None:
        predicate = EXACT_MATCH
    elif isinstance(predicate, str):
        predicate = NormalizedReference.from_curie(predicate)

    id_name_mapping = pyobo.get_id_name_mapping(prefix, strict=strict)
    it = tqdm(
        id_name_mapping.items(), desc=f"[{prefix}] lexical tuples", unit_scale=True, unit="name"
    )
    name_prediction_count = 0
    for identifier, name in it:
        for scored_match in grounder.get_matches(name):
            name_prediction_count += 1
            yield SemanticMapping(
                subject=NormalizedNamedReference(prefix=prefix, identifier=identifier, name=name),
                predicate=predicate,
                object=scored_match.reference,
                mapping_justification=LEXICAL_MATCHING_PROCESS,
                confidence=round(scored_match.score, 3),
                mapping_tool=provenance,
            )

    tqdm.write(f"[{prefix}] generated {name_prediction_count:,} predictions from names")

    if identifiers_are_names:
        it = tqdm(
            pyobo.get_ids(prefix), desc=f"[{prefix}] lexical tuples", unit_scale=True, unit="id"
        )
        identifier_prediction_count = 0
        for identifier in it:
            for scored_match in grounder.get_matches(identifier):
                name_prediction_count += 1
                yield SemanticMapping(
                    subject=NormalizedNamedReference(
                        prefix=prefix, identifier=identifier, name=identifier
                    ),
                    predicate=predicate,
                    object=scored_match.reference,
                    mapping_justification=LEXICAL_MATCHING_PROCESS,
                    confidence=round(scored_match.score, 3),
                    mapping_tool=provenance,
                )
        tqdm.write(
            f"[{prefix}] generated {identifier_prediction_count:,} predictions from identifiers"
        )


def filter_custom(
    mappings: Iterable[SemanticMapping],
    custom_filter: CMapping,
) -> Iterable[SemanticMapping]:
    """Filter out custom mappings."""
    counter = 0
    for mapping in mappings:
        if (
            custom_filter.get(mapping.subject.prefix, {})
            .get(mapping.object.prefix, {})
            .get(mapping.subject.identifier)
        ):
            counter += 1
            continue
        yield mapping
    logger.info("filtered out %d custom mapped matches", counter)


def filter_existing_xrefs(
    mappings: Iterable[SemanticMapping], prefixes: Iterable[str]
) -> Iterable[SemanticMapping]:
    """Filter predictions that match xrefs already loaded through PyOBO."""
    prefixes = set(prefixes)

    entity_to_mapped_prefixes: defaultdict[Reference, set[str]] = defaultdict(set)
    for subject_prefix in prefixes:
        for subject_id, target_prefix, object_id in pyobo.get_xrefs_df(subject_prefix).values:
            entity_to_mapped_prefixes[
                NormalizedReference(prefix=subject_prefix, identifier=subject_id)
            ].add(target_prefix)
            entity_to_mapped_prefixes[
                NormalizedReference(prefix=target_prefix, identifier=object_id)
            ].add(subject_prefix)

    n_predictions = 0
    for mapping in tqdm(mappings, desc="filtering predictions"):
        if (
            mapping.object.prefix in entity_to_mapped_prefixes[mapping.subject]
            or mapping.subject.prefix in entity_to_mapped_prefixes[mapping.object]
        ):
            n_predictions += 1
            continue
        yield mapping

    tqdm.write(
        f"filtered out {n_predictions:,} pre-mapped matches",
    )


def lexical_prediction_cli(
    script: str,
    prefix: str,
    target: str | list[str],
    *,
    filter_mutual_mappings: bool = False,
    identifiers_are_names: bool = False,
) -> None:
    """Construct a CLI and run it."""
    tt = target if isinstance(target, str) else ", ".join(target)

    @click.command(help=f"Generate mappings from {prefix} to {tt}")
    @verbose_option
    def main() -> None:
        """Generate mappings."""
        if filter_mutual_mappings:
            mutual_mapping_filter = get_mutual_mapping_filter(prefix, target)
        else:
            mutual_mapping_filter = None

        append_lexical_predictions(
            prefix,
            target,
            custom_filter=mutual_mapping_filter,
            provenance=get_script_url(script),
            identifiers_are_names=identifiers_are_names,
        )

    main()
