#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "biomappings",
#     "bioregistry>=0.14.0",
#     "pyobo>=0.13.3",
#     "sssom-curator",
# ]
#
# [tool.uv.sources]
# biomappings = { path = "../", editable = true }
# sssom-curator = { path = "../../sssom-curator" }
# pyobo = { path = "../../pyobo" }
# ///

"""Predict mappings to MeSH for all OBO foundry ontologies."""

import logging

import bioregistry

from biomappings import lexical_prediction_cli

if __name__ == "__main__":
    skip = {"ncit", "ncbitaxon", "interpro", "chebi", "omit", "gaz"}
    extras = {"icd10", "icd11"}
    prefixes = {
        resource.prefix
        for resource in bioregistry.resources()
        if resource.get_obofoundry_prefix()
        and not resource.is_deprecated()
        and not resource.no_own_terms
        and resource.prefix not in skip
    }
    logging.getLogger("pyobo").setLevel(logging.ERROR)
    lexical_prediction_cli(
        "mesh",
        sorted(prefixes | extras),
        filter_mutual_mappings=True,
        flip=True,
    )
