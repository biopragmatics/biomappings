"""Update biomappings internal format to SSSOM."""

from pathlib import Path

import bioregistry
import pandas as pd

HERE = Path(__file__).parent.resolve()


def main() -> None:
    """Update biomappings internal format to SSSOM."""
    paths = [
        (HERE.joinpath("incorrect.tsv"), HERE.joinpath("negative.sssom.tsv"), True),
        (HERE.joinpath("mappings.tsv"), HERE.joinpath("positive.sssom.tsv"), False),
        (HERE.joinpath("unsure.tsv"), HERE.joinpath("unsure.sssom.tsv"), False),
    ]
    for old_path, new_path, add_not in paths:
        update(old_path, new_path, add_not=add_not)


def update(old_path: Path, new_path: Path, add_not: bool = False) -> None:
    """Run the update on a given file."""
    df = pd.read_csv(old_path, sep="\t")
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

    del df["prediction_type"]
    del df["prediction_confidence"]

    df = df.rename(
        columns={
            "type": "mapping_justification",
            "source": "author_id",
            "source prefix": "subject_id",
            "target prefix": "object_id",
            "source name": "subject_label",
            "target name": "object_label",
            "relation": "predicate_id",
            "prediction_source": "mapping_tool",
        }
    )
    if add_not:
        df["predicate_modifier"] = "NOT"
    df.to_csv(new_path, sep="\t", index=False)


if __name__ == "__main__":
    main()
