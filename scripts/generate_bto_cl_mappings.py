"""Generate mappings using Gilda from BTO."""

import click

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate BTO mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("bto", "cl", provenance=provenance)


if __name__ == "__main__":
    main()
