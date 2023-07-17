"""Contribute Biomappings back to ontologies encoded in Functional OWL.

Example ontologies using Functional OWL:
- Cell Ontology (CL)
- Experimental Factor Ontology (EFO)
"""

from pathlib import Path
from typing import Union

from bioregistry import curie_to_str, standardize_identifier
from tqdm.auto import tqdm

from biomappings import load_mappings


def update_functional_owl(
    prefix: str, path: Union[str, Path], *, uppercase_prefix: bool = False
) -> None:
    """Update a functional OWL file

    :param prefix: Prefix for the ontology
    :param path: Path to the ontology edit file, encoded with functional OWL
    :param uppercase_prefix: Should prefixes be uppercased?
    """
    mappings = load_mappings()
    mappings = [mapping for mapping in mappings if mapping["source prefix"] == prefix]

    with open(path, "r") as fh:
        lines = fh.readlines()

    for mapping in tqdm(mappings, unit="mapping", unit_scale=True):
        target_prefix = mapping["target prefix"]
        target_identifier = standardize_identifier(target_prefix, mapping["target identifier"])
        if uppercase_prefix:
            target_prefix = target_prefix.upper()

        # FIXME be careful about assumption about identifier. currently
        #  assumes that OBO all have bananas.
        lines = add_xref(
            lines, mapping["source identifier"], curie_to_str(target_prefix, target_identifier)
        )

    with open(path, "w") as fh:
        fh.writelines(lines)


def add_xref(lines, node, xref, *, include_xsd_string: bool = False):
    """Add xrefs to an appropriate place in the OWL file."""
    node_owl = node.replace(":", "_")
    look_for_xref = False
    start_xref_idx = None
    def_idx = None
    xref_entries = []
    for idx, line in enumerate(lines):
        if line.startswith("# Class: obo:%s" % node_owl):
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

    xref_str = 'AnnotationAssertion(oboInOwl:hasDbXref obo:%s "%s"%s)\n' % (
        node_owl,
        xref,
        "^^xsd:string" if include_xsd_string else "",
    )
    xref_2_str = "AnnotationAssertio(Annotation(oboInOwl:hasDbXref https://orcid.org/) ...)"

    if xref_str in xref_entries:
        return lines
    xref_entries.append(xref_str)
    xref_entries = sorted(xref_entries)
    xr_idx = xref_entries.index(xref_str)
    lines.insert(start_xref_idx + xr_idx, xref_str)
    return lines


if __name__ == "__main__":
    update_functional_owl(
        "cl", "/Users/cthoyt/dev/cell-ontology/src/ontology/cl-edit.owl", uppercase_prefix=True
    )
