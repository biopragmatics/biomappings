#!/usr/bin/env sh

SCRIPT_DIR=$(dirname $(realpath "$0"))
uv run \
  --script https://github.com/gyorilab/mapnet/raw/refs/heads/main/scripts/generate_gilda_mesh_icd10_mapping.py \
  --predictions-path "$SCRIPT_DIR/../src/biomappings/resources/predictions.sssom.tsv" \
  --semra-url "${SEMRA_URL:-https://zenodo.org/records/21935586/files/processed.sssom.tsv.gz?download=1}"
