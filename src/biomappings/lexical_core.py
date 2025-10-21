"""Utilities for generating predictions with lexical predictions."""

from __future__ import annotations

import logging
import typing
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Literal, TypeAlias, cast

import curies
import networkx as nx
import pyobo
import ssslm
from bioregistry import NormalizedNamableReference, NormalizedNamedReference
from curies.vocabulary import exact_match, lexical_matching_process
from pyobo import get_grounder
from sssom_pydantic import MappingTool, SemanticMapping
from tqdm.auto import tqdm

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "PredictionMethod",
    "RecognitionMethod",
    "filter_custom",
    "filter_existing_xrefs",
    "get_predictions",
    "predict_embedding_mappings",
    "predict_lexical_mappings",
]

logger = logging.getLogger(__name__)

RecognitionMethod: TypeAlias = Literal["ner", "grounding"]
PredictionMethod: TypeAlias = RecognitionMethod | Literal["embedding"]

#: A filter 3-dictionary of source prefix to target prefix to source identifier to target identifier
NestedMappingDict: TypeAlias = Mapping[str, Mapping[str, Mapping[str, str]]]


def get_predictions(
    prefix: str,
    target_prefixes: str | Iterable[str],
    mapping_tool: str | MappingTool,
    *,
    relation: str | None | curies.NamableReference = None,
    identifiers_are_names: bool = False,
    method: PredictionMethod | None = None,
    cutoff: float | None = None,
    batch_size: int | None = None,
    custom_filter_function: Callable[[SemanticMapping], bool] | None = None,
    progress: bool = True,
    filter_mutual_mappings: bool = False,
) -> list[SemanticMapping]:
    """Add lexical matching-based predictions to the Biomappings predictions.tsv file.

    :param prefix: The source prefix
    :param target_prefixes: The target prefix or prefixes
    :param mapping_tool: The provenance text. Typically generated with
        ``biomappings.utils.get_script_url(__file__)``.
    :param relation: The relationship. Defaults to ``skos:exactMatch``.
    :param identifiers_are_names: The source prefix's identifiers should be considered
        as names
    :param method: The lexical predication method to use
    :param cutoff: an optional minimum prediction confidence cutoff
    :param batch_size: The batch size for embeddings
    :param custom_filter_function: A custom function that decides if semantic mappings
        should be kept, applied after all other logic.
    :param progress: Should progress be shown?
    :param filter_mutual_mappings: Should mappings between entities in the given
        namespaces be filtered out?
    """
    if isinstance(target_prefixes, str):
        targets = [target_prefixes]
    else:
        targets = list(target_prefixes)

    if isinstance(mapping_tool, str):
        mapping_tool = MappingTool(name=mapping_tool)

    if method is None or method in typing.get_args(RecognitionMethod):
        # by default, PyOBO wraps a gilda grounder, but
        # can be configured to use other NER/NEN systems
        grounder = get_grounder(targets)
        predictions = predict_lexical_mappings(
            prefix,
            predicate=relation,
            grounder=grounder,
            mapping_tool=mapping_tool,
            identifiers_are_names=identifiers_are_names,
            method=cast(RecognitionMethod | None, method),
        )
    elif method == "embedding":
        predictions = predict_embedding_mappings(
            prefix,
            target_prefixes,
            mapping_tool=mapping_tool,
            relation=relation,
            cutoff=cutoff,
            batch_size=batch_size,
            progress=progress,
        )
    else:
        raise ValueError(f"invalid lexical prediction method: {method}")

    if filter_mutual_mappings:
        mutual_mapping_filter = get_mutual_mapping_filter(prefix, target_prefixes)
        predictions = filter_custom(predictions, mutual_mapping_filter)

    predictions = filter_existing_xrefs(predictions, [prefix, *targets])

    if custom_filter_function:
        predictions = list(filter(custom_filter_function, predictions))

    predictions = sorted(predictions)
    return predictions


def predict_embedding_mappings(
    prefix: str,
    target_prefixes: str | Iterable[str],
    mapping_tool: str | MappingTool,
    *,
    relation: str | None | curies.NamableReference = None,
    cutoff: float | None = None,
    batch_size: int | None = None,
    progress: bool = True,
) -> list[SemanticMapping]:
    """Predict semantic mappings with embeddings."""
    import pyobo.api.embedding

    if isinstance(target_prefixes, str):
        targets = [target_prefixes]
    else:
        targets = list(target_prefixes)
    if cutoff is None:
        cutoff = 0.65
    if batch_size is None:
        batch_size = 10_000

    model = pyobo.api.embedding.get_text_embedding_model()
    source_df = pyobo.get_text_embeddings_df(prefix, model=model)

    if isinstance(mapping_tool, str):
        mapping_tool = MappingTool(name=mapping_tool)

    predictions = []
    for target in tqdm(targets, disable=len(targets) == 1):
        target_df = pyobo.get_text_embeddings_df(target, model=model)
        for source_id, target_id, confidence in _calculate_similarities(
            source_df, target_df, batch_size, cutoff, progress=progress
        ):
            predictions.append(
                SemanticMapping(
                    subject=_r(prefix=prefix, identifier=source_id),
                    predicate=relation,
                    object=_r(prefix=target, identifier=target_id),
                    justification=lexical_matching_process,
                    confidence=confidence,
                    mapping_tool=mapping_tool,
                )
            )
    return predictions


def _calculate_similarities(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    batch_size: int | None,
    cutoff: float,
    progress: bool = True,
) -> list[tuple[str, str, float]]:
    if batch_size is not None:
        return _calculate_similarities_batched(
            source_df, target_df, batch_size=batch_size, cutoff=cutoff, progress=progress
        )
    else:
        return _calculate_similarities_unbatched(source_df, target_df, cutoff=cutoff)


def _calculate_similarities_batched(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    *,
    batch_size: int,
    cutoff: float,
    progress: bool = True,
) -> list[tuple[str, str, float]]:
    import torch
    from sentence_transformers.util import cos_sim

    similarities = []
    source_df_numpy = source_df.to_numpy()
    for target_start in tqdm(
        range(0, len(target_df), batch_size), unit="target batch", disable=not progress
    ):
        target_end = target_start + batch_size
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
    mapping_tool: str | MappingTool,
    *,
    predicate: str | curies.NamableReference | None = None,
    grounder: ssslm.Grounder,
    identifiers_are_names: bool = False,
    strict: bool = False,
    method: RecognitionMethod | None = None,
) -> Iterable[SemanticMapping]:
    """Iterate over prediction tuples for a given prefix."""
    if predicate is None:
        predicate = exact_match
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

    if isinstance(mapping_tool, str):
        mapping_tool = MappingTool(name=mapping_tool)

    name_prediction_count = 0
    for identifier, name in it:
        for scored_match in _get_matches(name):
            name_prediction_count += 1
            yield SemanticMapping(
                subject=NormalizedNamedReference(prefix=prefix, identifier=identifier, name=name),
                predicate=predicate,
                object=scored_match.reference,
                justification=lexical_matching_process,
                confidence=round(scored_match.score, 3),
                mapping_tool=mapping_tool,
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
                    justification=lexical_matching_process,
                    confidence=round(scored_match.score, 3),
                    mapping_tool=mapping_tool,
                )
        tqdm.write(
            f"[{prefix}] generated {identifier_prediction_count:,} predictions from identifiers"
        )


def filter_custom(
    mappings: Iterable[SemanticMapping],
    custom_filter: NestedMappingDict,
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
    """Filter predictions that match xrefs already loaded through PyOBO.

    :param mappings: Semantic mappings to filter
    :param prefixes: Prefixes for resources to check for existing mappings
    :yields: Filtered semantic mappings
    """
    entity_to_mapped_prefixes = _get_entity_to_mapped_prefixes(prefixes)

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


def _get_entity_to_mapped_prefixes(prefixes: Iterable[str]) -> dict[curies.Reference, set[str]]:
    entity_to_mapped_prefixes: defaultdict[curies.Reference, set[str]] = defaultdict(set)
    for prefix in prefixes:
        for mapping in pyobo.get_semantic_mappings(prefix):
            entity_to_mapped_prefixes[mapping.subject].add(mapping.object.prefix)
            entity_to_mapped_prefixes[mapping.object].add(mapping.subject.prefix)
    return dict(entity_to_mapped_prefixes)


def get_mutual_mapping_filter(prefix: str, targets: str | Iterable[str]) -> NestedMappingDict:
    """Get a custom filter dictionary induced over the mutual mapping graph with all target prefixes.

    :param prefix: The source prefix
    :param targets: All potential target prefixes

    :returns: A filter 3-dictionary of source prefix to target prefix to source
        identifier to target identifier
    """
    if isinstance(targets, str):
        targets = [targets]
    graph = _mutual_mapping_graph([prefix, *targets])
    rv: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for node in graph:
        if node.prefix != prefix:
            continue
        for xref_prefix, xref_identifier in nx.single_source_shortest_path(graph, node):
            rv[xref_prefix][node.identifier] = xref_identifier
    return {prefix: dict(rv)}


def _mutual_mapping_graph(prefixes: Iterable[str]) -> nx.Graph:
    """Get the undirected mapping graph between the given prefixes.

    :param prefixes: A list of prefixes to use with :func:`pyobo.get_filtered_xrefs` to
        get xrefs.
    :returns: The undirected mapping graph containing mappings between entries in the
        given namespaces.
    """
    prefixes = set(prefixes)
    graph = nx.Graph()
    for prefix in sorted(prefixes):
        for mapping in pyobo.get_semantic_mappings(prefix):
            if mapping.object.prefix not in prefixes:
                continue
            graph.add_edge(mapping.subject, mapping.object)
    return graph


def _upgrade_set(values: Iterable[str] | None = None) -> set[str]:
    return set() if values is None else set(values)
