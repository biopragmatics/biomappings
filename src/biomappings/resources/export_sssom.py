"""Export Biomappings as SSSOM."""

from __future__ import annotations

import importlib.metadata
import pathlib
from collections.abc import Collection
from typing import TYPE_CHECKING, NamedTuple

import bioregistry
import click
import yaml
from curies import ReferenceTuple
from tqdm.auto import tqdm

from biomappings.resources import NEGATIVES_SSSOM_PATH, POSITIVES_SSSOM_PATH, PREDICTIONS_SSSOM_PATH
from biomappings.utils import DATA

if TYPE_CHECKING:
    import pandas as pd
    from sssom import MappingSetDataFrame

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


class SSSOMReturnTuple(NamedTuple):
    """A package for SSSOM coalation."""

    prefix_map: dict[str, str]
    creator_curies: list[str]
    df: pd.DataFrame
    msdf: MappingSetDataFrame


def get_sssom_df(*, use_tqdm: bool = False) -> SSSOMReturnTuple:
    """Get an SSSOM dataframe."""
    import pandas as pd

    creator_curies: set[str] = set()
    prefixes: set[str] = {"semapv"}

    # NEW WAY: load all DFs, concat them, reorder columns
    a = pd.read_csv(POSITIVES_SSSOM_PATH, sep="\t")
    b = pd.read_csv(NEGATIVES_SSSOM_PATH, sep="\t")
    c = pd.read_csv(PREDICTIONS_SSSOM_PATH, sep="\t")
    df = pd.concat([a, b, c])
    df = df[columns]

    for column in ["subject_id", "object_id", "predicate_id"]:
        df[column] = df[column].map(lambda p: bioregistry.normalize_curie(p, use_preferred=True))

    for _, mapping in tqdm(
        df.iterrows(), desc="tabulating prefixes & authors", disable=not use_tqdm
    ):
        prefixes.add(_get_prefix(mapping["subject_id"]))
        prefixes.add(_get_prefix(mapping["predicate_id"]))
        prefixes.add(_get_prefix(mapping["object_id"]))
        author_id = mapping["author_id"]
        if pd.notna(author_id) and any(author_id.startswith(x) for x in ["orcid:", "wikidata:"]):
            prefixes.add(_get_prefix(author_id))
            creator_curies.add(author_id)
        # TODO add justification:

    from sssom.constants import DEFAULT_VALIDATION_TYPES
    from sssom.parsers import from_sssom_dataframe
    from sssom.validators import validate

    prefix_map = get_prefix_map(prefixes)

    try:
        msdf = from_sssom_dataframe(df, prefix_map=prefix_map, meta=META)
    except Exception as e:
        click.secho(f"SSSOM Export failed...\n{e}", fg="red")
        raise

    results = validate(msdf=msdf, validation_types=DEFAULT_VALIDATION_TYPES, fail_on_error=False)
    for validator_type, validation_report in results.items():
        if validation_report.results:
            click.secho(f"SSSOM Validator Failed: {validator_type}", fg="red")
            for result in validation_report.results:
                click.secho(f"- {result}", fg="red")
            click.echo("")

    return SSSOMReturnTuple(prefix_map, sorted(creator_curies), df, msdf)


def _get_prefix(curie: str) -> str:
    """Get a prefix from a CURIE string."""
    return ReferenceTuple.from_curie(curie).prefix


def get_prefix_map(prefixes: Collection[str]) -> dict[str, str]:
    """Get a CURIE map containing only the relevant prefixes."""
    prefix_map = {}
    for prefix in sorted(prefixes, key=str.casefold):
        resource = bioregistry.get_resource(prefix)
        if resource is None:
            raise KeyError
        uri_prefix = resource.get_rdf_uri_prefix() or resource.get_uri_prefix()
        if uri_prefix is None:
            raise ValueError(f"could not look up URI prefix for {prefix}")
        preferred_prefix = resource.get_preferred_prefix() or prefix
        prefix_map[preferred_prefix] = uri_prefix
    return prefix_map


@click.command()
def sssom() -> None:
    """Export SSSOM."""
    from sssom.writers import write_json, write_owl

    prefix_map, creator_curies, df, msdf = get_sssom_df()

    tsv_meta = {**META, "creator_id": creator_curies, "curie_map": prefix_map}

    with TSV_PATH.open("w") as file:
        for line in yaml.safe_dump(tsv_meta).splitlines():
            print(f"# {line}", file=file)
        df.to_csv(file, sep="\t", index=False)

    with open(META_PATH, "w") as file:
        yaml.safe_dump(tsv_meta, file)

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
