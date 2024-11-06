"""Import mappings from ComPath."""

import pandas as pd
import pyobo
from tqdm import tqdm

from biomappings.resources import append_true_mappings

URL = "https://github.com/ComPath/compath-resources/raw/master/docs/data/compath.tsv"
BLACKLIST = {"decopath", "pathbank"}


def main():
    """Import mappings from ComPath."""
    df = pd.read_csv(URL, sep="\t")
    df = df[df["relation"] == "skos:exactMatch"]
    df = df[~df["source prefix"].isin(BLACKLIST)]
    df = df[~df["target prefix"].isin(BLACKLIST)]
    df["type"] = "semapv:ManualMatchingCuration"
    df["source"] = "orcid:0000-0002-2046-6145"  # ComPath is courtesy of Uncle Daniel

    # TODO check that species are the same

    # Make sure nomenclature is correct
    df["source name"] = [
        name if prefix == "kegg.pathway" else pyobo.get_name(prefix, identifier)
        for prefix, identifier, name in tqdm(
            df[["source prefix", "source identifier", "source name"]].values
        )
    ]
    df["target name"] = [
        name if prefix == "kegg.pathway" else pyobo.get_name(prefix, identifier)
        for prefix, identifier, name in tqdm(
            df[["target prefix", "target identifier", "target name"]].values
        )
    ]
    df = df.drop_duplicates()
    mappings = (mapping for _, mapping in df.iterrows())
    append_true_mappings(mappings, sort=True)


if __name__ == "__main__":
    main()
