"""The biomappings CLI."""

from __future__ import annotations

import itertools as itt
import os
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

import click

from .resources.export_sssom import export_sssom
from .summary import export
from .utils import DATA, IMG, get_git_hash

if TYPE_CHECKING:
    import matplotlib.axes


@click.group()
@click.version_option()
def main() -> None:
    """Run the biomappings CLI."""


main.add_command(export)
main.add_command(export_sssom)

if get_git_hash() is not None:
    resolver_base_option = click.option(
        "--resolver-base",
        help="A custom resolver base URL, instead of the Bioregistry.",
    )

    @main.command()
    @click.option("--predictions-path", type=Path, help="A predictions TSV file path")
    @click.option("--positives-path", type=Path, help="A positives curation TSV file path")
    @click.option("--negatives-path", type=Path, help="A negatives curation TSV file path")
    @click.option("--unsure-path", type=Path, help="An unsure curation TSV file path")
    @resolver_base_option
    def web(
        predictions_path: Path,
        positives_path: Path,
        negatives_path: Path,
        unsure_path: Path,
        resolver_base: str | None,
    ) -> None:
        """Run the biomappings web app."""
        import webbrowser

        from more_click import run_app

        from .wsgi import get_app

        app = get_app(
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
            resolver_base=resolver_base,
        )

        webbrowser.open_new_tab("http://localhost:5000")

        run_app(app, with_gunicorn=False)

    @main.command()
    @click.option("--path", required=True, type=Path, help="A predictions TSV file path")
    @resolver_base_option
    def curate(
        path: Path,
        resolver_base: str | None,
    ) -> None:
        """Run a target curation web app."""
        from curies import Reference
        from more_click import run_app

        from .resources import _load_table
        from .wsgi import get_app

        target_references: list[Reference] = []
        for mapping in _load_table(path):
            target_references.append(mapping.subject)
            target_references.append(mapping.object)
        app = get_app(target_references=target_references, resolver_base=resolver_base)
        run_app(app, with_gunicorn=False)

else:

    @main.command()
    def web() -> None:
        """Show an error for the web interface."""
        click.secho(
            "You are not running biomappings from a development installation.\n"
            "Please run the following to install in development mode:\n"
            "  $ git clone https://github.com/biomappings/biomappings.git\n"
            "  $ cd biomappings\n"
            "  $ pip install -e .",
            fg="red",
        )


@main.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Run all update functions."""
    click.secho("Building general exports", fg="green")
    ctx.invoke(export)
    click.secho("Building SSSOM export", fg="green")
    ctx.invoke(export_sssom)
    click.secho("Generating charts", fg="green")
    ctx.invoke(charts)


@main.command()
def lint() -> None:
    """Sort files and remove duplicates."""
    from . import resources

    resources.lint_true_mappings()
    resources.lint_false_mappings()
    resources.lint_unsure_mappings()
    resources.lint_predictions()


@main.command()
@click.option("--username", help="NDEx username, also looks in pystow configuration")
@click.option("--password", help="NDEx password, also looks in pystow configuration")
def ndex(username: str | None, password: str | None) -> None:
    """Upload to NDEx, see https://www.ndexbio.org/viewer/networks/402d1fd6-49d6-11eb-9e72-0ac135e8bacf."""
    from sssom_pydantic import MappingSet
    from sssom_pydantic.contrib.ndex import update_ndex

    from biomappings import load_mappings
    from biomappings.utils import BIOMAPPINGS_NDEX_UUID, get_git_hash

    mappings = load_mappings()
    metadata = MappingSet(
        mapping_set_id="https://w3id.org/biopragmatics/biomappings/sssom/biomappings.sssom.tsv",
        mapping_set_title="Biomappings",
        mapping_set_description="Manually curated semantic mappings (e.g., skos:exactMatch) between biological entities",
        license="CC0",
        mapping_set_version=get_git_hash(),
    )
    update_ndex(
        uuid=BIOMAPPINGS_NDEX_UUID,
        mappings=mappings,
        metadata=metadata,
        username=username,
        password=password,
    )
    click.echo(f"Uploaded to https://bioregistry.io/ndex:{BIOMAPPINGS_NDEX_UUID}")


@main.command()
def charts() -> None:
    """Make charts."""
    import matplotlib.pyplot as plt
    import networkx as nx
    import seaborn as sns
    import yaml
    from curies.vocabulary import exact_match
    from tqdm import tqdm

    from .resources import _graph_from_mappings, load_false_mappings, load_mappings

    true_mappings = load_mappings()
    true_graph = _graph_from_mappings(true_mappings, include=[exact_match], strata="correct")
    for u, v in true_graph.edges():
        true_graph.edges[u, v]["correct"] = True
    false_mappings = load_false_mappings()
    false_graph = _graph_from_mappings(false_mappings, include=[exact_match], strata="incorrect")
    for u, v in false_graph.edges():
        false_graph.edges[u, v]["correct"] = False

    component_node_sizes = []
    component_edge_sizes = []
    component_densities = []
    component_number_prefixes = []
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
                "name": getattr(reference, "name", None),
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
    main()
