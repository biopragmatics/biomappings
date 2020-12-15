# -*- coding: utf-8 -*-

"""The biomappings CLI."""

import click


@click.group()
def main():
    """Run the biomappings CLI."""


@main.command()
def web():
    """Run the biomappings web curation interface."""
    from .wsgi import app
    app.run()


if __name__ == '__main__':
    main()
