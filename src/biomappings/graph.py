"""Load Biomappings as a graph."""

from __future__ import annotations

import itertools as itt
import logging
import os
from collections import Counter
from collections.abc import Collection, Iterable, Sequence
from typing import TYPE_CHECKING

import click
import networkx as nx
import yaml
from curies import Reference
from tqdm import tqdm

from biomappings.resources import (
    SemanticMapping,
    load_false_mappings,
    load_mappings,
    load_predictions,
)
from biomappings.utils import DATA, EXACT_MATCH, IMG

if TYPE_CHECKING:
    import matplotlib.axes

__all__ = [
    "get_false_graph",
    "get_predictions_graph",
    "get_true_graph",
]

logger = logging.getLogger(__name__)


def get_true_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the true mappings."""
    return _graph_from_mappings(load_mappings(), strata="correct", include=include, exclude=exclude)


def get_false_graph(
    include: Sequence[Reference] | None = None,
    exclude: Sequence[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the false mappings."""
    return _graph_from_mappings(
        load_false_mappings(), strata="incorrect", include=include, exclude=exclude
    )


def get_predictions_graph(
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> nx.Graph:
    """Get a graph of the predicted mappings."""
    return _graph_from_mappings(
        load_predictions(), strata="predicted", include=include, exclude=exclude
    )


def _graph_from_mappings(
    mappings: Iterable[SemanticMapping],
    strata: str,
    include: Collection[Reference] | None = None,
    exclude: Collection[Reference] | None = None,
) -> nx.Graph:
    graph = nx.Graph()

    if include is not None:
        include = set(include)
        logger.info("only including %s", include)
    if exclude is not None:
        exclude = set(exclude)
        logger.info("excluding %s", exclude)

    for mapping in mappings:
        if exclude and (mapping.predicate in exclude):
            continue
        if include and (mapping.predicate not in include):
            continue
        graph.add_edge(
            mapping.subject,
            mapping.object,
            relation=mapping.predicate.curie,
            provenance=mapping.author.name if mapping.author else None,
            type=mapping.mapping_justification.curie,
            strata=strata,
        )
    return graph


@click.command()
def charts() -> None:
    """Make charts."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    true_mappings = load_mappings()
    true_graph = _graph_from_mappings(true_mappings, include=[EXACT_MATCH], strata="correct")
    for u, v in true_graph.edges():
        true_graph.edges[u, v]["correct"] = True
    false_mappings = load_false_mappings()
    false_graph = _graph_from_mappings(false_mappings, include=[EXACT_MATCH], strata="incorrect")
    for u, v in false_graph.edges():
        false_graph.edges[u, v]["correct"] = False

    component_node_sizes, component_edge_sizes, component_densities, component_number_prefixes = (
        [],
        [],
        [],
        [],
    )
    prefix_list = []
    components_with_duplicate_prefixes = []
    incomplete_components = []
    unstable_components = []
    n_duplicates = []
    for component in tqdm(
        nx.connected_components(true_graph), desc="Positive SCCs", unit="component", unit_scale=True
    ):
        component = true_graph.subgraph(component)
        node_size = component.number_of_nodes()
        edge_size = component.number_of_edges()

        nodes_data = {
            reference.curie: {
                "link": f"https://bioregistry.io/{reference.curie}",
                "prefix": str(reference.prefix),
                "identifier": reference.identifier,
                "name": reference.name,
            }
            for reference in component.nodes
        }

        unstable_edges = [
            (u, v, false_graph[u, v])
            for u, v in itt.combinations(component, 2)
            if false_graph.has_edge(u, v)
        ]
        if unstable_edges:
            unstable_components.append({"nodes": nodes_data, "unstable_edges": unstable_edges})

        component_node_sizes.append(node_size)
        component_edge_sizes.append(edge_size)
        if node_size > 2:
            component_densities.append(nx.density(component))
        if node_size > 2 and edge_size < (node_size * (node_size - 1) / 2):
            incomplete_components_edges = []
            for u, v in sorted(nx.complement(component.copy()).edges()):
                if u > v:
                    u, v = v, u
                incomplete_components_edges.append(
                    {
                        "source": {"curie": u.curie, **nodes_data[u.curie]},
                        "target": {"curie": v.curie, **nodes_data[v.curie]},
                    }
                )
            incomplete_components_edges = sorted(
                incomplete_components_edges, key=lambda d: d["source"]["curie"]
            )
            incomplete_components.append(
                {
                    "nodes": nodes_data,
                    "edges": incomplete_components_edges,
                }
            )

        prefixes = [node.prefix for node in component]
        prefix_list.extend(prefixes)
        unique_prefixes = len(set(prefixes))
        component_number_prefixes.append(unique_prefixes)
        _n_duplicates = len(prefixes) - unique_prefixes
        n_duplicates.append(_n_duplicates)
        if _n_duplicates:
            components_with_duplicate_prefixes.append(nodes_data)

    with open(os.path.join(DATA, "incomplete_components.yml"), "w") as file:
        yaml.safe_dump(incomplete_components, file)
    with open(os.path.join(DATA, "components_with_duplicate_prefixes.yml"), "w") as file:
        yaml.safe_dump(components_with_duplicate_prefixes, file)
    with open(os.path.join(DATA, "unstable_components.yml"), "w") as file:
        yaml.safe_dump(unstable_components, file)

    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.5))

    _countplot_list(component_node_sizes, ax=axes[0][0])
    axes[0][0].set_yscale("log")
    axes[0][0].set_title("Size (Nodes)")

    _countplot_list(component_edge_sizes, ax=axes[0][1])
    axes[0][1].set_yscale("log")
    axes[0][1].set_title("Size (Edges)")
    axes[0][1].set_ylabel("")

    sns.kdeplot(component_densities, ax=axes[0][2])
    axes[0][2].set_xlim([0.0, 1.0])
    axes[0][2].set_title("Density ($|V| > 2$)")
    axes[0][2].set_ylabel("")

    _countplot_list(component_number_prefixes, ax=axes[1][0])
    axes[1][0].set_title("Number Prefixes")
    axes[1][0].set_yscale("log")
    # has duplicate prefix in component

    _countplot_list(n_duplicates, ax=axes[1][1])
    axes[1][1].set_yscale("log")
    axes[0][2].set_ylabel("")
    axes[1][1].set_title("Number Duplicate Prefixes")

    axes[1][2].axis("off")

    path = os.path.join(IMG, "components.png")
    click.echo(f"saving to {path}")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.savefig(os.path.join(IMG, "components.svg"))
    plt.close(fig)

    prefix_counter = Counter(prefix_list)
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 7))
    sns.countplot(y=prefix_list, ax=axes[0], order=[k for k, _ in prefix_counter.most_common()])
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Count")
    axes[0].set_title(f"Prefixes ({len(prefix_counter)})")

    relations = [m.predicate.curie for m in true_mappings]
    relation_counter = Counter(relations)
    sns.countplot(y=relations, ax=axes[1], order=[k for k, _ in relation_counter.most_common()])
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Count")
    axes[1].set_title(f"Relations ({len(relation_counter)})")

    path = os.path.join(IMG, "summary.png")
    click.echo(f"saving to {path}")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.savefig(os.path.join(IMG, "summary.svg"))
    plt.close(fig)


def _countplot_list(data: list[int], ax: matplotlib.axes.Axes) -> None:
    import pandas as pd
    import seaborn as sns

    counter = Counter(data)
    for size in range(min(counter), max(counter)):
        if size not in counter:
            counter[size] = 0
    df = pd.DataFrame(counter.items(), columns=["size", "count"]).sort_values("size").reset_index()
    sns.barplot(data=df, x="size", y="count", ax=ax)


if __name__ == "__main__":
    charts()
