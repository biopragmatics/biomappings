"""Contribute Biomappings back to ontologies encoded in Functional OWL.

Example ontologies using Functional OWL:
- Cell Ontology (CL)
- Experimental Factor Ontology (EFO)
- Human Phenotype Ontology
"""

from pathlib import Path
from typing import Union, List

import click

import bioregistry
from bioontologies.robot import convert
from biomappings.contribute.utils import get_curated_mappings
from bioregistry import standardize_identifier


def update_ofn(
    *,
    prefix: str,
    path: Union[str, Path],
    base_uri: str = "http://purl.obolibrary.org/obo/",
    include_xsd_string: bool = False,
) -> None:
    """Update an OWL ontology encoded in Functional OWL.

    :param prefix: Prefix for the ontology
    :param path: Path to the ontology edit file, encoded with in Functional OWL

    Example usage

    .. code-block:: sh

        git clone https://github.com/EBISPOT/efo.git
        python -m biomappings.contribute.ofn --prefix uberon --path efo/src/ontology/efo-edit.owl
    """
    path = Path(path).resolve()
    with path.open("r") as file:
        lines = file.readlines()

    # The last line should have a closing ) that corresponds
    # to the opening ontology tag. Remove it so we can inject
    # additional parts.
    lines = lines[:-1]
    lines.append("\n")
    lines.extend(
        get_ofn_lines(prefix=prefix, base_uri=base_uri, include_xsd_string=include_xsd_string)
    )
    lines.append(")")
    with path.open("w") as file:
        file.writelines(lines)
    # Run through ROBOT to canonicalize
    # convert(input_path=path, output_path=path, fmt="ofn")


def get_ofn_lines(
    *,
    prefix: str,
    include_xsd_string: bool = False,
    base_uri: str = "http://purl.obolibrary.org/obo/",
    relation_uri: str = "http://www.geneontology.org/formats/oboInOwl#hasDbXref",
    contributor_uri: str = "http://purl.org/dc/terms/contributor",
) -> List[str]:
    mappings = get_curated_mappings(prefix)
    rv = []
    for mapping in mappings:
        node_owl = mapping["source identifier"]
        node_owl = node_owl.replace(":", "_")

        target_prefix = mapping["target prefix"]
        target_prefix = bioregistry.get_preferred_prefix(target_prefix) or target_prefix
        target_identifier = standardize_identifier(target_prefix, mapping["target identifier"])
        target_curie = bioregistry.curie_to_str(target_prefix, target_identifier)

        source_curie = mapping["source"]
        if not source_curie.startswith("orcid:"):
            continue
        orcid = source_curie[len("orcid:") :]

        target_value = f'"{target_curie}"'
        if include_xsd_string:
            target_value += "^^xsd:string"

        xref_str = f'AnnotationAssertion(Annotation(<{contributor_uri}> "https://orcid.org/{orcid}") <{relation_uri}> <{base_uri}{node_owl}> {target_value})\n'
        rv.append(xref_str)
    return rv


@click.command()
@click.option("--prefix", required=True, help="The prefix corresponding to the ontology")
@click.option(
    "--path",
    type=click.Path(),
    required=True,
    help="After forking and cloning the version controlled repository for an ontology locally, "
    "give the path inside the directory to the ontology's edit file.",
)
def main(prefix: str, path: Path):
    """Contribute to an OWL file encoded in Functional OWL."""
    update_ofn(prefix=prefix, path=path)


if __name__ == "__main__":
    update_ofn(
        prefix="efo",
        base_uri="http://www.ebi.ac.uk/efo/EFO_",
        path="/Users/cthoyt/dev/efo/src/ontology/efo-edit.owl",
        include_xsd_string=True,
    )
