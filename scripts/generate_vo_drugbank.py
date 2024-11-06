"""Generate mappings using Gilda from VO to DrugBank."""

import click

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate VO-DrugBank mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("vo", "drugbank", provenance=provenance)


if __name__ == "__main__":
    main()
