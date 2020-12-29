# -*- coding: utf-8 -*-

"""Load Biomappings as a graph."""

import os

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns

from biomappings.resources import load_mappings
from biomappings.utils import IMG, MiriamValidator


def get_positive_graph() -> nx.Graph:
    """Get a graph of the positive mappings."""
    v = MiriamValidator()
    graph = nx.Graph()
    for mapping in load_mappings():
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


def _main():
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    graph = get_positive_graph()

    sizes = [len(c) for c in nx.connected_components(graph)]
    sns.histplot(sizes, ax=axes[0])
    axes[0].set_yscale('log')
    axes[0].set_title('Component Node Sizes')

    sizes = [graph.subgraph(c).number_of_edges() for c in nx.connected_components(graph)]
    sns.histplot(sizes, ax=axes[1])
    axes[1].set_yscale('log')
    axes[1].set_title('Component Edge Sizes')
    axes[1].set_ylabel('')

    densities = [nx.density(graph.subgraph(c)) for c in nx.connected_components(graph)]
    sns.histplot(densities, ax=axes[2], kde=True)
    axes[2].set_xlim([0.0, 1.0])
    axes[2].set_title('Component Densities')
    axes[2].set_ylabel('')

    path = os.path.join(IMG, 'components.png')
    print('saving to', path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    _main()
