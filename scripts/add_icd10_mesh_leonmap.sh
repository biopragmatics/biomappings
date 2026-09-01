#!/usr/bin/env sh

SCRIPT_DIR=$(dirname $(realpath "$0"))
uv run \
  --script https://github.com/gyorilab/mapnet/raw/refs/heads/main/scripts/generate_leonmap_mesh_icd10_mapping.py \
  --predictions-path "$SCRIPT_DIR/../src/biomappings/resources/predictions.sssom.tsv" \
  --semra-url https://zenodo.org/records/21935586/files/processed.sssom.tsv.gz \
  --coerce-exact
