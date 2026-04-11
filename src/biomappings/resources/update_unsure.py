"""Update the unsure SSSOM curation style."""

from pathlib import Path

import click
import sssom_pydantic
from curies.vocabulary import lexical_matching_process
from sssom_pydantic import SemanticMapping

UNSURE_PATH = Path(__file__).parent.joinpath("unsure.sssom.tsv")


@click.command()
def main() -> None:
    """Fix mappings."""
    mappings, converter, metadata = sssom_pydantic.read(UNSURE_PATH)
    mappings = [fix_mapping(m) for m in mappings]
    sssom_pydantic.write(mappings, UNSURE_PATH, converter=converter, metadata=metadata)


def fix_mapping(mapping: SemanticMapping) -> SemanticMapping:
    return mapping.model_copy(
        update={
            "justification": lexical_matching_process,
            "reviewers": mapping.authors,
            "authors": None,
            "reviewer_agreement": 0.0,
        }
    )


if __name__ == "__main__":
    main()
