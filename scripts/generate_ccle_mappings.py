"""Generate mappings to Gilda from given PyOBO prefixes."""

import click
from more_click import verbose_option

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.mapping_graph import get_custom_filter
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate CCLE mappings."""
    provenance = get_script_url(__file__)

    prefix = "ccle.cell"
    targets = ["depmap", "efo", "cellosaurus", "cl", "bto"]

    custom_filter = get_custom_filter(prefix, targets)
    append_gilda_predictions(
        prefix,
        targets,
        provenance=provenance,
        relation="skos:exactMatch",
        custom_filter=custom_filter,
        identifiers_are_names=True,
    )


if __name__ == "__main__":
    main()
