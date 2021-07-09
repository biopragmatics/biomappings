# -*- coding: utf-8 -*-

"""Generate mappings to Gilda from given PyOBO prefixes."""

import click
from more_click import verbose_option

import pyobo
from biomappings.gilda_utils import CMapping, append_gilda_predictions
from biomappings.utils import get_script_url


@click.command()
@verbose_option
def main():
    """Generate CCLE mappings."""
    provenance = get_script_url(__file__)
    custom_filter = generate_custom_filter()
    append_gilda_predictions(
        "ccle",
        ["depmap", "efo", "cellosaurus", "cl", "bto"],
        provenance=provenance,
        relation="skos:exactMatch",
        custom_filter=custom_filter,
        identifiers_are_names=True,
    )


def generate_custom_filter() -> CMapping:
    """Get custom CCLE->X mappings."""
    ccle_depmap = pyobo.get_filtered_xrefs("ccle", "depmap")
    ccle_cellosaurus = _cdict(
        (ccle_id, pyobo.get_xref("depmap", depmap_id, "cellosaurus"))
        for ccle_id, depmap_id in ccle_depmap.items()
    )
    ccle_efo = _cdict(
        (ccle_id, pyobo.get_xref("cellosaurus", cvcl_id, "efo"))
        for ccle_id, cvcl_id in ccle_cellosaurus.items()
    )
    ccle_bto = _cdict(
        (ccle_id, pyobo.get_xref("cellosaurus", cvcl_id, "bto"))
        for ccle_id, cvcl_id in ccle_cellosaurus.items()
    )
    return {
        "ccle": {
            "depmap": ccle_depmap,
            "cellosaurus": ccle_cellosaurus,
            "efo": ccle_efo,
            "ccle_bto": ccle_bto,
        }
    }


def _cdict(x):
    return {k: v for k, v in x if v}


if __name__ == "__main__":
    main()
