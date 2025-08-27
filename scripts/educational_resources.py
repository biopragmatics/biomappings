"""Generate mappings between educational resources."""

import itertools

import bioregistry
import click
import pyobo
import rdflib
import ssslm
from curies import NamableReference
from curies.vocabulary import exact_match, has_label, lexical_matching_process

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
    literal_mappings = []
    for prefix in PREFIXES:
        resource = bioregistry.get_resource(prefix, strict=True)

        if not resource.uri_format:
            raise ValueError

        uri_prefix = resource.uri_format.removesuffix("$1")
        click.echo("=========")
        click.echo(f"{prefix} {uri_prefix}")

        if resource.get_download_owl() and resource.prefix != "kim.lp":
            xxx = pyobo.get_literal_mappings(prefix)
            click.echo(f"got {len(xxx):,} literal mappings from OWL for {prefix}")
            literal_mappings.extend(xxx)

        elif skos_url := (resource.get_download_skos() or resource.get_download_rdf()):
            click.echo(f"getting SKOS {skos_url}")
            graph = rdflib.Graph()
            graph.parse(skos_url)
            names = {
                uri.removeprefix(uri_prefix): str(name) for uri, name in graph.query(ENGLISH_NAME_QUERY)
            }

            for uri, name in graph.query(ALL_NAME_QUERY):
                if not uri.startswith(uri_prefix):
                    continue
                identifier = uri.removeprefix(uri_prefix)
                literal_mappings.append(
                    ssslm.LiteralMapping(
                        reference=NamableReference(
                            prefix=resource.prefix,
                            identifier=identifier,
                            name=names.get(identifier) or str(name),
                        ),
                        text=str(name),
                        language=name._language,
                        predicate=has_label,
                    )
                )

            for uri, synonym in graph.query(SYNONYM_QUERY):
                if not uri.startswith(uri_prefix):
                    continue
                identifier = uri.removeprefix(uri_prefix)
                literal_mappings.append(
                    ssslm.LiteralMapping(
                        reference=NamableReference(
                            prefix=prefix, identifier=identifier, name=names.get(identifier)
                        ),
                        text=str(synonym),
                        language=synonym._language,
                    )
                )

        else:
            try:
                xxx = pyobo.get_literal_mappings(prefix)
            except pyobo.getters.NoBuildError:
                xxx = []
            if xxx:
                click.echo(f"got {len(xxx):,} literal mappings from {prefix}")
                literal_mappings.extend(xxx)
            else:
                click.echo(f"no luck for {prefix}")
                continue

    grounder: ssslm.GildaGrounder = ssslm.make_grounder(literal_mappings)
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
