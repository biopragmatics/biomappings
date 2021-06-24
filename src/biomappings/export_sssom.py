# -*- coding: utf-8 -*-

"""Export Biomappings as SSSOM."""

import os

import click
import pandas as pd

from biomappings import load_mappings, load_predictions
from biomappings.utils import DATA, MiriamValidator

PATH = os.path.join(DATA, "biomappings.sssom.tsv")
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
validator = MiriamValidator()


def get_sssom_df() -> pd.DataFrame:
    """Get an SSSOM dataframe."""
    rows = []
    columns = [
        "subject_id",
        "predicate_id",
        "object_id",
        "subject_label",
        "object_label",
        "match_type",
        "creator_id",
        "license",
        'confidence',
        'mapping_tool',
    ]
    for mapping in load_mappings():
        rows.append(
            (
                validator.get_curie(mapping["source prefix"], mapping["source identifier"]),
                f'{mapping["relation"]}',
                validator.get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["source name"],
                mapping["target name"],
                "HumanCurated",  # match type
                mapping["source"],  # curator CURIE
                CC0_URL,
                None,  # no confidence necessary
                None,  # mapping tool: none necessary for manually curated
            )
        )
    for mapping in load_predictions():
        rows.append(
            (
                validator.get_curie(mapping["source prefix"], mapping["source identifier"]),
                f'{mapping["relation"]}',
                validator.get_curie(mapping["target prefix"], mapping["target identifier"]),
                mapping["source name"],
                mapping["target name"],
                "LexicalEquivalenceMatch",  # match type
                None,  # no curator CURIE
                CC0_URL,
                mapping['confidence'],
                mapping['source'],  # mapping tool: source script
            )
        )
    df = pd.DataFrame(rows, columns=columns)
    del df['license']
    return df


@click.command()
@click.option("--path", default=PATH)
def main(path):
    """Export SSSOM."""
    df = get_sssom_df()
    df.to_csv(path, sep="\t", index=False)


if __name__ == "__main__":
    main()
