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


if __name__ == "__main__":
    main()
