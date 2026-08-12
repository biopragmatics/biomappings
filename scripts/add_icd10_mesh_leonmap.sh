#!/usr/bin/env bash

uv run \
  --script https://github.com/gyorilab/mapnet/raw/refs/heads/main/scripts/generate_leonmap_mesh_icd10_mapping.py --predictions-path src/biomappings/resources/predictions.sssom.tsv
