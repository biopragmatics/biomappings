"""Generate mappings from CCLE."""

from biomappings.lexical import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(
        __file__,
        "ccle.cell",
        ["depmap", "efo", "cellosaurus", "cl", "bto"],
        filter_mutual_mappings=True,
        identifiers_are_names=True,
    )
