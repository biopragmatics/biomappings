"""Generate mappings from MONDO."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("mondo", ["doid", "efo", "mesh"], script=__file__)
