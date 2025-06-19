"""Generate a summary for the Biomappings website."""

from __future__ import annotations

import itertools as itt
import os
import typing
from collections import Counter
from collections.abc import Iterable
from typing import Any, TypedDict, cast

import click
import yaml
from curies import NamableReference

from biomappings.resources import SemanticMapping

__all__ = [
    "export",
]


@click.command()
def export() -> None:
    """Create export data file."""
    from biomappings.resources import (
        load_false_mappings,
        load_mappings,
        load_predictions,
        load_unsure,
    )
    from biomappings.utils import DATA

    path = os.path.join(DATA, "summary.yml")

    true_mappings = load_mappings()
    false_mappings = load_false_mappings()
    unsure_mappings = load_unsure()

    rv: dict[str, Any] = {
        "contributors": _get_contributors(
            itt.chain(true_mappings, false_mappings, unsure_mappings)
        ),
    }

    for key, mappings in [
        ("positive", true_mappings),
        ("negative", false_mappings),
        ("unsure", unsure_mappings),
        ("predictions", load_predictions()),
    ]:
        count_records = _get_count_records(mappings)
        rv[key] = count_records
        rv[f"{key}_mapping_count"] = sum(count_record["count"] for count_record in count_records)
        rv[f"{key}_prefix_count"] = len(
            set(
                itt.chain.from_iterable(
                    (count_record["source"], count_record["target"])
                    for count_record in count_records
                )
            )
        )

    with open(path, "w") as file:
        yaml.safe_dump(rv, file, indent=2)


class CountRecord(TypedDict):
    """A result from getting counter."""

    source: str
    target: str
    count: int


def _get_count_records(mappings: Iterable[SemanticMapping]) -> list[CountRecord]:
    counter: typing.Counter[tuple[str, str]] = Counter()
    for mapping in mappings:
        subject, target = mapping.subject, mapping.object
        if subject > target:
            subject, target = target, subject
        counter[str(subject.prefix), str(target.prefix)] += 1
    return [
        {"source": subject_prefix, "target": target_prefix, "count": count}
        for (subject_prefix, target_prefix), count in counter.most_common()
    ]


def _get_contributors(mappings: Iterable[SemanticMapping]) -> list[dict[str, str | int]]:
    from biomappings.resources import load_curators

    orcid_to_curator_reference: dict[str, NamableReference] = {
        record.identifier: record for record in load_curators().values()
    }
    counter = Counter(
        mapping.author.identifier
        for mapping in mappings
        if mapping.author and mapping.author.prefix == "orcid"
    )
    return [
        {
            "count": count,
            "orcid": reference.identifier,
            "name": cast(str, reference.name),
        }
        if (reference := orcid_to_curator_reference.get(orcid)) is not None
        else {"count": count}
        for orcid, count in counter.most_common()
    ]


if __name__ == "__main__":
    export()
