"""Generate mappings from ChEBI."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("chebi", ["mesh", "efo"], script=__file__)
