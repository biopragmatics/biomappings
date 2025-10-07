"""Generate vaccine mappings."""

import click
import pyobo
from curies.vocabulary import exact_match, lexical_matching_process
from pyobo.sources.cpt import iter_terms

from biomappings.lexical import append_lexical_predictions
from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url


@click.command()
def main() -> None:
    """Generate vaccine mappings."""
    provenance = get_script_url(__file__)
    append_lexical_predictions("cvx", ["mesh", "cpt", "vo"], provenance=provenance)
    append_lexical_predictions("cpt", ["mesh", "vo"], provenance=provenance)

    preds = []
    grounder = pyobo.get_grounder(["mesh", "vo"], versions=["2023", None])
    for term in iter_terms():
        texts = [term.name, *(s.name for s in term.synonyms)]
        for text in texts:
            for scored_match in grounder.get_matches(text + " vaccine"):
                pred = SemanticMapping(
                    subject=term.reference,
                    predicate=exact_match,
                    object=scored_match.reference,
                    justification=lexical_matching_process,
                    confidence=0.9,
                    mapping_tool=provenance,
                )
                preds.append(pred)
    append_prediction_tuples(preds)


if __name__ == "__main__":
    main()
