"""Contribute Biomappings back to ontologies encoded in the OBO flat file format.

Example ontologies using the OBO flat file format:
- Uber Anatomy Ontology (UBERON)
- Mondo Disease Ontology (MONDO)
"""

from pathlib import Path
from typing import Union

from bioregistry import curie_to_str, standardize_identifier
from tqdm.auto import tqdm

from biomappings.contribute.utils import get_mappings


def update_obo(prefix: str, path: Union[str, Path], *, uppercase_prefix: bool = False) -> None:
    """Update an OBO flat file.

    :param prefix: Prefix for the ontology
    :param path: Path to the ontology edit file, encoded with OBO flat file format
    :param uppercase_prefix: Should prefixes be uppercased?
    """
    mappings = get_mappings(prefix)

    with open(path, "r") as fh:
        lines = fh.readlines()

    for mapping in tqdm(mappings, unit="mapping", unit_scale=True):
        target_prefix = mapping["target prefix"]
        target_identifier = standardize_identifier(target_prefix, mapping["target identifier"])
        if uppercase_prefix:
            target_prefix = target_prefix.upper()

        source_curie = mapping["source"]
        if not source_curie.startswith("orcid:"):
            continue

        # FIXME be careful about assumption about identifier. currently
        #  assumes that OBO all have bananas.
        lines = add_xref(
            lines,
            mapping["source identifier"],
            curie_to_str(target_prefix, target_identifier),
            mapping["target name"],
            source_curie.removeprefix("orcid:"),
        )

    with open(path, "w") as fh:
        fh.writelines(lines)


def add_xref(lines, node, xref, xref_name, author_orcid: str):
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    #: The 0-indexed line number on which the first xref appears
    start_xref_idx = None
    #: The 0-indexed line number on which the definition appears in a given
    def_idx = None
    xref_entries = []
    xref_values = set()
    for idx, line in enumerate(lines):
        if line == f"id: {node}\n":
            look_for_xref = True
        if look_for_xref and line.startswith("def"):
            def_idx = idx
        if look_for_xref:
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_line: str = line.removeprefix("xref:").strip()
                # TODO handle [] xrefs
                if "{" in xref_line:  # if there are qualifiers, only keep everything up until them
                    xref_values.add(xref_line[: xref_line.find("{")].strip())
                else:
                    xref_values.add(xref_line)
                xref_entries.append(xref_line)
            if start_xref_idx and not line.startswith("xref"):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx

    if xref in xref_values:
        return lines

    xref_entries.append(xref)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref)
    line = (
        f'xref: {xref} {{dcterms:contributor="https://orcid.org/{author_orcid}"}} ! {xref_name}\n'
    )
    lines.insert(start_xref_idx + xr_idx, line)
    return lines


if __name__ == "__main__":
    update_obo(
        "uberon", "/Users/cthoyt/dev/uberon/src/ontology/uberon-edit.obo", uppercase_prefix=True
    )