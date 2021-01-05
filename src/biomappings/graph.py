# -*- coding: utf-8 -*-

"""Load Biomappings as a graph."""

import os
from typing import Iterable, Mapping

import click
import networkx as nx

from biomappings.resources import load_false_mappings, load_mappings
from biomappings.utils import IMG, MiriamValidator


def get_true_graph() -> nx.Graph:
    """Get a graph of the true mappings."""
    return _graph_from_mappings(load_mappings())


def get_false_graph() -> nx.Graph:
    """Get a graph of the false mappings."""
    return _graph_from_mappings(load_false_mappings())


def get_predictions_graph() -> nx.Graph:
    """Get a graph of the predicted mappings."""
    return _graph_from_mappings(load_false_mappings())


def _graph_from_mappings(mappings: Iterable[Mapping[str, str]]) -> nx.Graph:
    v = MiriamValidator()
    graph = nx.Graph()
    for mapping in mappings:
        source_curie = v.get_curie(mapping['source prefix'], mapping['source identifier'])
        graph.add_node(
            source_curie,
            prefix=mapping['source prefix'],
            identifier=mapping['source identifier'],
            name=mapping['source name'],
        )
        target_curie = v.get_curie(mapping['target prefix'], mapping['target identifier'])
        graph.add_node(
            target_curie,
            prefix=mapping['target prefix'],
            identifier=mapping['target identifier'],
            name=mapping['target name'],
        )
        graph.add_edge(
            source_curie,
            target_curie,
            provenance=mapping['source'],
            type=mapping['type'],
        )
    return graph


@click.command()
def charts():
    """Make charts."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    graph = get_true_graph()
    node_sizes, edge_sizes, densities, n_prefixes = [], [], [], []
    n_duplicates = []
    for c in nx.connected_components(graph):
        node_sizes.append(len(c))
        sg = graph.subgraph(c)
        edge_sizes.append(sg.number_of_edges())
        densities.append(nx.density(sg))
        prefixes = [
            graph.nodes[node]['prefix']
            for node in c
        ]
        unique_prefixes = len(set(prefixes))
        n_prefixes.append(unique_prefixes)
        n_duplicates.append(len(prefixes) - unique_prefixes)

    fig, axes = plt.subplots(2, 3, figsize=(10, 6.5))

    sns.histplot(node_sizes, ax=axes[0][0])
    axes[0][0].set_yscale('log')
    axes[0][0].set_title('Component Node Sizes')

    sns.histplot(edge_sizes, ax=axes[0][1])
    axes[0][1].set_yscale('log')
    axes[0][1].set_title('Component Edge Sizes')
    axes[0][1].set_ylabel('')

    sns.kdeplot(densities, ax=axes[0][2], log_scale=True)
    # axes[2].set_xlim([0.0, 1.0])
    axes[0][2].set_title('Component Densities')
    axes[0][2].set_ylabel('')

    sns.histplot(n_prefixes, ax=axes[1][0])
    axes[1][0].set_title('Number Prefixes')

    # has duplicate prefix in component

    sns.histplot(n_duplicates, ax=axes[1][1])
    axes[1][1].set_yscale('log')
    axes[0][2].set_ylabel('')
    axes[1][1].set_title('Number Duplicate Prefixes')

    axes[1][2].axis('off')

    path = os.path.join(IMG, 'components.png')
    print('saving to', path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    charts()
