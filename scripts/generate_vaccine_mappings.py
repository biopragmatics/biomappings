"""Generate vaccine mappings."""

import click

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate vaccine mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("cvx", ["mesh", "cpt"], provenance=provenance)
    append_gilda_predictions("cpt", ["mesh"], provenance=provenance)


if __name__ == "__main__":
    main()
