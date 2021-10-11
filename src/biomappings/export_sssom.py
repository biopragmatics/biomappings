# -*- coding: utf-8 -*-

"""Export Biomappings as SSSOM."""

import pathlib

import bioregistry
import click
import yaml

from biomappings import load_mappings, load_predictions
from biomappings.utils import DATA, get_curie

DIRECTORY = pathlib.Path(DATA).joinpath("sssom")
DIRECTORY.mkdir(exist_ok=True, parents=True)
TSV_PATH = DIRECTORY.joinpath("biomappings.sssom.tsv")
JSON_PATH = DIRECTORY.joinpath("biomappings.sssom.json")
META_PATH = DIRECTORY.joinpath("biomappings.sssom.yml")
META = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_provider": "https://github.com/biopragmatics/biomappings",
    "mapping_set_group": "biomappings",
    "mapping_set_id": "biomappings",
    "mapping_set_title": "Biomappings",
}


def get_sssom_df():
    """Get an SSSOM dataframe."""
    import pandas as pd

    rows = []
    prefixes = set()
    columns = [
        "subject_id",
        "subject_label",
        "predicate_id",
        "object_id",
        "object_label",
        "match_type",
        "creator_id",
        "confidence",
        "mapping_tool",
    ]
    for mapping in load_mappings():
        prefixes.add(mapping["source prefix"])
        prefixes.add(mapping["target prefix"])
        rows.append(
            (
                get_curie(mapping["source prefix"], mapping["source identifier"]),
                mapping["source name"],
                f'{mapping["relation"]}',
                get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["target name"],
                "HumanCurated",  # match type
                mapping["source"],  # curator CURIE
                None,  # no confidence necessary
                None,  # mapping tool: none necessary for manually curated
            )
        )
    for mapping in load_predictions():
        prefixes.add(mapping["source prefix"])
        prefixes.add(mapping["target prefix"])
        rows.append(
            (
                get_curie(mapping["source prefix"], mapping["source identifier"]),
                mapping["source name"],
                f'{mapping["relation"]}',
                get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["target name"],
                "LexicalEquivalenceMatch",  # match type
                None,  # no curator CURIE
                mapping["confidence"],
                mapping["source"],  # mapping tool: source script
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    return prefixes, df


@click.command()
def sssom():
    """Export SSSOM."""
    prefixes, df = get_sssom_df()
    df.to_csv(TSV_PATH, sep="\t", index=False)

    # Get a CURIE map containing only the relevant prefixes
    prefix_map = {
        prefix: formatter
        for prefix, formatter in bioregistry.get_prefix_map().items()
        if prefix in prefixes
    }
    with open(META_PATH, "w") as file:
        yaml.safe_dump({"curie_map": prefix_map, **META}, file)

    from sssom.parsers import from_sssom_dataframe
    from sssom.writers import write_json

    msdf = from_sssom_dataframe(df, prefix_map=prefix_map, meta=META)
    with JSON_PATH.open("w") as file:
        write_json(msdf, file)

    # TODO add RDF export, but it's currently broken in SSSOM-py
    #  and in general the LinkML one is completely unusable (too slow)


if __name__ == "__main__":
    sssom()
