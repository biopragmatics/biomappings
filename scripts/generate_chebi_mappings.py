"""Generate mappings from ChEBI."""

from biomappings.lexical import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(__file__, "chebi", ["mesh", "efo"])
