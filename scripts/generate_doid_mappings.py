"""Generate mappings to Gilda from given PyOBO prefixes."""

import click
from more_click import verbose_option

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.mapping_graph import get_custom_filter
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate DOID mappings."""
    provenance = get_script_url(__file__)

    prefix = "doid"
    targets = [
        "umls",
        "efo",
        "mesh",
        # MONDO and IDO both have the issue of
        # mismatch of regex/banana
        # "mondo",
        # "ido",
        # ORDO and CIDO can't be parsed
        # "ordo",
        # "cido"
    ]

    custom_filter = get_custom_filter(prefix, targets)
    append_gilda_predictions(
        prefix,
        targets,
        provenance=provenance,
        relation="skos:exactMatch",
        custom_filter=custom_filter,
    )


if __name__ == "__main__":
    main()
