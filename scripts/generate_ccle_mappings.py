# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

import itertools as itt
from collections import defaultdict
from typing import Iterable, Mapping, Optional

import click
import networkx as nx
import pyobo
from more_click import verbose_option

from biomappings.gilda_utils import CMapping, append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate CCLE mappings."""
    provenance = get_script_url(__file__)

    prefix = "ccle.cell"
    targets = ["depmap", "efo", "cellosaurus", "cl", "bto"]

    custom_filter = get_custom_filter(prefix, targets)
    append_gilda_predictions(
        prefix,
        targets,
        provenance=provenance,
        relation="skos:exactMatch",
        custom_filter=custom_filter,
        identifiers_are_names=True,
    )


def get_custom_filter(prefix: str, targets: Iterable[str]) -> Mapping[str, Mapping[str, Mapping[str, str]]]:
    """Get a custom filter dictionary induced over the mutual mapping graph with all target prefixes.

    :param prefix: The source prefix
    :param targets: All potential target prefixes
    :returns: A filter 3-dictionary of source prefix to target prefix to source identifier to target identifier
    """
    graph = mutual_mapping_graph([prefix, *targets])
    rv = defaultdict(dict)
    for p, identifier in graph:
        if p != prefix:
            continue
        for xref_prefix, xref_identifier in nx.single_source_shortest_path(graph, (p, identifier)):
            rv[xref_prefix][identifier] = xref_identifier
    return {prefix: dict(rv)}


def mutual_mapping_graph(
    prefixes: Iterable[str],
    skip_sources: Optional[Iterable[str]] = None,
    skip_targets: Optional[Iterable[str]] = None
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


def ccle_custom_filter() -> CMapping:
    """Get custom CCLE->X mappings."""
    ccle_depmap = pyobo.get_filtered_xrefs("ccle", "depmap")
    ccle_cellosaurus = _cdict(
        (ccle_id, pyobo.get_xref("depmap", depmap_id, "cellosaurus"))
        for ccle_id, depmap_id in ccle_depmap.items()
    )
    ccle_efo = _cdict(
        (ccle_id, pyobo.get_xref("cellosaurus", cvcl_id, "efo"))
        for ccle_id, cvcl_id in ccle_cellosaurus.items()
    )
    ccle_bto = _cdict(
        (ccle_id, pyobo.get_xref("cellosaurus", cvcl_id, "bto"))
        for ccle_id, cvcl_id in ccle_cellosaurus.items()
    )
    return {
        "ccle": {
            "depmap": ccle_depmap,
            "cellosaurus": ccle_cellosaurus,
            "efo": ccle_efo,
            "ccle_bto": ccle_bto,
        }
    }


def _cdict(x):
    return {k: v for k, v in x if v}


if __name__ == "__main__":
    main()
