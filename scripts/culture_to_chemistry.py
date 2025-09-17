"""Generate a bridge between cultural heritage and chemical vocabularies."""

import click
from more_click import verbose_option

__all__ = ["main"]


@click.group()
def main():
    """Run culture to chemistry workflows."""


@main.command(name="chmo")
def match_chmo():
    """Get embedding matches to CHMO."""
    from pyobo.struct.vocabulary import related_match

    from biomappings.lexical import lexical_prediction_cli

    lexical_prediction_cli(
        __file__,
        "iconclass",
        "chmo",
        predicate=related_match,
        method="embedding",
    )


@main.command(name="chmo")
def match_obi():
    """Get embedding matches to OBI."""
    from pyobo.struct.vocabulary import related_match

    from biomappings.lexical import lexical_prediction_cli

    lexical_prediction_cli(
        __file__,
        "iconclass",
        "obi",
        predicate=related_match,
        method="embedding",
    )


@main.command(name="chebi")
@verbose_option
def match_chebi() -> None:
    """Get embedding matches to ChEBI."""
    from pyobo.struct.vocabulary import related_match

    from biomappings import SemanticMapping
    from biomappings.lexical import lexical_prediction_cli

    def _custom_filter(m: SemanticMapping) -> bool:
        return len(m.subject.name) < 60

    lexical_prediction_cli(
        __file__,
        "iconclass",
        "chebi",
        predicate=related_match,
        method="ner",
        custom_filter_function=_custom_filter,
    )


@main.command()
def demo() -> None:
    """Run the federation demo."""
    import pystow
    import rdflib
    import sssom
    from curies.dataframe import filter_df_by_prefixes
    from tabulate import tabulate

    from biomappings.resources import POSITIVES_SSSOM_PATH

    path = pystow.join("nfdi", name="chem-culture.sssom.ttl")
    msdf = sssom.parse_tsv(POSITIVES_SSSOM_PATH)

    # only keep iconclass mappings
    msdf.df = filter_df_by_prefixes(msdf.df, column="subject_id", prefixes=["iconclass"])

    sssom.write_rdf(msdf, path)

    graph = rdflib.Graph()
    graph.parse(path)

    # find things in the culture graph
    sparql = """\
        SELECT *
        WHERE {
            ?s skos:relatedMatch

            SERVICE <https://nfdi4culture.de/sparq> {
                ?biomodels_protein owl:sameAs ?uniprot_protein.
            }
            SERVICE <https://search.nfdi4chem.de/sparql> {

            }
        }
    """

    records = graph.query(sparql)
    click.echo(tabulate(records))


if __name__ == "__main__":
    match_chebi()
