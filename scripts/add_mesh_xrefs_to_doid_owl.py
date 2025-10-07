"""This script adds newly inferred cross-references for DOID.

These are directly added to the version controlled DOID OWL file.
"""

import csv
from collections.abc import Sequence

import obonet

from biomappings import load_mappings

EDITABLE_OWL_PATH = "/Users/ben/src/HumanDiseaseOntology/src/ontology/doid-edit.owl"
OBO_PATH = "/Users/ben/src/HumanDiseaseOntology/src/ontology/HumanDO.obo"
REVIEW_PATH = "/Users/ben/src/HumanDiseaseOntology/doid_mesh_review.tsv"

# Get the DOID ontology
g = obonet.read_obo(
    "https://raw.githubusercontent.com/DiseaseOntology/"
    "HumanDiseaseOntology/main/src/ontology/HumanDO.obo"
)


def add_xref(lines: list[str], node_curie: str, xref_curie: str) -> list[str]:
    """Add xrefs to an appropriate place in the OWL file."""
    node_owl = node_curie.replace(":", "_")
    look_for_xref = False
    start_xref_idx = None
    def_idx: int | None = None
    xref_entries = []
    for idx, line in enumerate(lines):
        # First, find the class with the given ID and start looking for xrefs
        if line.startswith(f"# Class: obo:{node_owl}"):
            blank_counter = 0
            look_for_xref = True
            def_idx = idx + 2
            continue
        # If we are already looking for xrefs after the header
        if look_for_xref:
            # Note that there is always a blank line right after this header, and
            # also after the block corresponding to the entry ends. So we need
            # to be able to tell whether we are at the first or second blank line
            # after the header.
            if not line.strip():
                if not blank_counter:
                    blank_counter += 1
                    continue
                else:
                    break
            # If we find some xrefs, we keep track of those
            if line.startswith("AnnotationAssertion(oboInOwl:hasDbXref obo"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line)
            # If we found any xrefs but now there is a different line, we finish
            elif start_xref_idx and not line.startswith("AnnotationAssertion(oboInOwl:hasDbXref"):
                break
    # If we never found any existing xrefs then we will put the new xref
    # after the definition
    if start_xref_idx is None:
        if def_idx is None:
            raise ValueError
        start_xref_idx = def_idx + 1
    # We now have to render the xref string and sort xrefs alphabetically
    # to make sure we put the new one in the right place
    xref_str = (
        f'AnnotationAssertion(oboInOwl:hasDbXref obo:{node_owl} "{xref_curie}"^^xsd:string)\n'
    )
    xref_entries.append(xref_str)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref_str)
    lines.insert(start_xref_idx + xr_idx, xref_str)
    return lines


def main() -> None:
    """Add curated cross-references to the DOID OWL file."""
    # There are some curations that are redundant since DOID already mapped
    # these nodes to MESH. We figure out what these are so we can avoid
    # adding them.
    doid_already_mapped = set()
    g = obonet.read_obo(OBO_PATH)
    for node, data in g.nodes(data=True):
        # Skip external entries
        if not node.startswith("DOID"):
            continue
        # Make sure we have a name
        if "name" not in data:
            continue
        # Get existing xrefs as a standardized dict
        xrefs = dict([xref.split(":", maxsplit=1) for xref in data.get("xref", [])])
        # If there are already MESH mappings, we keep track of that
        if "MESH" in xrefs:
            doid_already_mapped.add(node)

    # We now load mappings curated in Biomappings
    mappings = load_mappings()
    doid_mappings = [
        (mapping.subject.identifier, mapping.object.identifier, mapping)
        for mapping in mappings
        if (
            mapping.subject.prefix == "doid"
            and mapping.object.prefix == "mesh"
            and mapping.subject.identifier not in doid_already_mapped
        )
    ]
    # Make sure we get and standardize the order of mappings in both directions
    doid_mappings += [
        (mapping.object.identifier, mapping.subject.identifier, mapping)
        for mapping in mappings
        if (
            mapping.subject.prefix == "mesh"
            and mapping.object.prefix == "doid"
            and mapping.object.identifier not in doid_already_mapped
        )
    ]

    # Read the OWL file
    with open(EDITABLE_OWL_PATH) as fh:
        lines = fh.readlines()

    review_cols = [
        "source prefix",
        "source identifier",
        "source name",
        "relation",
        "target prefix",
        "target identifier",
        "target name",
        "type",
        "source",
    ]
    review_rows: list[Sequence[str]] = [review_cols]
    # Add all the xrefs to the OWL, simultaneously add xrefs to a review TSV
    for do_id, mesh_id, mapping in doid_mappings:
        lines = add_xref(lines, do_id, "MESH:" + mesh_id)
        review_rows.append(
            (
                str(mapping.subject.prefix),
                mapping.subject.identifier,
                mapping.subject_name or "",
                mapping.predicate.curie,
                str(mapping.object.prefix),
                mapping.object.identifier,
                mapping.object_name or "",
                mapping.justification.curie,
                mapping.mapping_tool_name or "",
            )
        )

    # Dump the new review TSV and OWL file
    with open(REVIEW_PATH, "w") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerows(review_rows)

    with open(EDITABLE_OWL_PATH, "w") as fh:
        fh.writelines(lines)


if __name__ == "__main__":
    main()
