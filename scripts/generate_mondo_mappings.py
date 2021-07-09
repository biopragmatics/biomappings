# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

import click
from more_click import verbose_option

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate MONDO mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions(
        "mondo", ["doid", "efo"], provenance=provenance, relation="skos:exactMatch"
    )


if __name__ == "__main__":
    main()
