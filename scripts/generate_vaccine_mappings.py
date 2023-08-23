"""Generate vaccine mappings."""

import click
from pyobo.sources.cpt import iter_terms

from biomappings import PredictionTuple
from biomappings.gilda_utils import append_gilda_predictions, get_grounder
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url


@click.command()
def main():
    """Generate vaccine mappings."""
    provenance = get_script_url(__file__)
    append_gilda_predictions("cvx", ["mesh", "cpt", "vo"], provenance=provenance)
    append_gilda_predictions("cpt", ["mesh", "vo"], provenance=provenance)

    preds = []
    grounder = get_grounder(["mesh", "vo"], versions=["2023", None])
    for term in iter_terms():
        texts = [term.name, *(s.name for s in term.synonyms)]
        for text in texts:
            for scored_match in grounder.ground(text + " vaccine"):
                pred = PredictionTuple(
                    source_prefix=term.prefix,
                    source_id=term.identifier,
                    source_name=term.name,
                    relation="skos:exactMatch",
                    target_prefix=scored_match.term.db,
                    target_identifier=scored_match.term.id,
                    target_name=scored_match.term.entry_name,
                    type="semapv:LexicalMatching",
                    confidence=0.9,
                    source=provenance,
                )
                preds.append(pred)
    append_prediction_tuples(preds)


if __name__ == "__main__":
    main()
