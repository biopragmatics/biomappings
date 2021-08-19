# -*- coding: utf-8 -*-

"""The biomappings CLI."""

import click
from more_click import verbose_option

from .export_sssom import sssom
from .graph import charts
from .summary import export
from .upload_ndex import ndex


@click.group()
def main():
    """Run the biomappings CLI."""


@main.command()
@verbose_option
def web():
    """Run the biomappings web curation interface."""
    from .wsgi import app
    from .utils import get_git_hash

    if get_git_hash() is None:
        click.secho(
            "You are not running biomappings from a development installation.\n"
            "Please run the following to install in development mode:\n"
            "  $ git clone https://github.com/biomappings/biomappings.git\n"
            "  $ cd biomappings\n"
            "  $ pip install -e .",
            fg="red",
        )
    else:
        app.run()


@main.command()
@click.pass_context
def update(ctx: click.Context):
    """Run all update functions."""
    click.secho("Building general exports", fg="green")
    ctx.invoke(export)
    click.secho("Building SSSOM export", fg="green")
    ctx.invoke(sssom)
    click.secho("Generating charts", fg="green")
    ctx.invoke(charts)
    click.secho("Uploading to NDEx", fg="green")
    ctx.invoke(ndex)


@main.command()
def lint():
    """Sort files and remove duplicates."""
    from .resources import (
        lint_predictions,
        lint_true_mappings,
        lint_unsure_mappings,
        lint_false_mappings,
    )

    lint_true_mappings()
    lint_false_mappings()
    lint_unsure_mappings()
    lint_predictions()


@main.command()
@click.argument("prefixes", nargs=-1)
def prune(prefixes):
    """Prune inferred mappings between the given prefixes from the predictions."""
    from .mapping_graph import get_custom_filter
    from .resources import filter_predictions

    cf = get_custom_filter(prefixes[0], prefixes[1:])
    filter_predictions(cf)


main.add_command(export)
main.add_command(ndex)
main.add_command(charts)

if __name__ == "__main__":
    main()
