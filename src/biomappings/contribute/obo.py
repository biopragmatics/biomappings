"""Contribute Biomappings back to ontologies encoded in the OBO flat file format.

Example ontologies using the OBO flat file format:
- Uber Anatomy Ontology (UBERON)
- Mondo Disease Ontology (MONDO)
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import bioregistry
import click
from tqdm.auto import tqdm

from biomappings import SemanticMapping
from biomappings.contribute.utils import get_curated_mappings


def update_obo(*, prefix: str, path: str | Path) -> None:
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
    lines = update_obo_lines(lines=lines, mappings=mappings)
    with path.open("w") as file:
        file.writelines(lines)


def update_obo_lines(
    *, lines: list[str], mappings: list[SemanticMapping], progress: bool = True
) -> list[str]:
    """Update the lines of an OBO file.

    :param mappings: Mappings to add
    :param lines: A list of lines of the file (still containing trailing newlines)
    :param progress: Show a progress bar
    :returns: New lines. Does not modify the original list.
    """
    lines = deepcopy(lines)

    for mapping in tqdm(mappings, unit="mapping", unit_scale=True, disable=not progress):
        subject_curie = bioregistry.normalize_curie(
            mapping.subject.curie, use_preferred=True, strict=True
        )
        if subject_curie is None:
            raise ValueError
        object_curie = bioregistry.normalize_curie(
            mapping.object.curie, use_preferred=True, strict=True
        )
        if object_curie is None:
            raise ValueError

        if not mapping.author or mapping.author.prefix != "orcid":
            continue

        lines = add_xref(
            lines,
            node_curie=subject_curie,
            xref_curie=object_curie,
            xref_name=mapping.object.name,
            author_orcid=mapping.author.identifier,
        )
    return lines


def add_xref(
    lines: list[str], *, node_curie: str, xref_curie: str, xref_name: str, author_orcid: str
) -> list[str]:
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    id_idx = None

    #: The 0-indexed line number on which the first xref appears
    start_xref_idx = None
    #: The 0-indexed line number on which the definition appears in a given
    def_idx = None
    xref_entries = []
    xref_values = set()
    for idx, line in enumerate(lines):
        if line == f"id: {node_curie}":
            id_idx = idx
            look_for_xref = True
        if look_for_xref and line.startswith("def"):
            def_idx = idx
        if look_for_xref:
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_line: str = line[len("xref:") :].strip()
                xref_values.add(_extract_ref(xref_line))
                xref_entries.append(xref_line)
            if start_xref_idx and not line.startswith("xref"):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx

    if id_idx is None:
        # term not found
        return lines

    if xref_curie in xref_values:
        # term already has this xref, don't modify it
        return lines

    if start_xref_idx is None:
        if def_idx:
            start_xref_idx = def_idx + 1
        else:
            # there were no existing xrefs, so let's just stick them directly after the definition
            start_xref_idx = id_idx + 1

    xref_entries.append(xref_curie)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref_curie)
    line = f'xref: {xref_curie} {{dcterms:contributor="https://orcid.org/{author_orcid}"}} ! {xref_name}'
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
    return xref_line


@click.command()
@click.option("--prefix", required=True, help="The prefix corresponding to the ontology")
@click.option(
    "--path",
    type=click.Path(),
    required=True,
    help="After forking and cloning the version controlled repository for an ontology locally, "
    "give the path inside the directory to the ontology's edit file.",
)
def main(prefix: str, path: Path) -> None:
    """Contribute to an OBO file."""
    update_obo(prefix=prefix, path=path)


if __name__ == "__main__":
    main()
