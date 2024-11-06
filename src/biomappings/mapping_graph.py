"""Functions for working with the mapping graph."""

import itertools as itt
from collections import defaultdict
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

import networkx as nx
import pyobo

from biomappings.utils import CMapping

if TYPE_CHECKING:
    import semra

__all__ = [
    "get_custom_filter",
    "get_filter_from_semra",
    "mutual_mapping_graph",
]


def get_filter_from_semra(mappings: list["semra.Mapping"]) -> CMapping:
    """Get a custom filter dictionary from a set of SeMRA mappings."""
    rv: defaultdict[str, defaultdict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    for mapping in mappings:
        rv[mapping.s.prefix][mapping.o.prefix][mapping.s.identifier] = mapping.o.identifier
    return rv


def get_custom_filter(prefix: str, targets: Iterable[str]) -> CMapping:
    """Get a custom filter dictionary induced over the mutual mapping graph with all target prefixes.

    :param prefix: The source prefix
    :param targets: All potential target prefixes
    :returns: A filter 3-dictionary of source prefix to target prefix to source identifier to target identifier
    """
    graph = mutual_mapping_graph([prefix, *targets])
    rv: defaultdict[str, dict[str, str]] = defaultdict(dict)
    for p, identifier in graph:
        if p != prefix:
            continue
        for xref_prefix, xref_identifier in nx.single_source_shortest_path(graph, (p, identifier)):
            rv[xref_prefix][identifier] = xref_identifier
    return {prefix: dict(rv)}


def mutual_mapping_graph(
    prefixes: Iterable[str],
    skip_sources: Optional[Iterable[str]] = None,
    skip_targets: Optional[Iterable[str]] = None,
) -> nx.Graph:
    """Get the undirected mapping graph between the given prefixes.

    :param prefixes: A list of prefixes to use with :func:`pyobo.get_filtered_xrefs` to get xrefs.
    :param skip_sources: An optional list of prefixes to skip as the source for xrefs
    :param skip_targets: An optional list of prefixes to skip as the target for xrefs
    :return: The undirected mapping graph containing mappings between entries in the given namespaces.
    """
    prefixes = sorted(prefixes)
    skip_sources = set() if skip_sources is None else set(skip_sources)
    skip_targets = set() if skip_targets is None else set(skip_targets)
    graph = nx.Graph()
    for source, target in itt.product(prefixes, repeat=2):
        if source == target or source in skip_sources or target in skip_targets:
            continue
        for source_id, target_id in pyobo.get_filtered_xrefs(source, target).items():
            graph.add_edge((source, source_id), (target, target_id))
    return graph
