"""Generate mappings from Reactome, WikiPathways, and Pathway Ontology."""

from biomappings import append_lexical_predictions
from biomappings.utils import get_script_url


def main() -> None:
    """Make species specific groundings from reactome to wikipathways."""
    target_prefixes = ["reactome", "wikipathways", "pw"]
    provenance = get_script_url(__file__)
    for prefix in ["reactome", "wikipathways"]:
        append_lexical_predictions(
            prefix, target_prefixes, mapping_tool=provenance, relation="speciesSpecific"
        )


if __name__ == "__main__":
    main()
