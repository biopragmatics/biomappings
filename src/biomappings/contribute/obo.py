"""Contribute Biomappings back to ontologies encoded in the OBO flat file format.

Example ontologies using the OBO flat file format:
- Uber Anatomy Ontology (UBERON)
- Mondo Disease Ontology (MONDO)
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Union

import bioregistry
import click
from bioregistry import curie_to_str, standardize_identifier
from tqdm.auto import tqdm

from biomappings.contribute.utils import get_curated_mappings


def update_obo(*, prefix: str, path: Union[str, Path], upper: bool = False) -> None:
    """Update an OBO flat file.

    :param prefix: Prefix for the ontology
    :param path: Path to the ontology edit file, encoded with OBO flat file format

    Example usage

    .. code-block:: sh

        git clone https://github.com/obophenotype/uberon.git
        python -m biomappings.contribute.obo --prefix uberon --path uberon/src/ontology/uberon-edit.obo
    """
    path = Path(path).resolve()
    with path.open("r") as file:
        lines = file.readlines()
    mappings = get_curated_mappings(prefix)
    lines = update_obo_lines(lines=lines, mappings=mappings, upper=upper)
    with path.open("w") as file:
        file.writelines(lines)


def update_obo_lines(
    *, lines: List[str], mappings: List[Dict[str, Any]], progress: bool = True, upper: bool = False
) -> List[str]:
    """Update the lines of an OBO file.

    :param mappings: Mappings to add
    :param lines: A list of lines of the file (still containing trailing newlines)
    :param progress: Show a progress bar
    :returns: New lines. Does not modify the original list.
    """
    lines = deepcopy(lines)

    for mapping in tqdm(
        mappings, unit="mapping", unit_scale=True, disable=not progress, desc="Adding mappings"
    ):
        target_prefix = mapping["target prefix"]
        preterred_target_prefix = bioregistry.get_preferred_prefix(target_prefix)
        if preterred_target_prefix:
            target_prefix = preterred_target_prefix
        elif upper:
            target_prefix = target_prefix.upper()
        target_identifier = standardize_identifier(target_prefix, mapping["target identifier"])

        source_curie = mapping["source"]
        if not source_curie.startswith("orcid:"):
            tqdm.write("missing ORCID")
            continue

        # FIXME be careful about assumption about identifier. currently
        #  assumes that OBO all have bananas.
        lines = add_xref(
            lines,
            mapping["source identifier"],
            curie_to_str(target_prefix, target_identifier),
            mapping["target name"],
            source_curie[len("orcid:") :],
        )
    return lines


def add_xref(
    lines: List[str], node: str, xref_curie: str, xref_name: str, author_orcid: str
) -> List[str]:
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    id_idx = None

    #: The 0-indexed line number on which the first xref appears
    start_xref_idx = None
    #: The 0-indexed line number on which the definition appears in a given
    def_idx = None
    xref_entries = []
    existing_xref_curies = set()
    for idx, line in enumerate(lines):
        if line.strip() == f"id: {node}":
            id_idx = idx
            look_for_xref = True
        if look_for_xref and line.startswith("def"):
            def_idx = idx
        if look_for_xref:
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_line: str = line[len("xref:") :].strip()
                existing_xref_curies.add(_extract_ref(xref_line))
                xref_entries.append(xref_line)
            if start_xref_idx and not line.startswith("xref"):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx

    if id_idx is None:
        tqdm.write(f"term not found for {node}")
        return lines

    if _standardize_curie(xref_curie) in existing_xref_curies:
        # term already has this xref, don't modify it
        return lines

    if start_xref_idx is None:
        if def_idx:
            start_xref_idx = def_idx + 1
        else:
            # there were no existing xrefs, so let's just stick them directly after the definition
            start_xref_idx = id_idx + 1

    xref_entries.append(xref_curie)
    xref_entries = sorted(xref_entries, key=str.casefold)
    xr_idx = xref_entries.index(xref_curie)
    # see https://github.com/obophenotype/uberon/pull/2950/files#r1302892427 for explanation of correct
    # format for xref contributor information. Names aren't added since they get stripped by protege
    line = f'xref: {xref_curie} {{http://purl.org/dc/terms/contributor="https://orcid.org/{author_orcid}"}}\n'
    lines.insert(start_xref_idx + xr_idx, line)
    return lines


def _extract_ref(xref_line: str) -> str:
    # remove trailing comments
    if "!" in xref_line:
        xref_line = xref_line[: xref_line.find("!")].strip()
    # remove meta-xrefs
    if "[" in xref_line:
        xref_line = xref_line[: xref_line.find("[")].strip()
    # if there are qualifiers, only keep everything up until them
    if "{" in xref_line:
        return xref_line[: xref_line.find("{")].strip()
    return _standardize_curie(xref_line)


def _standardize_curie(curie: str) -> str:
    p, i = bioregistry.parse_curie(curie)
    if not p or not i:
        tqdm.write(f"could not parse existing xref: {curie}")
        return curie
    return bioregistry.curie_to_str(p, i)


@click.command()
@click.option("--prefix", required=True, help="The prefix corresponding to the ontology")
@click.option(
    "--path",
    type=click.Path(),
    required=True,
    help="After forking and cloning the version controlled repository for an ontology locally, "
    "give the path inside the directory to the ontology's edit file.",
)
@click.option("--upper", is_flag=True)
def main(prefix: str, path: Path, upper: bool):
    """Contribute to an OBO file."""
    update_obo(prefix=prefix, path=path, upper=upper)


if __name__ == "__main__":
    main()
