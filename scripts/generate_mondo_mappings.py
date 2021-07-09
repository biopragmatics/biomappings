# -*- coding: utf-8 -*-

import click
from more_click import verbose_option

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    fname = get_script_url(__file__)
    append_gilda_predictions("mondo", ["doid", "efo"], provenance=fname, rel="skos:exactMatch")


if __name__ == "__main__":
    main()
