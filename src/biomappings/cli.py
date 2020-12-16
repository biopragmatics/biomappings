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
    from .utils import get_git_hash
    if get_git_hash() is None:
        click.secho(
            'You are not running biomappings from a development installation.\n'
            'Please run the following to install in development mode:\n'
            '  $ git clone https://github.com/biomappings/biomappings.git\n'
            '  $ cd biomappings\n'
            '  $ pip install -e .',
            fg='red',
        )
    else:
        app.run()


if __name__ == '__main__':
    main()
