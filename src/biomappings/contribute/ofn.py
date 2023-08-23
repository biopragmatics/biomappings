"""Contribute Biomappings back to ontologies encoded in Functional OWL.

Example ontologies using Functional OWL:
- Cell Ontology (CL)
- Experimental Factor Ontology (EFO)
- Human Phenotype Ontology
"""

from copy import deepcopy
from itertools import groupby
from pathlib import Path
from typing import Union, List, Dict, Any

import bioregistry
from bioregistry import curie_to_str, standardize_identifier
from tqdm.auto import tqdm
from pyparsing import OneOrMore, Word, Or
from pyparsing.common import quoted_string
from biomappings.contribute.utils import get_curated_mappings

curie_expr = Word() + ":" + Word()
identifier = curie_expr
identifier_or_scalar = identifier ^ quoted_string
annotation_expr = "Annotation(" + identifier + identifier + ")"
expr = "AnnotationAssertion(" + OneOrMore(annotation_expr) + identifier + identifier_or_scalar + ")"


def update_functional_owl(
    prefix: str, path: Union[str, Path], *, uppercase_prefix: bool = False, compressed: bool = False
) -> None:
    """Update a functional OWL file.

    :param prefix: Prefix for the ontology
    :param path: Path to the ontology edit file, encoded with functional OWL
    :param uppercase_prefix: Should prefixes be uppercased?
    """
    mappings = get_curated_mappings(prefix)[:10]
    print(f"[{prefix}] got {len(mappings):,} positive mappings from Biomappings")

    with open(path, "r") as fh:
        lines = fh.readlines()

    with open(path, "w") as fh:
        fh.writelines(lines)


def update_ofn_lines(
    *, lines: List[str], mappings: List[Dict[str, Any]], progress: bool = True
) -> List[str]:
    """Update the lines of a Functional OWL file.

    :param mappings: Mappings to add
    :param lines: A list of lines of the file (still containing trailing newlines)
    :param progress: Show a progress bar
    :returns: New lines. Does not modify the original list.
    """
    lines = deepcopy(lines)

    for mapping in tqdm(mappings, unit="mapping", unit_scale=True, disable=not progress):
        target_prefix = mapping["target prefix"]
        target_prefix = bioregistry.get_preferred_prefix(target_prefix) or target_prefix
        target_identifier = bioregistry.standardize_identifier(
            target_prefix, mapping["target identifier"]
        )

        source_curie = mapping["source"]
        if not source_curie.startswith("orcid:"):
            continue

        # FIXME be careful about assumption about identifier. currently
        #  assumes that OBO all have bananas.
        lines = add_xref(
            lines=lines,
            node_curie=mapping["source identifier"],
            xref=bioregistry.curie_to_str(target_prefix, target_identifier),
            orcid=source_curie[len("orcid:") :],
        )
    return lines


def _line_is_begin(line: str, curie: str) -> bool:
    obo_luid = curie.replace(":", "_")
    obo_curie = f"obo:{obo_luid}"
    obo_uri = f"<http://purl.obolibrary.org/obo/{obo_luid}>"

    # here, we use line.startwith since this comment
    # typically includes the name of the class
    if line.startswith(f"# Class: {obo_curie}"):
        return True
    if line.startswith(f"# Class: {obo_uri}"):
        return True
    # TODO check with combination of base_uri + LUID
    raise NotImplementedError


def _line_is_xref(line: str, curie: str) -> bool:
    if line.startswith(f"AnnotationAssertion(oboInOwl:hasDbXref"):
        pass


compressed = False
if compressed:
    class_line_prefix = ...
    xref_line_prefix = 'AnnotationAssertion(oboInOwl:hasDbXref"'
    obo_prefix = f"{xref_line_prefix} obo"
else:
    class_line_prefix = f"# Class: <http://purl.obolibrary.org/obo/{...}>"
    xref_line_prefix = (
        'AnnotationAssertion(<http://www.geneontology.org/formats/oboInOwl#hasDbXref>"'
    )
    obo_prefix = f"{xref_line_prefix} <http://purl.obolibrary.org/obo/"


def add_xref(
    lines: List[str],
    node_curie: str,
    xref: str,
    orcid: str,
    *,
    include_xsd_string: bool = False,
) -> List[str]:
    """Add xrefs to an appropriate place in the OWL file."""
    node_owl = node_curie.replace(":", "_")

    look_for_xref = False
    #: The 0-indexed line number on which the ID begins
    id_idx = None
    #: The 0-indexed line number on which the first xref appears
    start_xref_idx = None
    #: The 0-indexed line number on which the definition appears in a given
    def_idx = None

    xref_entries = []

    for idx, line in enumerate(lines):
        if _line_is_begin(line, node_curie):
            id_idx = idx
            look_for_xref = True
        if line.startswith(class_line_prefix):
            look_for_xref = True
        if look_for_xref and line.startswith(xref_line_prefix):
            # The line at which xrefs begin
            def_idx = idx
        if look_for_xref:
            if line.startswith(obo_prefix):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line)
            if start_xref_idx and not line.startswith(xref_line_prefix):
                break
        if look_for_xref and not line.strip():
            start_xref_idx = def_idx

    if start_xref_idx is None:
        # FIXME
        tqdm.write("NONE!")
        return lines

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
        "hp",
        "/Users/cthoyt/dev/human-phenotype-ontology/src/ontology/hp-edit.owl",
        uppercase_prefix=True,
        compressed=False,
    )
