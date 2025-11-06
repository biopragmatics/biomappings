"""Generate mappings from DOID."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(
        "doid",
        ["umls", "efo", "mesh", "mondo", "ido", "ordo", "cido"],
        filter_mutual_mappings=True,
        script=__file__,
    )
