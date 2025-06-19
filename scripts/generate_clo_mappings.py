"""Generate mappings from CLO."""

import click
from more_click import verbose_option
from semra.sources.clo import get_clo_mappings

from biomappings.lexical import append_lexical_predictions
from biomappings.mapping_graph import get_filter_from_semra
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate mappings from CLO."""
    provenance = get_script_url(__file__)

    prefix = "clo"
    targets = [
        "mesh",
        "efo",
    ]

    clo_mappings = get_clo_mappings()
    custom_filter = get_filter_from_semra(clo_mappings)

    append_lexical_predictions(
        prefix,
        targets,
        provenance=provenance,
        custom_filter=custom_filter,
    )


if __name__ == "__main__":
    main()
