"""Update biomappings internal format to SSSOM."""

from __future__ import annotations

from pathlib import Path

import bioregistry
import pandas as pd

from biomappings.utils import (
    NEGATIVES_SSSOM_PATH,
    POSITIVES_SSSOM_PATH,
    PREDICTIONS_SSSOM_PATH,
    UNSURE_SSSOM_PATH,
)

HERE = Path(__file__).parent.resolve()
OLD_RESOURCE_FOLDER = Path.home().joinpath("Desktop", "biomappings-old")


def main() -> None:
    """Update biomappings internal format to SSSOM."""
    paths = [
        (OLD_RESOURCE_FOLDER.joinpath("incorrect.tsv"), NEGATIVES_SSSOM_PATH, True),
        (OLD_RESOURCE_FOLDER.joinpath("unsure.tsv"), UNSURE_SSSOM_PATH, False),
        (OLD_RESOURCE_FOLDER.joinpath("mappings.tsv"), POSITIVES_SSSOM_PATH, False),
    ]
    for old_path, new_path, add_not in paths:
        update_curated(old_path, new_path, add_not=add_not)

    update_predicted(OLD_RESOURCE_FOLDER.joinpath("predictions.tsv"), PREDICTIONS_SSSOM_PATH)


def update_predicted(old_path: Path, new_path: Path) -> None:
    """Run the update on a given predictions file."""
    df = pd.read_csv(old_path, sep="\t")
    df = _shared_update(df)
    df = df.rename(columns={"source": "mapping_tool"})
    df.to_csv(new_path, sep="\t", index=False)


def update_curated(old_path: Path, new_path: Path, add_not: bool = False) -> None:
    """Run the update on a given curated file."""
    df = pd.read_csv(old_path, sep="\t")
    df = _shared_update(df)

    # we're deleting prediction type and confidence since these
    # don't have a proper place in the SSSOM data model and can
    # be understood from the original script
    del df["prediction_type"]
    del df["prediction_confidence"]

    df = df.rename(
        columns={
            "source": "author_id",
            "prediction_source": "mapping_tool",
            "prediction_confidence": "confidence",
        }
    )

    if add_not:
        df["predicate_modifier"] = "Not"
    else:
        df["predicate_modifier"] = ""
    df.to_csv(new_path, sep="\t", index=False)


def _shared_update(df: pd.DataFrame) -> pd.DataFrame:
    df["source prefix"] = [
        bioregistry.NormalizedReference(prefix=p, identifier=i).curie
        for p, i in df[["source prefix", "source identifier"]].values
    ]
    df["target prefix"] = [
        bioregistry.NormalizedReference(prefix=p, identifier=i).curie
        for p, i in df[["target prefix", "target identifier"]].values
    ]
    del df["source identifier"]
    del df["target identifier"]

    df = df.rename(
        columns={
            "type": "mapping_justification",
            "source prefix": "subject_id",
            "target prefix": "object_id",
            "source name": "subject_label",
            "target name": "object_label",
            "relation": "predicate_id",
        }
    )
    return df


if __name__ == "__main__":
    main()
