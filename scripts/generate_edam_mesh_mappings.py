# -*- coding: utf-8 -*-

"""Generate mappings to EDAM from MeSH."""

import click
from more_click import verbose_option

from biomappings.resources import PredictionTuple, append_prediction_tuples
from biomappings.utils import get_script_url
from pyobo.gilda_utils import get_grounder
import pandas as pd


@click.command()
@verbose_option
def main():
    """Generate EDAM-MeSH mappings."""
    provenance = get_script_url(__file__)
    mesh_grounder = get_grounder("mesh")
    df = pd.read_csv("https://edamontology.org/EDAM_1.25.tsv", sep="\t")
    df = df[df["Class ID"].map(lambda s: s.startswith("http://edamontology.org/topic_"))]
    df = df[~df["Obsolete"]]
    df["edam_id"] = df["Class ID"].map(lambda s: s.removeprefix("http://edamontology.org/topic_"))
    df = df[df["edam_id"] != "0003"]  # remove top-level

    tups = []
    for eid, name, synonyms in df[["Class ID", "Preferred Label", "Synonyms"]].values:
        eid = eid.removeprefix("http://edamontology.org/topic_")
        raw_strs = [name]
        if pd.notna(synonyms):
            raw_strs.extend(synonyms.split("|"))
        for raw_str in raw_strs:
            for scored_match in mesh_grounder.ground(raw_str):
                tups.append(
                    PredictionTuple(
                        "edam.topic",
                        eid,
                        name,
                        "skos:exactMatch",
                        "mesh",
                        scored_match.term.id,
                        scored_match.term.entry_name,
                        "semapv:LexicalMatching",
                        scored_match.score,
                        provenance,
                    )
                )

    append_prediction_tuples(tups)


if __name__ == "__main__":
    main()
