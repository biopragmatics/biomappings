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
OWL_PATH = DIRECTORY.joinpath("biomappings.sssom.owl")
META_PATH = DIRECTORY.joinpath("biomappings.sssom.yml")

CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
META = {
    "license": CC0_URL,
    "mapping_provider": "https://github.com/biopragmatics/biomappings",
    "mapping_set_group": "biomappings",
    "mapping_set_id": "biomappings",
    "mapping_set_title": "Biomappings",
}


def get_sssom_df():
    """Get an SSSOM dataframe."""
    import pandas as pd

    creators = set()

    rows = []
    prefixes = set()
    columns = [
        "subject_id",
        "subject_label",
        "predicate_id",
        "object_id",
        "object_label",
        "mapping_justification",
        "author_id",
        "confidence",
        "mapping_tool",
    ]
    for mapping in load_mappings():
        prefixes.add(mapping["source prefix"])
        prefixes.add(mapping["target prefix"])
        source = mapping["source"]
        if any(source.startswith(x) for x in ["orcid:", "wikidata:"]):
            creators.add(source)
        rows.append(
            (
                get_curie(mapping["source prefix"], mapping["source identifier"]),
                mapping["source name"],
                f'{mapping["relation"]}',
                get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["target name"],
                mapping["type"],  # match justification
                source,  # curator CURIE
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
                mapping["type"],  # match justification
                None,  # no curator CURIE
                mapping["confidence"],
                mapping["source"],  # mapping tool: source script
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    return prefixes, sorted(creators), df


@click.command()
def sssom():
    """Export SSSOM."""
    prefixes, creators, df = get_sssom_df()
    df.to_csv(TSV_PATH, sep="\t", index=False)

    # Get a CURIE map containing only the relevant prefixes
    prefix_map = {
        prefix: formatter
        for prefix, formatter in bioregistry.get_prefix_map().items()
        if prefix in prefixes
    }
    with open(META_PATH, "w") as file:
        yaml.safe_dump({"curie_map": prefix_map, "creator_id": creators, **META}, file)

    from sssom.parsers import from_sssom_dataframe
    from sssom.writers import write_json, write_owl

    try:
        msdf = from_sssom_dataframe(df, prefix_map=prefix_map, meta=META)
    except Exception as e:
        click.secho(f"SSSOM Export failed...\n{e}", fg="red")
        return
    click.echo("Writing JSON")
    with JSON_PATH.open("w") as file:
        write_json(msdf, file)
    click.echo("Writing OWL")
    with OWL_PATH.open("w") as file:
        write_owl(msdf, file)


if __name__ == "__main__":
    sssom()
