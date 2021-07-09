# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


def main():
    """Make species specific groundings from reactome to wikipathways."""
    to = ["reactome", "wikipathways", "pw"]
    fname = get_script_url(__file__)
    for prefix in ["reactome", "wikipathways"]:
        append_gilda_predictions(prefix, to, provenance=fname, rel="speciesSpecific")


if __name__ == "__main__":
    main()
