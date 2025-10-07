"""Utilities for generating predictions with lexical predictions."""

from __future__ import annotations

import logging
import typing
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Callable, Literal, TypeAlias, cast

import click
import curies
import pandas as pd
import pyobo
import ssslm
from bioregistry import NormalizedNamableReference, NormalizedNamedReference, NormalizedReference
from more_click import verbose_option
from pyobo import get_grounder
from tqdm.auto import tqdm

from biomappings import SemanticMapping
from biomappings.mapping_graph import get_mutual_mapping_filter
from biomappings.resources import append_prediction_tuples
from biomappings.utils import EXACT_MATCH, LEXICAL_MATCHING_PROCESS, CMapping, get_script_url

__all__ = [
    "append_lexical_predictions",
    "filter_custom",
    "filter_existing_xrefs",
    "lexical_prediction_cli",
    "predict_lexical_mappings",
]

logger = logging.getLogger(__name__)

RecognitionMethod: TypeAlias = Literal["ner", "grounding"]
PredictionMethod: TypeAlias = RecognitionMethod | Literal["embedding"]


def append_lexical_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    provenance: str,
    *,
    relation: str | None | curies.NamableReference = None,
    custom_filter: CMapping | None = None,
    identifiers_are_names: bool = False,
    path: Path | None = None,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    batch_size: int | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
) -> None:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param provenance: The provenance text. Typically generated with
        ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param custom_filter: A triple nested dictionary from source prefix to target prefix
        to source id to target id. Any source prefix, target prefix, source id
        combinations in this dictionary will be filtered.
    :param identifiers_are_names: The source prefix's identifiers should be considered
        as names
    :param path: A custom path to predictions TSV file
    :param method: The lexical predication method to use
    :param cutoff: an optional minimum prediction confidence cutoff
    :param batch_size: The batch size for embeddings
    :param custom_filter_function: A custom function that decides if semantic mappings
        should be kept, applied after all other logic.
    """
    if isinstance(target_prefixes, str):
        targets = [target_prefixes]
    else:
        targets = list(target_prefixes)

    if method is None or method in typing.get_args(RecognitionMethod):
        # by default, PyOBO wraps a gilda grounder, but
        # can be configured to use other NER/NEN systems
        grounder = get_grounder(targets)
        predictions = predict_lexical_mappings(
            prefix,
            predicate=relation,
            grounder=grounder,
            provenance=provenance,
            identifiers_are_names=identifiers_are_names,
            method=cast(RecognitionMethod | None, method),
        )
        if custom_filter is not None:
            predictions = filter_custom(predictions, custom_filter)
        predictions = filter_existing_xrefs(predictions, [prefix, *targets])

    elif method == "embedding":
        import pyobo.api.embedding

        if cutoff is None:
            cutoff = 0.65
        if batch_size is None:
            batch_size = 10_000

        model = pyobo.api.embedding.get_text_embedding_model()
        source_df = pyobo.get_text_embeddings_df(prefix, model=model)

        predictions = []
        for target in tqdm(targets, disable=len(targets) == 1):
            target_df = pyobo.get_text_embeddings_df(target, model=model)
            for source_id, target_id, confidence in _calculate_similarities(
                source_df, target_df, batch_size, cutoff
            ):
                predictions.append(
                    SemanticMapping(
                        subject=_r(prefix=prefix, identifier=source_id),
                        predicate=relation,
                        object=_r(prefix=target, identifier=target_id),
                        justification=LEXICAL_MATCHING_PROCESS,
                        confidence=confidence,
                        mapping_tool=provenance,
                    )
                )

    else:
        raise ValueError(f"invalid lexical prediction method: {method}")

    if custom_filter_function:
        predictions = list(filter(custom_filter_function, predictions))

    predictions = sorted(predictions)
    tqdm.write(f"[{prefix}] generated {len(predictions):,} predictions")

    # since the function that constructs the predictions already
    # pre-standardizes, we don't have to worry about standardizing again
    append_prediction_tuples(predictions, path=path)


def _calculate_similarities(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    batch_size: int | None,
    cutoff: float,
) -> list[tuple[str, str, float]]:
    if batch_size is not None:
        return _calculate_similarities_batched(
            source_df, target_df, batch_size=batch_size, cutoff=cutoff
        )
    else:
        return _calculate_similarities_unbatched(source_df, target_df, cutoff=cutoff)


def _calculate_similarities_batched(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    *,
    batch_size: int,
    cutoff: float,
) -> list[tuple[str, str, float]]:
    import torch
    from sentence_transformers.util import cos_sim

    similarities = []
    source_df_numpy = source_df.to_numpy()
    for target_start in tqdm(range(0, len(target_df), batch_size), unit="target batch"):
        target_end = target_start + batch_size
        tqdm.write(f"target batch from {target_start} to {target_end}")
        target_batch_df = target_df.iloc[target_start:target_end]
        similarity = cos_sim(
            source_df_numpy,
            target_batch_df.to_numpy(),
        )
        source_target_pairs = torch.nonzero(similarity >= cutoff, as_tuple=False)
        for source_idx, target_idx in source_target_pairs:
            source_id: str = source_df.index[source_idx.item()]
            target_id: str = target_batch_df.index[target_idx.item()]
            similarities.append(
                (
                    source_id,
                    target_id,
                    similarity[source_idx, target_idx].item(),
                )
            )
    return similarities


def _calculate_similarities_unbatched(
    source_df: pd.DataFrame, target_df: pd.DataFrame, *, cutoff: float
) -> list[tuple[str, str, float]]:
    import torch
    from sentence_transformers.util import cos_sim

    similarities = []
    similarity = cos_sim(source_df.to_numpy(), target_df.to_numpy())
    source_target_pairs = torch.nonzero(similarity >= cutoff, as_tuple=False)
    for source_idx, target_idx in source_target_pairs:
        source_id: str = source_df.index[source_idx.item()]
        target_id: str = target_df.index[target_idx.item()]
        similarities.append(
            (
                source_id,
                target_id,
                similarity[source_idx, target_idx].item(),
            )
        )
    return similarities


def _r(prefix: str, identifier: str) -> NormalizedNamableReference:
    return NormalizedNamableReference(
        prefix=prefix, identifier=identifier, name=pyobo.get_name(prefix, identifier)
    )


def predict_lexical_mappings(
    prefix: str,
    provenance: str,
    *,
    predicate: str | curies.NamableReference | None = None,
    grounder: ssslm.Grounder,
    identifiers_are_names: bool = False,
    strict: bool = False,
    method: RecognitionMethod | None = None,
) -> Iterable[SemanticMapping]:
    """Iterate over prediction tuples for a given prefix."""
    if predicate is None:
        predicate = EXACT_MATCH
    elif isinstance(predicate, str):
        predicate = NormalizedNamableReference.from_curie(predicate)

    id_name_mapping = pyobo.get_id_name_mapping(prefix, strict=strict)
    it = tqdm(
        id_name_mapping.items(), desc=f"[{prefix}] lexical tuples", unit_scale=True, unit="name"
    )

    if method is None or method == "grounding":

        def _get_matches(s: str) -> list[ssslm.Match]:
            return grounder.get_matches(s)

    elif method == "ner":

        def _get_matches(s: str) -> list[ssslm.Match]:
            return [a.match for a in grounder.annotate(s)]
    else:
        raise ValueError(f"invalid lexical method: {method}")

    name_prediction_count = 0
    for identifier, name in it:
        for scored_match in _get_matches(name):
            name_prediction_count += 1
            yield SemanticMapping(
                subject=NormalizedNamedReference(prefix=prefix, identifier=identifier, name=name),
                predicate=predicate,
                object=scored_match.reference,
                justification=LEXICAL_MATCHING_PROCESS,
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
            for scored_match in _get_matches(identifier):
                name_prediction_count += 1
                yield SemanticMapping(
                    subject=NormalizedNamedReference(
                        prefix=prefix, identifier=identifier, name=identifier
                    ),
                    predicate=predicate,
                    object=scored_match.reference,
                    justification=LEXICAL_MATCHING_PROCESS,
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

    entity_to_mapped_prefixes: defaultdict[curies.Reference, set[str]] = defaultdict(set)
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
    predicate: str | None | curies.NamableReference = None,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
) -> None:
    """Construct a CLI and run it."""
    tt = target if isinstance(target, str) else ", ".join(target)

    @click.command(help=f"Generate mappings from {prefix} to {tt}")
    @verbose_option  # type:ignore[misc]
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
            relation=predicate,
            method=method,
            cutoff=cutoff,
            custom_filter_function=custom_filter_function,
        )

    main()
