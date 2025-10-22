"""Generate a summary for the Biomappings website."""

from __future__ import annotations

import itertools as itt
import typing
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

import click
from sssom_pydantic import SemanticMapping

if TYPE_CHECKING:
    from .repo import Repository


def get_summary_command(
    repository: Repository,
    output_directory: Path,
    get_orcid_to_name: typing.Callable[[], dict[str, str]] | None = None,
) -> click.Command:
    """Get the export command."""

    @click.command()
    @click.option("--output", type=Path, default=output_directory.joinpath("summary.yml"))
    def summary(output: Path) -> None:
        """Create export data file."""
        import yaml

        positive_mappings = repository.read_positive_mappings()
        negative_mappings = repository.read_negative_mappings()
        unsure_mappings = repository.read_unsure_mappings()
        predicted_mappings = repository.read_predicted_mappings()

        rv: dict[str, Any] = {
            "contributors": _get_contributors(
                itt.chain(positive_mappings, negative_mappings, unsure_mappings),
                get_orcid_to_name() if get_orcid_to_name is not None else {},
            ),
        }

        for key, mappings in [
            ("positive", positive_mappings),
            ("negative", negative_mappings),
            ("unsure", unsure_mappings),
            ("predictions", predicted_mappings),
        ]:
            count_records = _get_count_records(mappings)
            rv[key] = count_records
            rv[f"{key}_mapping_count"] = sum(
                count_record["count"] for count_record in count_records
            )
            rv[f"{key}_prefix_count"] = len(
                set(
                    itt.chain.from_iterable(
                        (count_record["source"], count_record["target"])
                        for count_record in count_records
                    )
                )
            )

        with open(output, "w") as file:
            yaml.safe_dump(rv, file, indent=2)

    return summary


class CountRecord(TypedDict):
    """A result from getting counter."""

    source: str
    target: str
    count: int


def _get_count_records(mappings: Iterable[SemanticMapping]) -> list[CountRecord]:
    counter: typing.Counter[tuple[str, str]] = Counter()
    for mapping in mappings:
        subject, target = sorted([mapping.subject, mapping.object])
        counter[str(subject.prefix), str(target.prefix)] += 1
    return [
        {"source": subject_prefix, "target": target_prefix, "count": count}
        for (subject_prefix, target_prefix), count in counter.most_common()
    ]


def _get_contributors(
    mappings: Iterable[SemanticMapping], orcid_to_name: dict[str, str]
) -> list[dict[str, Any]]:
    orcid_counter = Counter(
        author.identifier
        for mapping in mappings
        if mapping.authors
        for author in mapping.authors
        if author.prefix == "orcid"
    )
    rv = []
    for orcid, count in orcid_counter.most_common():
        d = {"count": count, "orcid": orcid}
        if name := orcid_to_name.get(orcid):
            d["name"] = name
        rv.append(d)
    return rv
