"""This script adds newly inferred cross-references for CL.

These are directly added to the version controlled CL OWL file.
"""

from biomappings import load_mappings

EDITABLE_OWL_PATH = "/Users/ben/src/cell-ontology/src/ontology/cl-edit.owl"


def add_xref(lines: list[str], node_curie: str, xref_curie: str) -> list[str]:
    """Add xrefs to an appropriate place in the OWL file."""
    node_owl = node_curie.replace(":", "_")
    look_for_xref = False
    start_xref_idx: int | None = None
    def_idx = None
    xref_entries = []
    for idx, line in enumerate(lines):
        if line.startswith(f"# Class: obo:{node_owl}"):
            look_for_xref = True
        if look_for_xref and line.startswith('AnnotationAssertion(oboInOwl:hasDbXref "'):
            def_idx = idx
        if look_for_xref:
            if line.startswith("AnnotationAssertion(oboInOwl:hasDbXref obo"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line)
            if start_xref_idx and not line.startswith("AnnotationAssertion(oboInOwl:hasDbXref"):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx
    xref_str = (
        f'AnnotationAssertion(oboInOwl:hasDbXref obo:{node_owl} "{xref_curie}"^^xsd:string)\n'
    )
    xref_entries.append(xref_str)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref_str)
    if start_xref_idx is None:
        raise ValueError
    lines.insert(start_xref_idx + xr_idx, xref_str)
    return lines


def main() -> None:
    """Add curated cross-references to the CL OBO file."""
    mappings = load_mappings()
    cl_mappings = [m for m in mappings if m.subject.prefix == "cl" and m.object.prefix == "mesh"]

    with open(EDITABLE_OWL_PATH) as fh:
        lines = fh.readlines()

    for mapping in cl_mappings:
        lines = add_xref(
            lines,
            # TODO update to OBO-preferred prefix for subject curie
            mapping.subject.curie,
            mapping.object.curie,
        )

    with open(EDITABLE_OWL_PATH, "w") as fh:
        fh.writelines(lines)


if __name__ == "__main__":
    main()
