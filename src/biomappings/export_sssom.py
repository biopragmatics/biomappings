# -*- coding: utf-8 -*-

"""Export Biomappings as SSSOM."""

import pathlib

import bioregistry
import click
import yaml

from biomappings import load_mappings, load_predictions
from biomappings.utils import DATA, MiriamValidator

DIRECTORY = pathlib.Path(DATA).joinpath('sssom')
DIRECTORY.mkdir(exist_ok=True, parents=True)
PATH = DIRECTORY.joinpath("biomappings.sssom.tsv")
META_PATH = DIRECTORY.joinpath("biomappings.sssom.yml")
META = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_provider": "https://github.com/biomappings/biomappings",
    "mapping_set_group": "biomappings",
    "mapping_set_id": "biomappings",
    "mapping_set_title": "Biomappings",
}

validator = MiriamValidator()


def get_sssom_df():
    """Get an SSSOM dataframe."""
    import pandas as pd

    rows = []
    prefixes = set()
    columns = [
        "subject_id",
        "predicate_id",
        "object_id",
        "subject_label",
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
                validator.get_curie(mapping["source prefix"], mapping["source identifier"]),
                f'{mapping["relation"]}',
                validator.get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["source name"],
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
                validator.get_curie(mapping["source prefix"], mapping["source identifier"]),
                f'{mapping["relation"]}',
                validator.get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["source name"],
                mapping["target name"],
                "LexicalEquivalenceMatch",  # match type
                None,  # no curator CURIE
                mapping["confidence"],
                mapping["source"],  # mapping tool: source script
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    return prefixes, df


def get_msdf():
    """Get an SSSOM mapping set dataframe object."""
    # FIXME there are bugs in the linkml and SSSOM code that make this not work
    from sssom.datamodel_util import MappingSetDataFrame
    from sssom.parsers import from_dataframe

    _, df = get_sssom_df()
    msdf: MappingSetDataFrame = from_dataframe(
        df, curie_map=dict(bioregistry.get_format_urls()), meta=META
    )
    return msdf


@click.command()
@click.option("--path", default=PATH)
def sssom(path):
    """Export SSSOM."""
    prefixes, df = get_sssom_df()
    df.to_csv(path, sep="\t", index=False)

    # Get a CURIE map containing only the relevant prefixes
    curie_map = {
        prefix: formatter
        for prefix, formatter in bioregistry.get_format_urls().items()
        if prefix in prefixes
    }
    with open(META_PATH, "w") as file:
        yaml.safe_dump({"curie_map": curie_map, **META}, file)

    # TODO incorporate validation from sssom-py


if __name__ == "__main__":
    sssom()
