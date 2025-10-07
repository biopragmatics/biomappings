"""Generate mappings from VO."""

import bioontologies
import pyobo
import ssslm
from bioontologies.obograph import Node
from bioregistry import NormalizedNamableReference
from curies.vocabulary import (
    alternative_term,
    exact_match,
    lexical_matching_process,
    see_also,
    structural_matching,
)
from sssom_pydantic import MappingTool
from tqdm import tqdm

from biomappings.resources import SemanticMapping, append_prediction_tuples
from biomappings.utils import get_script_url


def main() -> None:
    """Generate mappings from between VO and MeSH."""
    mesh_grounder = pyobo.get_grounder("mesh")
    provenance = get_script_url(__file__)
    graph = bioontologies.get_obograph_by_prefix("vo", check=False).guess("vo").standardize()
    rows = []
    extracted_mesh = 0
    for node in tqdm(graph.nodes, unit="node", unit_scale=True):
        if not node.name or node.prefix != "vo":
            continue
        if node.meta:
            found_mesh = False
            for p in node.meta.properties or []:
                if not p.predicate:
                    continue
                if p.predicate.curie == see_also.curie:
                    values = [
                        value.strip().replace(" ", "") for value in p.value_raw.strip().split(";")
                    ]
                    for value in values:
                        # TODO this is place to extract other mapping types
                        if not value.lower().startswith("mesh:"):
                            continue
                        mesh_id = value.split(":", 1)[1].strip()
                        mesh_name = pyobo.get_name("mesh", mesh_id)
                        if not mesh_name:
                            tqdm.write(f"No mesh name for vo:{node.name} mapped to mesh:{mesh_id}")
                            continue
                        rows.append(
                            SemanticMapping(
                                subject=NormalizedNamableReference(
                                    prefix=node.prefix,
                                    identifier=node.identifier,
                                    name=node.name,
                                ),
                                predicate=exact_match,
                                object=NormalizedNamableReference(
                                    prefix="mesh",
                                    identifier=mesh_id,
                                    name=mesh_name,
                                ),
                                justification=structural_matching,
                                confidence=0.99,
                                mapping_tool=MappingTool(name=provenance),
                            )
                        )
                        found_mesh = True
                        extracted_mesh += 1
            if found_mesh:
                continue

        _ground(mesh_grounder, node, rows, provenance)

    append_prediction_tuples(rows)
    print(f"extracted {extracted_mesh} mesh mappings. should be about 65")


def _ground(
    grounder: ssslm.Grounder, node: Node, rows: list[SemanticMapping], provenance: str
) -> None:
    if not node.reference:
        return None

    texts = [node.name]
    # VO doesn't store its synonyms using standard predicates,
    # so look in IAO_0000118 (alternate label) or IAO_0000116 (editor note)
    # with "synonym: " as the string prefix
    if node.meta:
        for p in node.meta.properties or []:
            if not p.predicate:
                continue
            if p.predicate.curie == alternative_term.curie.lower():
                texts.append(p.value_raw)
            elif p.predicate.curie == "iao:0000116" and p.value_raw.startswith("synonym:"):
                texts.append(p.value_raw.removeprefix("synonym:").strip())

    for text in [node.name, *(s.value for s in node.synonyms)]:
        if text is None:
            continue
        for scored_match in grounder.get_matches(text):
            rows.append(
                SemanticMapping(
                    subject=node.reference,
                    predicate=exact_match,
                    object=scored_match.reference,
                    justification=lexical_matching_process,
                    confidence=round(scored_match.score, 2),
                    mapping_tool=MappingTool(name=provenance),
                )
            )


if __name__ == "__main__":
    main()
