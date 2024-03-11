# Scripts

This folder houses scripts that can be used to generate predicted mappings, typically
through a lexical mapping workflow.

Most of the lexical mappings in Biomappings were generated with a workflow that wraps Gilda and PyOBO.
However, Biomappings is generic to any workflow that generates predictions, such as those
coming from knowledge graph embedding models. More information can be found about the helper functions
for writing your own prediction generation workflow can be found
at https://biomappings.readthedocs.io/en/latest/usage.html. This also has a summary of the data types that
correspond to rows in the mappings (`MappingTuple`) and predictions files (`PredictionTuple`).
