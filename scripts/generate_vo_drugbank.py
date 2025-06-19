"""Generate mappings using from VO."""

from biomappings.lexical import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli(__file__, "vo", ["drugbank", "umls", "ncit"])
