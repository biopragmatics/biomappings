"""Utilities for generating mappings with BERTMap."""

PREFIX_TO_DOWNLOAD_URL = {
    "GO": "https://purl.obolibrary.org/obo/go.owl",
    "CHEBI": "https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl",
    "DOID": "https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/refs/heads/main/src/ontology/doid.owl",
    "HGNC": "https://storage.googleapis.com/public-download-files/hgnc/owl/owl/hgnc.owl",
    "MESH": "https://data.bioontology.org/ontologies/RH-MESH/submissions"
    "/3/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  # SMALLER 2014 VERSION
    "MESH2024": "https://data.bioontology.org/ontologies/MESH/submissions"
    "/28/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  # Larger 2024 version in TTL format
}

SOURCE_PREFIX_IRI_MAPS = {
    "mesh": lambda x: "http://phenomebrowser.net/ontologies/mesh/mesh.owl#" + x,
    "mesh2024": lambda x: "http://purl.bioontology.org/ontology/MESH/" + x,
    "doid": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "hgnc": lambda x: "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:" + x,
    "chebi": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "go": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
}

IRI_SOURCE_PREFIX_MAPS = {
    "mesh": lambda x: x.removeprefix("http://phenomebrowser.net/ontologies/mesh/mesh.owl#"),
    "mesh2024": lambda x: x.removeprefix("http://purl.bioontology.org/ontology/MESH/"),
    "doid": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "hgnc": lambda x: x.removeprefix(
        "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/"
    ),
    "chebi": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "go": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
}


def get_luid(prefix: str, iri: str) -> str:
    """Get the local unique identifier."""
    return IRI_SOURCE_PREFIX_MAPS[prefix](iri)
