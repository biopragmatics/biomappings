"""Generate mappings from CLO."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("clo", ["mesh", "efo"], script=__file__)
