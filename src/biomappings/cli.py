"""The biomappings CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from more_click import run_app

from .graph import charts
from .resources.export_sssom import sssom
from .summary import export
from .utils import get_git_hash


@click.group()
@click.version_option()
def main() -> None:
    """Run the biomappings CLI."""


if get_git_hash() is not None:
    resolver_base_option = click.option(
        "--resolver-base",
        help="A custom resolver base URL, instead of the Bioregistry.",
    )

    @main.command()
    @click.option("--predictions-path", type=click.Path(), help="A predictions TSV file path")
    @click.option("--positives-path", type=click.Path(), help="A positives curation TSV file path")
    @click.option("--negatives-path", type=click.Path(), help="A negatives curation TSV file path")
    @click.option("--unsure-path", type=click.Path(), help="An unsure curation TSV file path")
    @resolver_base_option
    def web(
        predictions_path: Path,
        positives_path: Path,
        negatives_path: Path,
        unsure_path: Path,
        resolver_base: str | None,
    ) -> None:
        """Run the biomappings web app."""
        from .wsgi import get_app

        app = get_app(
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
            resolver_base=resolver_base,
        )
        run_app(app, with_gunicorn=False)

    @main.command()
    @click.option("--path", required=True, type=click.Path(), help="A predictions TSV file path")
    @resolver_base_option
    def curate(
        path: Path,
        resolver_base: str | None,
    ) -> None:
        """Run a target curation web app."""
        from curies import Reference

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
    ctx.invoke(sssom)
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
@click.argument("prefixes", nargs=-1)
def prune(prefixes: list[str]) -> None:
    """Prune inferred mappings between the given prefixes from the predictions."""
    from .lexical import get_mutual_mapping_filter
    from .resources import filter_predictions

    if len(prefixes) < 2:
        click.secho("Must give at least 2 prefixes", fg="red")
        sys.exit(0)

    cf = get_mutual_mapping_filter(prefixes[0], prefixes[1:])
    filter_predictions(cf)


@main.command()
def remove_curated() -> None:
    """Remove curated mappings from the predicted mappings, use this if they get out of sync."""
    from .resources import filter_predictions, get_curated_filter

    filter_predictions(get_curated_filter())


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


main.add_command(export)
main.add_command(charts)
main.add_command(sssom)

if __name__ == "__main__":
    main()
