"""Generate mappings between educational resources."""

import itertools

import bioregistry
import click
import pyobo
import ssslm
from curies.vocabulary import exact_match, lexical_matching_process

from biomappings import SemanticMapping
from biomappings.resources import append_predictions
from biomappings.utils import get_script_url

PREFIXES = [
    "oerschema",
    "ccso",
    "dalia",
    "kim.esv",
    "kim.hcrt",
    "kim.hochschulfaechersystematik",
    "kim.lp",
    "kim.schularten",
    "kim.schulfaecher",
    "kim.educationlevel",
    "isced1997",
    "isced2011",
    "isced2013",
    "ADCAD",
    "schema",
    "mesh",
    "gsso",
    "edam",
    "vivo",
    "itsjointly.curriculum",
]

ENGLISH_NAME_QUERY = """\
    SELECT ?uri ?name
    WHERE {
        ?uri skos:prefLabel|rdfs:label ?name .
        FILTER(LANG(?name) = 'en')
    }
"""

ALL_NAME_QUERY = """\
    SELECT ?uri ?name
    WHERE {
        ?uri skos:prefLabel|rdfs:label ?name .
    }
"""

SYNONYM_QUERY = """\
    SELECT ?uri ?synonym
    WHERE {
        ?uri skos:altLabel ?synonym .
    }
"""


@click.command()
def main() -> None:
    """Generate mappings between educational resources."""
    mapping_tool = get_script_url(__file__)
    all_literal_mappings = []
    for prefix in PREFIXES:
        resource = bioregistry.get_resource(prefix, strict=True)

        if not resource.uri_format:
            raise ValueError

        uri_prefix = resource.uri_format.removesuffix("$1")
        click.echo("=========")
        click.echo(f"{prefix} {uri_prefix}")

        if resource.prefix == "mesh":
            literal_mappings = pyobo.get_literal_mappings(prefix, version="2025")
            click.echo(f"got {len(literal_mappings):,} literal mappings from MeSH {prefix}")
            all_literal_mappings.extend(literal_mappings)

        elif resource.get_download_owl() and resource.prefix != "kim.lp":
            literal_mappings = pyobo.get_literal_mappings(prefix)
            click.echo(f"got {len(literal_mappings):,} literal mappings from OWL for {prefix}")
            all_literal_mappings.extend(literal_mappings)

        elif skos_url := (resource.get_download_skos() or resource.get_download_rdf()):
            click.echo(f"getting SKOS {skos_url}")
            literal_mappings = ssslm.read_skos(skos_url)
            click.echo(f"got {len(literal_mappings):,} literal mappings from SKOS for {prefix}")
            all_literal_mappings.extend(literal_mappings)

        else:
            try:
                literal_mappings = pyobo.get_literal_mappings(prefix)
            except pyobo.getters.NoBuildError:
                literal_mappings = []
            if literal_mappings:
                click.echo(f"got {len(literal_mappings):,} literal mappings from {prefix}")
                all_literal_mappings.extend(literal_mappings)
            else:
                click.echo(f"no luck for {prefix}")
                continue

    grounder: ssslm.GildaGrounder = ssslm.make_grounder(all_literal_mappings)
    semantic_mappings = set()
    for _key, entries in grounder._grounder.entries.items():
        n = {(e.db, e.id) for e in entries}
        if len(n) <= 1:
            continue

        local_literal_mappings = [ssslm.LiteralMapping.from_gilda(e) for e in entries]
        for left, right in itertools.combinations(local_literal_mappings, 2):
            if left.reference.prefix == right.reference.prefix:
                continue
            sm = SemanticMapping(
                subject=left.reference,
                object=right.reference,
                predicate=exact_match,
                mapping_justification=lexical_matching_process,
                mapping_tool=mapping_tool,
            )
            semantic_mappings.add(sm)

    append_predictions(semantic_mappings, standardize=True)
    click.echo(f"produced {len(semantic_mappings):,} mappings")


if __name__ == "__main__":
    main()
