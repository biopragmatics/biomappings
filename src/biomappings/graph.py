# -*- coding: utf-8 -*-

"""Load Biomappings as a graph."""

import os
from collections import Counter
from operator import itemgetter
from typing import Iterable, List, Mapping, Optional, Sequence

import click
import networkx as nx
import yaml
from bioregistry.resolve_identifier import get_bioregistry_iri
from tqdm import tqdm

from biomappings.resources import load_false_mappings, load_mappings
from biomappings.utils import DATA, IMG, get_curie


def get_true_graph(
    include: Optional[Sequence[str]] = None, exclude: Optional[Sequence[str]] = None
) -> nx.Graph:
    """Get a graph of the true mappings."""
    return _graph_from_mappings(load_mappings(), include=include, exclude=exclude)


def get_false_graph(
    include: Optional[Sequence[str]] = None, exclude: Optional[Sequence[str]] = None
) -> nx.Graph:
    """Get a graph of the false mappings."""
    return _graph_from_mappings(load_false_mappings(), include=include, exclude=exclude)


def get_predictions_graph(
    include: Optional[Sequence[str]] = None, exclude: Optional[Sequence[str]] = None
) -> nx.Graph:
    """Get a graph of the predicted mappings."""
    return _graph_from_mappings(load_false_mappings(), include=include, exclude=exclude)


def _graph_from_mappings(
    mappings: Iterable[Mapping[str, str]],
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
) -> nx.Graph:
    graph = nx.Graph()

    if include is not None:
        include = set(include)
        print("only including", *include)
    if exclude is not None:
        exclude = set(exclude)
        print("excluding", *exclude)

    for mapping in mappings:
        relation = mapping["relation"]
        if exclude and (relation in exclude):
            continue
        if include and (relation not in include):
            continue

        source_curie = get_curie(mapping["source prefix"], mapping["source identifier"])
        graph.add_node(
            source_curie,
            prefix=mapping["source prefix"],
            identifier=mapping["source identifier"],
            name=mapping["source name"],
        )
        target_curie = get_curie(mapping["target prefix"], mapping["target identifier"])
        graph.add_node(
            target_curie,
            prefix=mapping["target prefix"],
            identifier=mapping["target identifier"],
            name=mapping["target name"],
        )
        graph.add_edge(
            source_curie,
            target_curie,
            relation=relation,
            provenance=mapping["source"],
            type=mapping["type"],
        )
    return graph


@click.command()
def charts():
    """Make charts."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    true_mappings = load_mappings()
    true_graph = _graph_from_mappings(true_mappings, include=["skos:exactMatch"])

    component_node_sizes, component_edge_sizes, component_densities, component_number_prefixes = (
        [],
        [],
        [],
        [],
    )
    prefix_list = []
    components_with_duplicate_prefixes = []
    incomplete_components = []
    n_duplicates = []
    for component in tqdm(
        nx.connected_components(true_graph), desc="Positive SCCs", unit="component"
    ):
        component = true_graph.subgraph(component)
        node_size = component.number_of_nodes()
        edge_size = component.number_of_edges()

        nodes_data = {
            curie: {
                "link": get_bioregistry_iri(data["prefix"], data["identifier"]),
                **data,
            }
            for curie, data in sorted(component.nodes(data=True), key=itemgetter(0))
        }

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
                        "source": {"curie": u, **nodes_data[u]},
                        "target": {"curie": v, **nodes_data[v]},
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

        prefixes = [true_graph.nodes[node]["prefix"] for node in component]
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
    # axes[0][2].set_yscale('log')
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
    print("saving to", path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.savefig(os.path.join(IMG, "components.svg"))
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    sns.countplot(
        y=prefix_list, ax=axes[0], order=[k for k, _ in Counter(prefix_list).most_common()]
    )
    axes[0].set_xscale("log")
    axes[0].set_title("Prefix Frequency")

    relations = [m["relation"] for m in true_mappings]
    sns.countplot(y=relations, ax=axes[1], order=[k for k, _ in Counter(relations).most_common()])
    axes[1].set_xscale("log")
    axes[1].set_title("Relation Frequency")

    path = os.path.join(IMG, "summary.png")
    print("saving to", path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.savefig(os.path.join(IMG, "summary.svg"))
    plt.close(fig)


def _countplot_list(data: List[int], ax):
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
