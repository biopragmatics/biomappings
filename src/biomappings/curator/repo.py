"""Repository."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, NamedTuple

import click
import curies
from sssom_pydantic import MappingTool

__all__ = [
    "Repository",
    "resolver_base_option",
]


resolver_base_option = click.option(
    "--resolver-base",
    help="A custom resolver base URL, instead of the Bioregistry.",
)


class Repository(NamedTuple):
    """A quadruple of paths."""

    predictions_path: Path
    positives_path: Path
    negatives_path: Path
    unsure_path: Path

    @property
    def curated_paths(self) -> list[Path]:
        """Get curated paths."""
        return [self.positives_path, self.negatives_path, self.unsure_path]

    def get_predict_command(self) -> click.Command:
        """Get the predict command."""
        from . import lexical_core

        return lexical_core.get_predict_command(
            path=self.predictions_path,
            curated_paths=self.curated_paths,
        )

    def lexical_prediction_cli(
        self,
        prefix: str,
        target: str | list[str],
        /,
        *,
        mapping_tool: str | MappingTool | None = None,
        **kwargs: Any,
    ) -> None:
        """Run the lexical predictions CLI."""
        from . import lexical_core

        return lexical_core.lexical_prediction_cli(
            prefix,
            target,
            mapping_tool=mapping_tool,
            path=self.predictions_path,
            curated_paths=self.curated_paths,
            **kwargs,
        )

    def append_lexical_predictions(
        self,
        prefix: str,
        target_prefixes: str | Iterable[str],
        *,
        mapping_tool: str | MappingTool | None = None,
        **kwargs: Any,
    ) -> None:
        """Append lexical predictions."""
        from . import lexical_core

        return lexical_core.append_lexical_predictions(
            prefix,
            target_prefixes,
            mapping_tool=mapping_tool,
            path=self.positives_path,
            curated_paths=self.curated_paths,
            **kwargs,
        )

    def get_lint_command(self, converter: curies.Converter | None = None) -> click.Command:
        """Get the lint command."""
        import sssom_pydantic

        if converter is None:
            import bioregistry

            # use the full bioregistry converter instead of re-using the
            # prefix maps inside since this makes sure we cover everything.
            # it automatically contracts the prefix map to what's relevant
            # at the end
            converter = bioregistry.get_converter()

        @click.command()
        def lint() -> None:
            """Sort files and remove duplicates."""
            exclude_mappings = []
            for path in self.curated_paths:
                sssom_pydantic.lint(path, converter=converter)
                exclude_mappings.extend(sssom_pydantic.read(path)[0])

            sssom_pydantic.lint(
                self.predictions_path,
                exclude_mappings=exclude_mappings,
                drop_duplicates=True,
            )

        return lint

    def get_web_command(self) -> click.Command:
        """Get the web command."""

        @click.command()
        @resolver_base_option
        @click.option("--orcid", required=True)
        def web(resolver_base: str | None, orcid: str) -> None:
            """Run the semantic mappings curation app."""
            import webbrowser

            from bioregistry import NormalizedNamedReference
            from more_click import run_app

            from .wsgi import get_app

            user = NormalizedNamedReference(prefix="orcid", identifier=orcid)

            app = get_app(
                predictions_path=self.predictions_path,
                positives_path=self.positives_path,
                negatives_path=self.negatives_path,
                unsure_path=self.unsure_path,
                resolver_base=resolver_base,
                user=user,
            )

            webbrowser.open_new_tab("http://localhost:5000")

            run_app(app, with_gunicorn=False)

        return web
