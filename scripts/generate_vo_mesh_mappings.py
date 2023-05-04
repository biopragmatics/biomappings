# -*- coding: utf-8 -*-

import bioontologies
import gilda
import pyobo
from tqdm import tqdm

from biomappings import PredictionTuple
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url


def main():
    """Generate mappings from between VO and MeSH."""
    provenance = get_script_url(__file__)
    graph = (
        bioontologies.get_obograph_by_prefix(
            "vo", check=False, json_path="/Users/cthoyt/Desktop/vo.json"
        )
        .guess("vo")
        .standardize()
    )
    rows = []
    extracted_mesh = 0
    for node in tqdm(graph.nodes, unit="node", unit_scale=True):
        if not node.lbl:
            continue
        if node.meta:
            found_mesh = False
            for p in node.meta.basicPropertyValues or []:
                if p.pred_prefix == "rdfs" and p.pred_identifier == "seeAlso":
                    values = [value.strip().replace(" ", "") for value in p.val.strip().split(";")]
                    print(node.luid, values)
                    for value in values:
                        if not value.lower().startswith("mesh:"):
                            continue
                        mesh_id = value.split(":", 1)[1].strip()
                        mesh_name = pyobo.get_name("mesh", mesh_id)
                        if not mesh_name:
                            tqdm.write(f"No mesh name for vo:{node.luid} mapped to mesh:{mesh_id}")
                            continue
                        rows.append(
                            PredictionTuple(
                                "vo",
                                node.luid,
                                node.lbl,
                                "skos:exactMatch",
                                "mesh",
                                mesh_id,
                                mesh_name,
                                "semapv:StructuralMatching",
                                0.99,
                                "vo",
                            )
                        )
                        found_mesh = True
                        extracted_mesh += 1
            if found_mesh:
                continue

        continue
        _ground(node, rows, provenance)

    append_prediction_tuples(rows)
    print(f"extracted {extracted_mesh} mesh mappings. should be abount 65")


def _ground(node, rows, provenance):
    texts = [node.lbl]
    # VO doesn't store its synonyms using standard predicates,
    # so look in IAO_0000118 (alternate label) or IAO_0000116 (editor note)
    # with "synonym: " as the string prefix
    if node.meta:
        for p in node.meta.basicPropertyValues or []:
            if p.pred_prefix == "iao" and p.pred_identifier == "0000118":
                texts.append(p.val)
            if (
                p.pred_prefix == "iao"
                and p.pred_identifier == "0000116"
                and p.val.startswith("synonym:")
            ):
                texts.append(p.val.removeprefix("synonym:").strip())

    for text in [node.lbl, *(s.val for s in node.synonyms)]:
        for scored_match in gilda.ground(text, namespaces=["MESH"]):
            rows.append(
                PredictionTuple(
                    "vo",
                    node.luid,
                    node.lbl,
                    "skos:exactMatch",
                    scored_match.term.db.lower(),
                    scored_match.term.id,
                    scored_match.term.entry_name,
                    "semapv:LexicalMatching",
                    scored_match.score,
                    provenance,
                )
            )


if __name__ == "__main__":
    main()
