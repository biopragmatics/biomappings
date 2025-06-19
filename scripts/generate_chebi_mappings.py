"""Generate mappings from ChEBI."""

import click
from more_click import verbose_option

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main() -> None:
    """Generate ChEBI mappings."""
    append_gilda_predictions(
        "chebi",
        ["mesh", "efo"],
        provenance=get_script_url(__file__),
    )


if __name__ == "__main__":
    main()
