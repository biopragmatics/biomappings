"""Generate vaccine mappings."""

import click
import pyobo
from pyobo.sources.cpt import iter_terms

from biomappings.gilda_utils import append_gilda_predictions
from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate vaccine mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("cvx", ["mesh", "cpt", "vo"], provenance=provenance)
    append_gilda_predictions("cpt", ["mesh", "vo"], provenance=provenance)

    preds = []
    grounder = pyobo.get_grounder(["mesh", "vo"], versions=["2023", None])
    for term in iter_terms():
        texts = [term.name, *(s.name for s in term.synonyms)]
        for text in texts:
            for scored_match in grounder.get_matches(text + " vaccine"):
                pred = SemanticMapping(
                    subject=term.reference,
                    predicate="skos:exactMatch",
                    object=scored_match.refeference,
                    mapping_justification="semapv:LexicalMatching",
                    confidence=0.9,
                    mapping_tool=provenance,
                )
                preds.append(pred)
    append_prediction_tuples(preds)


if __name__ == "__main__":
    main()
