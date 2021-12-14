from rdflib import Graph
from tqdm import tqdm

import pystow
from biomappings import PredictionTuple
from biomappings.resources import append_prediction_tuples
from biomappings.utils import get_script_url
from pyobo.gilda_utils import get_grounder
from pystow.utils import read_zipfile_rdf


def ensure_agrovoc(version: str) -> Graph:
    url = f"https://agrovoc.fao.org/agrovocReleases/agrovoc_{version}_core.nt.zip"
    path = pystow.ensure("bio", "agrovoc", version, url=url, name="core.nt.zip")
    graph = read_zipfile_rdf(path, inner_path=f"agrovoc_{version}_core.rdf")
    graph.bind("skosxl", "http://www.w3.org/2008/05/skos-xl")
    return graph


QUERY = """
SELECT ?id ?label {
    ?term skosxl:prefLabel / skosxl:literalForm ?label .
    OPTIONAL { ?term skos:scopeNote ?description } .
    FILTER (lang(?label) = 'en') .
    FILTER (strStarts(str(?term), "http://aims.fao.org/aos/agrovoc/c_")) .
    BIND(strafter(str(?term), "_") as ?id)
}
"""


def main():
    version = "2021-12-02"
    provenance = get_script_url(__file__)
    grounder = get_grounder("AGRO")
    graph = ensure_agrovoc(version)
    rows = []
    for identifier_literal, label_literal in tqdm(graph.query(QUERY)):
        identifier: str = identifier_literal.toPython()
        name: str = label_literal.toPython()
        for scored_match in grounder.ground(name):
            rows.append(PredictionTuple(
                "agrovoc",
                identifier,
                name,
                "skos:exactMatch",
                scored_match.term.db.lower(),
                scored_match.term.id,
                scored_match.term.entry_name,
                "lexical",
                scored_match.score,
                provenance,
            ))
    append_prediction_tuples(rows)


if __name__ == '__main__':
    main()
