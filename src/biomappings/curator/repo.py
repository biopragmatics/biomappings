"""Repository."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

import click
import sssom_pydantic

if TYPE_CHECKING:
    import curies
    from bioregistry import NormalizedNamedReference
    from sssom_pydantic import MappingSet, MappingTool, SemanticMapping

__all__ = [
    "OrcidNameGetter",
    "Repository",
    "UserGetter",
]

#: A function that returns the current user
UserGetter: TypeAlias = Callable[[], "NormalizedNamedReference"]

#: A function that returns a dictionary from ORCID to name
OrcidNameGetter: TypeAlias = Callable[[], dict[str, str]]


@dataclasses.dataclass
class Repository:
    """A quadruple of paths."""

    predictions_path: Path
    positives_path: Path
    negatives_path: Path
    unsure_path: Path
    purl_base: str
    mapping_set: MappingSet
    basename: str | None = None
    ndex_uuid: str | None = None

    @property
    def curated_paths(self) -> list[Path]:
        """Get curated paths."""
        return [self.positives_path, self.negatives_path, self.unsure_path]

    def read_positive_mappings(self) -> list[SemanticMapping]:
        """Load the positive mappings."""
        return sssom_pydantic.read(self.positives_path)[0]

    def read_negative_mappings(self) -> list[SemanticMapping]:
        """Load the negative mappings."""
        return sssom_pydantic.read(self.negatives_path)[0]

    def read_unsure_mappings(self) -> list[SemanticMapping]:
        """Load the unsure mappings."""
        return sssom_pydantic.read(self.unsure_path)[0]

    def read_predicted_mappings(self) -> list[SemanticMapping]:
        """Load the predicted mappings."""
        return sssom_pydantic.read(self.predictions_path)[0]

    def append_positive_mappings(
        self, mappings: Iterable[SemanticMapping], *, converter: curies.Converter | None = None
    ) -> None:
        """Append new lines to the positive mappings document."""
        from .wsgi_utils import insert

        if converter is None:
            import bioregistry

            converter = bioregistry.get_converter()

        insert(
            self.positives_path,
            converter=converter,
            include_mappings=mappings,
        )

    def append_negative_mappings(
        self, mappings: Iterable[SemanticMapping], *, converter: curies.Converter | None = None
    ) -> None:
        """Append new lines to the negative mappings document."""
        from .wsgi_utils import insert

        if converter is None:
            import bioregistry

            converter = bioregistry.get_converter()

        insert(
            self.negatives_path,
            converter=converter,
            include_mappings=mappings,
        )

    def get_cli(
        self,
        *,
        enable_web: bool = True,
        get_user: UserGetter | None = None,
        output_directory: Path | None = None,
        sssom_directory: Path | None = None,
        image_directory: Path | None = None,
        get_orcid_to_name: OrcidNameGetter | None = None,
    ) -> click.Group:
        """Get a CLI."""

        @click.group()
        def main() -> None:
            """Run the CLI."""

        main.add_command(self.get_predict_command())
        main.add_command(self.get_lint_command())
        main.add_command(self.get_web_command(enable=enable_web, get_user=get_user))
        main.add_command(self.get_merge_command(sssom_directory=sssom_directory))
        main.add_command(self.get_ndex_cli())
        main.add_command(
            self.get_summary_command(
                output_directory=output_directory, get_orcid_to_name=get_orcid_to_name
            )
        )
        main.add_command(
            self.get_charts_command(
                output_directory=output_directory, image_directory=image_directory
            )
        )

        @main.command()
        @click.pass_context
        def update(ctx: click.Context) -> None:
            """Run all summary, merge, and chart exports."""
            click.secho("Building general exports", fg="green")
            ctx.invoke(main.commands["summary"])
            click.secho("Building SSSOM export", fg="green")
            ctx.invoke(main.commands["merge"])
            click.secho("Generating charts", fg="green")
            ctx.invoke(main.commands["charts"])

        return main

    def get_charts_command(
        self, output_directory: Path | None = None, image_directory: Path | None = None
    ) -> click.Command:
        """Get the charts command."""

        @click.command()
        @click.option(
            "--directory", type=click.Path(dir_okay=True, file_okay=False), default=output_directory
        )
        @click.option(
            "--image-directory",
            type=click.Path(dir_okay=True, file_okay=False),
            default=image_directory,
        )
        def charts(directory: Path, image_directory: Path) -> None:
            """Make charts."""
            from .charts import make_charts

            make_charts(self, directory, image_directory)

        return charts

    def get_summary_command(
        self,
        output_directory: Path | None = None,
        get_orcid_to_name: OrcidNameGetter | None = None,
    ) -> click.Command:
        """Get the summary command."""
        from .summary import get_summary_command

        return get_summary_command(
            self, output_directory=output_directory, get_orcid_to_name=get_orcid_to_name
        )

    def get_merge_command(self, sssom_directory: Path | None = None) -> click.Command:
        """Get the merge command."""

        @click.command(name="merge")
        @click.option(
            "--directory", type=click.Path(dir_okay=True, file_okay=False), default=sssom_directory
        )
        def main(sssom_directory: Path) -> None:
            """Merge files together to a single SSSOM."""
            from .merge import merge

            merge(self, directory=sssom_directory)

        return main

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
        self, *, enable: bool = True, get_user: UserGetter | None = None
    ) -> click.Command:
        """Get the web command."""
        if enable:

            @click.command()
            @click.option(
                "--resolver-base",
                help="A custom resolver base URL, instead of the Bioregistry.",
            )
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

    def get_ndex_cli(self) -> click.Command:
        """Get a CLI for uploading to NDEx."""

        @click.command()
        @click.option("--username", help="NDEx username, also looks in pystow configuration")
        @click.option("--password", help="NDEx password, also looks in pystow configuration")
        def ndex(username: str | None, password: str | None) -> None:
            """Upload to NDEx, see https://www.ndexbio.org/viewer/networks/402d1fd6-49d6-11eb-9e72-0ac135e8bacf."""
            if not self.ndex_uuid:
                import sys

                click.secho(
                    "can not upload to NDEx, no NDEx UUID is set in the curator configuration."
                )
                raise sys.exit(1)

            from sssom_pydantic.contrib.ndex import update_ndex

            mappings = self.read_positive_mappings()
            update_ndex(
                uuid=self.ndex_uuid,
                mappings=mappings,
                metadata=self.mapping_set,
                username=username,
                password=password,
            )
            click.echo(f"Uploaded to https://bioregistry.io/ndex:{self.ndex_uuid}")

        return ndex
