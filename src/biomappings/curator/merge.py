"""Export Biomappings as SSSOM."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import click

if TYPE_CHECKING:
    import pandas as pd
    from sssom import MappingSetDataFrame

    from biomappings.curator.repo import Repository

__all__ = [
    "merge",
]

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
    df: pd.DataFrame
    msdf: MappingSetDataFrame


def merge(repository: Repository, directory: Path) -> None:
    """Merge the SSSOM files together and output to a directory."""
    import yaml
    from sssom.writers import write_json, write_owl

    prefix_map, df, msdf = get_merged_sssom(repository)

    # the creator_id slot corresponds to the person who puts the mapping
    # set together, not the authors/creators of the individual mappings
    # themselves
    tsv_meta = {**repository.mapping_set.model_dump(), "curie_map": prefix_map}

    if repository.basename:
        fname = repository.basename
    elif repository.mapping_set.mapping_set_title is not None:
        fname = repository.mapping_set.mapping_set_title.lower().replace(" ", "-")
    else:
        raise ValueError("basename or mapping set title must be se")

    stub = directory.joinpath(fname)
    tsv_path = stub.with_suffix(".sssom.tsv")
    json_path = stub.with_suffix(".sssom.json")
    owl_path = stub.with_suffix(".sssom.owl")
    metadata_path = stub.with_suffix(".sssom.yml")

    with tsv_path.open("w") as file:
        for line in yaml.safe_dump(tsv_meta).splitlines():
            print(f"# {line}", file=file)
        df.to_csv(file, sep="\t", index=False)

    with open(metadata_path, "w") as file:
        yaml.safe_dump(tsv_meta, file)

    click.echo("Writing JSON")
    with json_path.open("w") as file:
        msdf.metadata["mapping_set_id"] = f"{repository.purl_base}/{fname}.sssom.json"
        write_json(msdf, file)
    click.echo("Writing OWL")
    with owl_path.open("w") as file:
        msdf.metadata["mapping_set_id"] = f"{repository.purl_base}/{fname}.sssom.owl"
        write_owl(msdf, file)


def get_merged_sssom(repository: Repository, *, use_tqdm: bool = False) -> SSSOMReturnTuple:
    """Get an SSSOM dataframe."""
    import bioregistry
    import pandas as pd
    from curies.utils import _prefix_from_curie
    from tqdm.auto import tqdm

    prefixes: set[str] = {"semapv"}

    # NEW WAY: load all DFs, concat them, reorder columns

    a = pd.read_csv(repository.positives_path, sep="\t", comment="#")
    b = pd.read_csv(repository.negatives_path, sep="\t", comment="#")
    c = pd.read_csv(repository.predictions_path, sep="\t", comment="#")
    df = pd.concat([a, b, c])
    df = df[columns]

    for column in ["subject_id", "object_id", "predicate_id"]:
        df[column] = df[column].map(lambda p: bioregistry.normalize_curie(p, use_preferred=True))

    for _, mapping in tqdm(
        df.iterrows(), desc="tabulating prefixes & authors", disable=not use_tqdm
    ):
        prefixes.add(_prefix_from_curie(mapping["subject_id"]))
        prefixes.add(_prefix_from_curie(mapping["predicate_id"]))
        prefixes.add(_prefix_from_curie(mapping["object_id"]))
        author_id = mapping["author_id"]
        if pd.notna(author_id) and any(author_id.startswith(x) for x in ["orcid:", "wikidata:"]):
            prefixes.add(_prefix_from_curie(author_id))
        # TODO add justification:

    from sssom.constants import DEFAULT_VALIDATION_TYPES
    from sssom.parsers import from_sssom_dataframe
    from sssom.validators import validate

    prefix_map = get_prefix_map(prefixes)

    try:
        msdf = from_sssom_dataframe(
            df, prefix_map=prefix_map, meta=repository.mapping_set.model_dump()
        )
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

    return SSSOMReturnTuple(prefix_map, df, msdf)


def get_prefix_map(prefixes: Collection[str]) -> dict[str, str]:
    """Get a CURIE map containing only the relevant prefixes."""
    import bioregistry

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
