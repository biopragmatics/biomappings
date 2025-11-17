"""Generate mappings from UBERON."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("uberon", ["bto", "mesh", "caro"], script=__file__)
