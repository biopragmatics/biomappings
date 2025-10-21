"""Generate mappings using from VO."""

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    lexical_prediction_cli("vo", ["drugbank", "umls", "ncit"], script=__file__)
