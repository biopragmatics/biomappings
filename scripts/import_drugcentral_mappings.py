"""This script imports Harry Caufield's mappings from DrugCentral to various resources."""

import bioregistry
import click
import pandas as pd
import pyobo
from tqdm import tqdm

from biomappings.resources import append_true_mappings

URL = "http://kg-hub-public-data.s3.amazonaws.com/frozen_incoming_data/drug-id-maps-0.2.sssom.tsv"


@click.command()
def main():
    """Import DrugCentral mappings from Harry Caufield into Biomappings."""
    df = pd.read_csv(URL, sep="\t", skiprows=11)
    del df["author_id"]
    del df["comment"]
    del df["mapping_justification"]
    df = df.rename(
        columns={
            "predicate_id": "relation",
            "subject_label": "source name",
            "object_label": "target name",
            "reviewer_id": "source",
        }
    )
    df["type"] = "manually_reviewed"

    drugcentral_drugbank_mappings = pyobo.get_filtered_xrefs("drugcentral", "drugbank")

    mappings = df.iterrows()
    mappings = [
        row
        for _, row in tqdm(
            mappings, unit="mapping", unit_scale=True, total=len(df.index), desc="Pre-Filtering"
        )
        if (
            row["subject_id"].startswith("DRUGBANK:")
            and row["object_id"].startswith("DrugCentral:")
            and row["object_id"].removeprefix("DrugCentral:") not in drugcentral_drugbank_mappings
        )
    ]
    mappings = (
        _prepare_mapping(row)
        for row in tqdm(mappings, unit="mapping", unit_scale=True, desc="Mapping")
    )
    # Filter mappings with missing values
    mappings = (mapping for mapping in mappings if mapping)
    append_true_mappings(mappings)


def _prepare_mapping(row):
    row = row.to_dict()
    subject_prefix, subject_id = bioregistry.parse_curie(row.pop("subject_id"))
    target_prefix, target_id = bioregistry.parse_curie(row.pop("object_id"))
    row["source prefix"] = subject_prefix
    row["source identifier"] = (
        bioregistry.miriam_standardize_identifier(subject_prefix, subject_id) or subject_id
    )
    row["target prefix"] = target_prefix
    row["target identifier"] = (
        bioregistry.miriam_standardize_identifier(target_prefix, target_id) or subject_id
    )
    if pd.isna(row["source name"]):
        row["source name"] = pyobo.get_name(subject_prefix, subject_id)
    if pd.isna(row["target name"]):
        row["target name"] = pyobo.get_name(target_prefix, target_id)
    if not all(value and pd.notna(value) for value in row.values()):
        tqdm.write(str(row))
        return None
    return row


if __name__ == "__main__":
    main()
