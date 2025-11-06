"""This script adds newly inferred cross-references for MONDO.

These are added directly to the version controlled MONDO OBO file.
"""

from biomappings import load_mappings

EDITABLE_OBO_PATH = "/home/ben/src/mondo/src/ontology/mondo-edit.obo"


def add_xref(lines: list[str], node: str, xref: str) -> list[str]:
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    start_xref_idx: int | None = None
    def_idx: int | None = None
    name_idx = None
    xref_entries = []
    for idx, line in enumerate(lines):
        # If this is the block for the given node, we start looking for xrefs
        if line == f"id: {node}\n":
            look_for_xref = True
            continue
        # If we are looking for xrefs
        elif look_for_xref:
            # If we find the definition, we save its index
            if line.startswith("def"):
                def_idx = idx
            if line.startswith("name"):
                name_idx = idx
            # If we find an xref, we keep track of it
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line[6:].strip())
            # If we've already found some xrefs and then hit a line that
            # is not an xref, then we are done collecting xrefs
            if start_xref_idx and not line.startswith("xref"):
                break
            # If we then find an empty line, we are at the end of the
            # OBO entry and never found any xrefs. In this case, we put
            # the xref after the definition line or the name line
            if not line.strip():
                if start_xref_idx is None:
                    raise ValueError
                elif def_idx is not None:
                    start_xref_idx = def_idx + 1
                elif name_idx is not None:
                    start_xref_idx = name_idx + 1
                else:
                    raise ValueError
                break
    xref_entries.append(xref)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref)
    if start_xref_idx is None:
        raise ValueError
    lines.insert(start_xref_idx + xr_idx, f'xref: {xref} {{source="MONDO:equivalentTo"}}\n')
    return lines


def main() -> None:
    """Add curated cross-references to the MONDO OBO file."""
    mappings = load_mappings()
    mondo_mappings = [m for m in mappings if m.subject.prefix == "mondo"]

    with open(EDITABLE_OBO_PATH) as fh:
        lines = fh.readlines()

    for mapping in mondo_mappings:
        lines = add_xref(
            # TODO update to OBO-preferred prefix for subject curie
            lines,
            mapping.subject.curie,
            mapping.object.curie,
        )

    with open(EDITABLE_OBO_PATH, "w") as fh:
        fh.writelines(lines)


if __name__ == "__main__":
    main()
