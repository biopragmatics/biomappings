"""Generate mappings from DOID."""

from biomappings.lexical import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(
        __file__,
        "doid",
        ["umls", "efo", "mesh", "mondo", "ido", "ordo", "cido"],
        filter_mutual_mappings=True,
    )
