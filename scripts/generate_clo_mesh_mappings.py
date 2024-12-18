"""Generate mappings to CLO from to MeSH."""

import click
from more_click import verbose_option
from semra.sources.clo import get_clo_mappings

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.mapping_graph import get_filter_from_semra
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate CLO-MeSH mappings."""
    provenance = get_script_url(__file__)

    prefix = "clo"
    targets = [
        "mesh",
        "efo",
    ]

    clo_mappings = get_clo_mappings()
    custom_filter = get_filter_from_semra(clo_mappings)

    append_gilda_predictions(
        prefix,
        targets,
        provenance=provenance,
        custom_filter=custom_filter,
    )


if __name__ == "__main__":
    main()
