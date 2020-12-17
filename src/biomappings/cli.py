# -*- coding: utf-8 -*-

"""The biomappings CLI."""

import os
from collections import Counter

import click
import yaml


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


@main.command()
def export():
    """Create export data file."""
    from .resources import load_mappings, load_predictions, load_false_mappings

    here = os.path.abspath(os.path.dirname(__file__))
    x = os.path.join(here, os.pardir, os.pardir, 'docs', '_data', 'summary.yml')

    rv = {
        'positive': _get_counter(load_mappings()),
        'negative': _get_counter(load_false_mappings()),
        'predictions': _get_counter(load_predictions()),
    }
    with open(x, 'w') as file:
        yaml.safe_dump(rv, file, indent=2)


def _get_counter(mappings):
    counter = Counter()
    for mapping in mappings:
        source, target = mapping['source prefix'], mapping['target prefix']
        if source > target:
            source, target = target, source
        counter[source, target] += 1
    return [
        dict(source=source, target=target, count=count)
        for (source, target), count in counter.most_common()
    ]


if __name__ == '__main__':
    main()
