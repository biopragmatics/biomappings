"""Generate mappings."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(
        "hp",
        ["umls", "efo", "mesh"],
        filter_mutual_mappings=True,
        script=__file__,
    )
