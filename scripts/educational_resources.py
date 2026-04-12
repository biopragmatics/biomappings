# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "biomappings[predict-lexical]",
# ]
#
# [tool.uv.sources]
# biomappings = { path = "../", editable = true }
# ///

"""Generate mappings between educational resources."""

import bioregistry

from biomappings import append_lexical_predictions

SKIP = {"kim.lp", "unesco.thesaurus"}
NEEDS_PYOBO = {
    "loc.fdd",  # see http://www.loc.gov/preservation/digital/formats/fddXML.zip
    "oerschema",  # see https://github.com/open-curriculum/oerschema/blob/master/src/config/schema.yml
}
PREFIXES = bioregistry.get_collection_prefixes("0000018", strict=True)
PREFIXES = [p for p in PREFIXES if p not in SKIP and p not in NEEDS_PYOBO]

if __name__ == "__main__":
    for i in range(len(PREFIXES) - 1):
        prefix = PREFIXES[i]
        rest = PREFIXES[i + 1 :]
        append_lexical_predictions(
            prefix, rest, cache=False, force=True, identifiers_are_names=True
        )
