# -*- coding: utf-8 -*-

from tqdm import tqdm
import gilda
from bioontologies.obograph import Node

import bioontologies
from biomappings import PredictionTuple
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url


def main():
    provenance = get_script_url(__file__)
    graph = bioontologies.get_obograph_by_prefix("vo", check=False).guess("vo").standardize()
    rows = []
    for node in tqdm(graph.nodes, unit="node", unit_scale=True):
        node: Node
        if not node.lbl:
            continue

        # TODO use synonyms from VO
        for scored_match in gilda.ground(node.lbl, namespaces=["MESH"]):
            rows.append(
                PredictionTuple(
                    "vo",
                    node.luid,
                    node.lbl,
                    "skos:exactMatch",
                    scored_match.term.db.lower(),
                    scored_match.term.id,
                    scored_match.term.entry_name,
                    "lexical",
                    scored_match.score,
                    provenance,
                )
            )



    append_prediction_tuples(rows)


if __name__ == "__main__":
    main()
