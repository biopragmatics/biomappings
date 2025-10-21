"""Generate mappings from BTO."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("bto", "cl", script=__file__)
