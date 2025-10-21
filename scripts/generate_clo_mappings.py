"""Generate mappings from CLO."""

import click
from more_click import verbose_option

from biomappings import append_lexical_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main() -> None:
    """Generate mappings from CLO."""
    provenance = get_script_url(__file__)

    prefix = "clo"
    targets = [
        "mesh",
        "efo",
    ]

    append_lexical_predictions(
        prefix,
        targets,
        provenance=provenance,
    )


if __name__ == "__main__":
    main()
