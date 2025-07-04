"""The biomappings CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from more_click import run_app

from .graph import charts
from .resources.export_sssom import sssom
from .summary import export
from .upload_ndex import ndex
from .utils import get_git_hash


@click.group()
@click.version_option()
def main() -> None:
    """Run the biomappings CLI."""


if get_git_hash() is not None:

    @main.command()
    @click.option("--predictions-path", type=click.Path(), help="A predictions TSV file path")
    @click.option("--positives-path", type=click.Path(), help="A positives curation TSV file path")
    @click.option("--negatives-path", type=click.Path(), help="A negatives curation TSV file path")
    @click.option("--unsure-path", type=click.Path(), help="An unsure curation TSV file path")
    def web(
        predictions_path: Path,
        positives_path: Path,
        negatives_path: Path,
        unsure_path: Path,
    ) -> None:
        """Run the biomappings web app."""
        from .wsgi import get_app

        app = get_app(
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
        )
        run_app(app, with_gunicorn=False)

    @main.command()
    @click.option("--path", required=True, type=click.Path(), help="A predictions TSV file path")
    def curate(path: Path) -> None:
        """Run a target curation web app."""
        from curies import NamableReference

        from .resources import _load_table
        from .wsgi import get_app

        target_references: list[NamableReference] = []
        for mapping in _load_table(path, standardize=True):
            target_references.append(mapping.subject)
            target_references.append(mapping.object)
        app = get_app(target_references=target_references)
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

    resources.lint_true_mappings(standardize=True)
    resources.lint_false_mappings(standardize=True)
    resources.lint_unsure_mappings(standardize=True)
    resources.lint_predictions(standardize=True)


@main.command()
@click.argument("prefixes", nargs=-1)
def prune(prefixes: list[str]) -> None:
    """Prune inferred mappings between the given prefixes from the predictions."""
    from .mapping_graph import get_mutual_mapping_filter
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


main.add_command(export)
main.add_command(ndex)
main.add_command(charts)
main.add_command(sssom)

if __name__ == "__main__":
    main()
