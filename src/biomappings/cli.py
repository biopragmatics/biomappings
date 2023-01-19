# -*- coding: utf-8 -*-

"""The biomappings CLI."""

import click
from more_click import make_web_command

from .export_sssom import sssom
from .graph import charts
from .summary import export
from .upload_ndex import ndex
from .utils import get_git_hash


@click.group()
@click.version_option()
def main():
    """Run the biomappings CLI."""


if get_git_hash() is not None:
    # This command is called "web" by default
    main.add_command(make_web_command("biomappings.wsgi:app"))
else:

    @main.command()
    def web():
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
        lint_false_mappings,
        lint_predictions,
        lint_true_mappings,
        lint_unsure_mappings,
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


@main.command()
def remove_curated():
    """Remove curated mappings from the predicted mappings, use this if they get out of sync."""
    from .resources import filter_predictions, get_curated_filter

    filter_predictions(get_curated_filter())


main.add_command(export)
main.add_command(ndex)
main.add_command(charts)
main.add_command(sssom)

if __name__ == "__main__":
    main()
