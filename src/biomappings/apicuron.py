"""Upload curation statistics to APICURON.

Run this with:

.. code-block:: sh

    $ pip install -e .[apicuron]
    $ pip install apicuron-client
    $ python -m biomappings.apicuron
"""

import datetime
from collections.abc import Iterable

import click
from apicuron_client import Description, Report, Submission, resubmit_curations

from biomappings import load_mappings

NOW = datetime.datetime.now()
START = datetime.datetime(year=2020, month=12, day=15)

DESCRIPTION_PAYLOAD = {
    "resource_id": "Biomappings",
    "resource_name": "Biomappings",
    "resource_uri": "https://biopragmatics.github.io/biomappings/",
    "resource_url": "https://biopragmatics.github.io/biomappings/",
    "resource_long_name": "Biomappings",
    "resource_description": "Community curated and predicted equivalences and related "
    "mappings between named biological entities that are not "
    "available from primary sources.",
    "terms_def": [
        {
            "activity_term": "novel_curation",
            "activity_name": "Curated novel mapping",
            "activity_category": "generation",
            "score": 50,
            "description": "Curated a novel mapping between two entities",
        },
        {
            "activity_term": "validate_prediction",
            "activity_name": "Validate predicted mapping",
            "activity_category": "generation",
            "score": 50,
            "description": "Affirmed the correctness of a predicted mapping",
        },
        {
            "activity_term": "invalidate_prediction",
            "activity_name": "Invalidate predicted mapping",
            "activity_category": "generation",
            "score": 50,
            "description": "Affirmed the incorrectness of a predicted mapping",
        },
    ],
    "achievements_def": [
        {
            "category": "1",
            "name": "Newbie curator",
            "count_threshold": 10,
            "type": "badge",
            "list_terms": ["novel_curation", "validate_prediction", "invalidate_prediction"],
            "color_code": "#055701",
        }
    ],
}
DESCRIPTION = Description(**DESCRIPTION_PAYLOAD)


def get_curation_payload() -> Submission:
    """Get curation payload dictionary for upload to APICURON."""
    return Submission(
        resource_uri=DESCRIPTION.resource_uri,
        reports=list(iter_reports()),
    )


def iter_reports() -> Iterable[Report]:
    """Generate reports from the Biomappings for APICURON."""
    for mapping in load_mappings():
        provenance = mapping["source"]
        if not provenance.startswith("orcid:"):
            continue

        source_curie = f"{mapping['source prefix']}:{mapping['source identifier']}"
        target_curie = f"{mapping['target prefix']}:{mapping['target identifier']}"
        entity_uri = f"{source_curie}-{target_curie}"
        yield Report(
            curator_orcid=provenance[len("orcid:") :],
            activity_term="novel_curation",
            resource_uri=DESCRIPTION.resource_uri,
            entity_uri=entity_uri,
        )


@click.command()
@click.option("--token")
def main(token):
    """Submit the payload."""
    sub = get_curation_payload()
    res = resubmit_curations(sub, token=token)
    click.echo(res.text)


if __name__ == "__main__":
    main()
