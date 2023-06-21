"""Generate mappings using Gilda from UBERON to BTO."""

import click

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate UBERON-BTO mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("uberon", "bto", provenance=provenance)


if __name__ == "__main__":
    main()
