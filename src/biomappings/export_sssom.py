"""Export Biomappings as SSSOM."""

import importlib.metadata
import pathlib

import bioregistry
import click
import yaml
from tqdm.auto import tqdm

from biomappings import load_false_mappings, load_mappings, load_predictions
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
    "mapping_set_description": "Biomappings is a repository of community curated and predicted equivalences and "
    "related mappings between named biological entities that are not available from primary sources. It's also a "
    "place where anyone can contribute curations of predicted mappings or their own novel mappings.",
    "mapping_set_id": "https://w3id.org/biopragmatics/biomappings/sssom/biomappings.sssom.tsv",
    "mapping_set_title": "Biomappings",
    "mapping_set_version": importlib.metadata.version("biomappings"),
}


def get_sssom_df(use_tqdm: bool = False):
    """Get an SSSOM dataframe."""
    import pandas as pd

    creators = set()

    rows = []
    prefixes = set()
    columns = [
        "subject_id",
        "subject_label",
        "predicate_id",
        "predicate_modifier",
        "object_id",
        "object_label",
        "mapping_justification",
        "author_id",
        "confidence",
        "mapping_tool",
    ]
    # see https://mapping-commons.github.io/sssom/predicate_modifier/
    # for more information on predicate modifiers
    for label, mappings, predicate_modifier in [
        ("positive mappings", load_mappings(), ""),  # no predicate modifier
        ("negative mappings", load_false_mappings(), "Not"),
    ]:
        for mapping in tqdm(
            mappings, unit="mapping", unit_scale=True, disable=not use_tqdm, desc=label
        ):
            prefixes.add(mapping["source prefix"])
            prefixes.add(mapping["target prefix"])
            source = mapping["source"]
            if any(source.startswith(x) for x in ["orcid:", "wikidata:"]):
                prefixes.add(source.split(":")[0])
                creators.add(source)
            prefixes.add(mapping["relation"].split(":")[0])

            rows.append(
                (
                    get_curie(
                        mapping["source prefix"], mapping["source identifier"], preferred=True
                    ),
                    mapping["source name"],
                    _standardize_curie(mapping["relation"]),
                    predicate_modifier,
                    get_curie(
                        mapping["target prefix"], mapping["target identifier"], preferred=True
                    ),
                    mapping["target name"],
                    mapping["type"],  # match justification
                    source,  # curator CURIE
                    mapping.get("prediction_confidence"),  # may be brought over from prediction
                    mapping.get("prediction_source"),  # may be brought over from prediction
                )
            )

    for mapping in tqdm(
        load_predictions(),
        unit="mapping",
        unit_scale=True,
        disable=not use_tqdm,
        desc="predicted mappings",
    ):
        prefixes.add(mapping["source prefix"])
        prefixes.add(mapping["target prefix"])
        rows.append(
            (
                get_curie(mapping["source prefix"], mapping["source identifier"], preferred=True),
                mapping["source name"],
                _standardize_curie(mapping["relation"]),
                "",  # no predicate modifier
                get_curie(mapping["target prefix"], mapping["target identifier"], preferred=True),
                mapping["target name"],
                mapping["type"],  # match justification
                None,  # no curator CURIE
                mapping["confidence"],
                mapping["source"],  # mapping tool: source script
            )
        )

    df = pd.DataFrame(rows, columns=columns)
    return prefixes, sorted(creators), df


def _standardize_curie(curie: str) -> str:
    prefix, identifier = bioregistry.parse_curie(curie, use_preferred=True)
    if prefix is None or identifier is None:
        raise RuntimeError
    return bioregistry.curie_to_str(prefix, identifier)


@click.command()
def sssom():
    """Export SSSOM."""
    prefixes, creators, df = get_sssom_df()
    df.to_csv(TSV_PATH, sep="\t", index=False)

    # Get a CURIE map containing only the relevant prefixes
    prefix_map = {}
    for prefix in sorted(prefixes, key=str.casefold):
        uri_prefix = bioregistry.get_uri_prefix(prefix)
        if uri_prefix is None:
            raise ValueError(f"could not look up URI prefix for {prefix}")
        pp = bioregistry.get_preferred_prefix(prefix) or prefix
        prefix_map[pp] = uri_prefix

    with open(META_PATH, "w") as file:
        yaml.safe_dump({"curie_map": prefix_map, "creator_id": creators, **META}, file)

    from sssom.constants import DEFAULT_VALIDATION_TYPES
    from sssom.parsers import from_sssom_dataframe
    from sssom.validators import validate
    from sssom.writers import write_json, write_owl

    try:
        msdf = from_sssom_dataframe(df, prefix_map=prefix_map, meta=META)
    except Exception as e:
        click.secho(f"SSSOM Export failed...\n{e}", fg="red")
        return

    validate(msdf=msdf, validation_types=DEFAULT_VALIDATION_TYPES)

    click.echo("Writing JSON")
    with JSON_PATH.open("w") as file:
        msdf.metadata["mapping_set_id"] = (
            "https://w3id.org/biopragmatics/biomappings/sssom/biomappings.sssom.json"
        )
        write_json(msdf, file)
    click.echo("Writing OWL")
    with OWL_PATH.open("w") as file:
        msdf.metadata["mapping_set_id"] = (
            "https://w3id.org/biopragmatics/biomappings/sssom/biomappings.sssom.owl"
        )
        write_owl(msdf, file)


if __name__ == "__main__":
    sssom()
