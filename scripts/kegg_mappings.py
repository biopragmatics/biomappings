"""Generate mappings to Gilda from given PyOBO prefixes."""

from collections.abc import Iterable

import gilda
import gilda.grounder
from pyobo.sources.kegg.api import ensure_list_pathways
from tqdm import tqdm

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url


def iterate_kegg_matches() -> Iterable[PredictionTuple]:
    """Iterate over predictions from KEGG Pathways to GO and MeSH."""
    provenance = get_script_url(__file__)
    id_name_mapping = ensure_list_pathways()
    for identifier, name in tqdm(id_name_mapping.items(), desc="Mapping KEGG Pathways"):
        for scored_match in gilda.ground(name):
            if scored_match.term.db.lower() not in {"go", "mesh"}:
                continue

            yield (
                "kegg.pathway",
                identifier,
                name,
                "skos:exactMatch",
                scored_match.term.db.lower(),
                scored_match.term.id,
                scored_match.term.entry_name,
                "semapv:LexicalMatching",
                scored_match.score,
                provenance,
            )


if __name__ == "__main__":
    append_prediction_tuples(iterate_kegg_matches())
