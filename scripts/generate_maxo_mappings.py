"""Generate mappings from MAxO."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("maxo", "mesh", script=__file__)
