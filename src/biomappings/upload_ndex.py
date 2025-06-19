"""Upload the Biomappings to NDEx.

.. seealso:: https://www.ndexbio.org/viewer/networks/402d1fd6-49d6-11eb-9e72-0ac135e8bacf
"""

from __future__ import annotations

import bioregistry
import click
import pystow
from tqdm import tqdm

from biomappings import load_mappings
from biomappings.utils import get_git_hash

__all__ = [
    "BIOMAPPINGS_NDEX_UUID",
    "ndex",
]

BIOMAPPINGS_NDEX_UUID = "402d1fd6-49d6-11eb-9e72-0ac135e8bacf"


@click.command()
@click.option("--username")
@click.option("--password")
def ndex(username: str | None, password: str | None) -> None:
    """Upload to NDEx."""
    try:
        from ndex2 import NiceCXBuilder
    except ImportError:
        click.secho("Need to `pip install ndex2` before uploading to NDEx", fg="red")
        return

    positive_mappings = load_mappings()
    cx = NiceCXBuilder()
    cx.set_name("Biomappings")
    cx.add_network_attribute(
        "description",
        "Manually curated semantic mappings (e.g., skos:exactMatch) between biological entities.",
    )
    cx.add_network_attribute("reference", "https://github.com/biomappings/biomappings")
    cx.add_network_attribute("rights", "Waiver-No rights reserved (CC0)")

    prefixes: set[str] = {
        reference.prefix
        for mapping in positive_mappings
        for reference in (mapping.subject, mapping.object)
    }
    prefixes.add("orcid")
    prefixes.add("semapv")
    cx.set_context({prefix: bioregistry.get_uri_prefix(prefix) for prefix in prefixes})

    cx.add_network_attribute("version", get_git_hash())
    author_orcid_ids = sorted(
        {
            mapping.author.identifier
            for mapping in positive_mappings
            if mapping.author and mapping.author.prefix == "orcid"
        }
    )
    cx.add_network_attribute("author", author_orcid_ids, type="list_of_string")

    for mapping in tqdm(positive_mappings, desc="Loading NiceCXBuilder"):
        source = cx.add_node(
            represents=mapping["subject_label"],
            name=mapping["subject_id"],
        )
        target = cx.add_node(
            represents=mapping["object_label"],
            name=mapping["object_id"],
        )
        edge = cx.add_edge(
            source=source,
            target=target,
            interaction=mapping["predicate_id"],
        )
        cx.add_edge_attribute(edge, "mapping_justification", mapping["mapping_justification"])
        cx.add_edge_attribute(edge, "author_id", mapping["author_id"])

    nice_cx = cx.get_nice_cx()
    nice_cx.update_to(
        uuid=BIOMAPPINGS_NDEX_UUID,
        server=pystow.get_config("ndex", "server", default="http://public.ndexbio.org"),
        username=pystow.get_config("ndex", "username", passthrough=username),
        password=pystow.get_config("ndex", "password", passthrough=password),
    )
    click.echo(f"Uploaded to https://bioregistry.io/ndex:{BIOMAPPINGS_NDEX_UUID}")


if __name__ == "__main__":
    ndex()
