"""Generate a summary for the Biomappings website."""

from __future__ import annotations

import itertools as itt
import os
import typing
from collections import Counter
from collections.abc import Iterable, Mapping

import click
import yaml

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
    rv = {
        "positive": _get_counter(true_mappings),
        "negative": _get_counter(false_mappings),
        "unsure": _get_counter(unsure_mappings),
        "predictions": _get_counter(load_predictions()),
        "contributors": _get_contributors(
            itt.chain(true_mappings, false_mappings, unsure_mappings)
        ),
    }
    rv.update(
        {
            f"{k}_mapping_count": sum(e["count"] for e in rv[k])
            for k in ("positive", "negative", "unsure", "predictions")
        }
    )
    rv.update(
        {
            f"{k}_prefix_count": len(
                set(itt.chain.from_iterable((e["source"], e["target"]) for e in rv[k]))
            )
            for k in ("positive", "negative", "unsure", "predictions")
        }
    )
    with open(path, "w") as file:
        yaml.safe_dump(rv, file, indent=2)


def _get_counter(mappings: Iterable[Mapping[str, str]]):
    from biomappings.utils import get_prefix

    counter: typing.Counter[tuple[str, str]] = Counter()
    for mapping in mappings:
        subject_curie, target_curie = mapping["subject_id"], mapping["object_id"]
        if subject_curie > target_curie:
            subject_curie, target_curie = target_curie, subject_curie
        counter[get_prefix(subject_curie), get_prefix(target_curie)] += 1
    return [
        {"source": subject_prefix, "target": target_prefix, "count": count}
        for (subject_prefix, target_prefix), count in counter.most_common()
    ]


def _get_contributors(mappings: Iterable[Mapping[str, str]]):
    from biomappings.resources import load_curators

    curators = {record["orcid"]: record for record in load_curators()}
    counter = Counter(_get_source(mapping["author_id"]) for mapping in mappings)
    return [
        dict(count=count, **curators[orcid]) if orcid else {"count": count}
        for orcid, count in counter.most_common()
    ]


def _get_source(source: str) -> str | None:
    if source.startswith("orcid:"):
        return source[len("orcid:") :]
    return None


if __name__ == "__main__":
    export()
