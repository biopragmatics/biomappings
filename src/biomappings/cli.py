# -*- coding: utf-8 -*-

"""The biomappings CLI."""

import click

from .graph import charts
from .summary import export
from .upload_ndex import ndex


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


main.add_command(export)
main.add_command(ndex)
main.add_command(charts)

if __name__ == '__main__':
    main()
