"""Repository."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

import click

if TYPE_CHECKING:
    import curies
    from bioregistry import NormalizedNamedReference
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
        from . import lexical

        return lexical.get_predict_command(
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
        from . import lexical

        return lexical.lexical_prediction_cli(
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
        from . import lexical

        return lexical.append_lexical_predictions(
            prefix,
            target_prefixes,
            mapping_tool=mapping_tool,
            path=self.positives_path,
            curated_paths=self.curated_paths,
            **kwargs,
        )

    def get_lint_command(self, converter: curies.Converter | None = None) -> click.Command:
        """Get the lint command."""

        @click.command()
        def lint() -> None:
            """Sort files and remove duplicates."""
            import sssom_pydantic

            nonlocal converter
            if converter is None:
                import bioregistry

                # use the full bioregistry converter instead of re-using the
                # prefix maps inside since this makes sure we cover everything.
                # it automatically contracts the prefix map to what's relevant
                # at the end
                converter = bioregistry.get_converter()

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

    def get_web_command(
        self, *, enable: bool = True, get_user: Callable[[], NormalizedNamedReference] | None = None
    ) -> click.Command:
        """Get the web command."""
        if enable:

            @click.command()
            @resolver_base_option
            @click.option("--orcid")
            def web(resolver_base: str | None, orcid: str) -> None:
                """Run the semantic mappings curation app."""
                import webbrowser

                from bioregistry import NormalizedNamedReference
                from more_click import run_app

                from .wsgi import get_app

                if orcid is not None:
                    user = NormalizedNamedReference(prefix="orcid", identifier=orcid)
                else:
                    user = get_user()

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

        else:

            @click.command()
            def web() -> None:
                """Show an error for the web interface."""
                click.secho(
                    "You are not running biomappings from a development installation.\n"
                    "Please run the following to install in development mode:\n"
                    "  $ git clone https://github.com/biomappings/biomappings.git\n"
                    "  $ cd biomappings\n"
                    "  $ pip install -e .[web]",
                    fg="red",
                )

        return web
