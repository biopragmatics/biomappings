"""Generate a bridge between cultural heritage and chemical vocabularies."""

import click
from more_click import verbose_option

__all__ = ["main"]


@click.group()
def main() -> None:
    """Run culture to chemistry workflows."""


@main.command(name="chmo")
def match_chmo() -> None:
    """Get embedding matches to CHMO."""
    from pyobo.struct.vocabulary import related_match

    from biomappings import lexical_prediction_cli

    lexical_prediction_cli(
        "iconclass",
        "chmo",
        predicate=related_match,
        method="embedding",
        script=__file__,
    )


@main.command(name="chmo")
def match_obi() -> None:
    """Get embedding matches to OBI."""
    from pyobo.struct.vocabulary import related_match

    from biomappings import lexical_prediction_cli

    lexical_prediction_cli(
        "iconclass",
        "obi",
        predicate=related_match,
        method="embedding",
        script=__file__,
    )


@main.command(name="chebi")
@verbose_option
def match_chebi() -> None:
    """Get embedding matches to ChEBI."""
    from pyobo.struct.vocabulary import related_match
    from sssom_pydantic import SemanticMapping

    from biomappings import lexical_prediction_cli

    def _custom_filter(m: SemanticMapping) -> bool:
        return m.subject_name is not None and len(m.subject_name) < 60

    lexical_prediction_cli(
        "iconclass",
        "chebi",
        predicate=related_match,
        method="ner",
        custom_filter_function=_custom_filter,
        script=__file__,
    )


if __name__ == "__main__":
    main()
