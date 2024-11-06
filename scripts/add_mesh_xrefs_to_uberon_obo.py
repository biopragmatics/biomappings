"""This script adds newly inferred cross-references for UBERON.

These are added directly to the version controlled UBERON OBO file.
"""

from biomappings import load_mappings

EDITABLE_OBO_PATH = "/Users/ben/src/uberon/src/ontology/uberon-edit.obo"


def add_xref(lines, node, xref):
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    start_xref_idx = None
    def_idx = None
    xref_entries = []
    for idx, line in enumerate(lines):
        if line == f"id: {node}\n":
            look_for_xref = True
        if look_for_xref and line.startswith("def"):
            def_idx = idx
        if look_for_xref:
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line[6:].strip())
            if start_xref_idx and not line.startswith("xref"):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx
    xref_entries.append(xref)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref)
    lines.insert(start_xref_idx + xr_idx, f"xref: {xref}\n")
    return lines


if __name__ == "__main__":
    mappings = load_mappings()
    uberon_mappings = [m for m in mappings if m["source prefix"] == "uberon"]

    with open(EDITABLE_OBO_PATH) as fh:
        lines = fh.readlines()

    for mapping in uberon_mappings:
        lines = add_xref(
            lines, mapping["source identifier"], "MESH:" + mapping["target identifier"]
        )

    with open(EDITABLE_OBO_PATH, "w") as fh:
        fh.writelines(lines)
