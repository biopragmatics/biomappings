"""Generate mappings to Gilda from given PyOBO prefixes."""

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.utils import get_script_url


def main():
    """Make species specific groundings from reactome to wikipathways."""
    target_prefixes = ["reactome", "wikipathways", "pw"]
    provenance = get_script_url(__file__)
    for prefix in ["reactome", "wikipathways"]:
        append_gilda_predictions(
            prefix, target_prefixes, provenance=provenance, relation="speciesSpecific"
        )


if __name__ == "__main__":
    main()
