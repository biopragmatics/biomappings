import json
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import bioontologies
import bioregistry
from bioontologies.obograph import _compress_uri
from bioregistry import manager
from tabulate import tabulate
from tqdm.auto import tqdm

__all__ = [
    "Result",
    "get_graph",
    "get_primary_mappings",
    "index_mappings",
]


@dataclass
class Result:
    dataset: str
    source: str
    target: str
    total: int
    missing: int
    missing_biomappings: int
    missing_predictions: int

    @classmethod
    def make(
        cls,
        dataset,
        source,
        target,
        datasource_identifiers,
        primary,
        secondary,
        tertiary,
    ):
        return cls.from_dicts(
            dataset=dataset,
            source=source,
            target=target,
            datasource_identifiers=datasource_identifiers,
            ontology_external_identifiers=set(primary.get(source, {}).get(target, {})),
            biomappings_external_identifiers=set(secondary.get(source, {}).get(target, {})),
            biomappings_prediction_identifiers=set(tertiary.get(source, {}).get(target, {})),
        )

    @classmethod
    def from_dicts(
        cls,
        dataset,
        source,
        target,
        datasource_identifiers,
        ontology_external_identifiers,
        biomappings_external_identifiers,
        biomappings_prediction_identifiers,
    ):
        return Result(
            dataset=dataset,
            source=source,
            target=target,
            total=len(datasource_identifiers),
            missing=len(datasource_identifiers - ontology_external_identifiers),
            missing_biomappings=len(
                datasource_identifiers
                - ontology_external_identifiers
                - biomappings_external_identifiers
            ),
            missing_predictions=len(
                datasource_identifiers
                - ontology_external_identifiers
                - biomappings_external_identifiers
                - biomappings_prediction_identifiers
            ),
        )

    def print(self):
        print(
            tabulate(
                [
                    (f"Total in {self.dataset}", f"{self.total:,}", ""),
                    (
                        f"Missing w/ {self.source}",
                        f"{self.missing:,}",
                        f"{self.missing / self.total:.2%}",
                    ),
                    (
                        f"Missing w/ {self.source} + BM.",
                        f"{self.missing_biomappings:,}",
                        f"{self.missing_biomappings / self.total:.1%}",
                    ),
                    (
                        f"Missing w/ {self.source} + BM. + Pred.",
                        f"{self.missing_predictions:,}",
                        f"{self.missing_predictions / self.total:.1%}",
                    ),
                ],
                headers=["Missing", f"Unmappable to {self.target}", "% Unmappable"],
            )
        )


@lru_cache
def get_graph(prefix: str, graph_uri=None):
    parse_results = bioontologies.get_obograph_by_prefix(prefix)
    if len(parse_results.graph_document.graphs) == 1:
        return parse_results.graph_document.graphs[0]
    if graph_uri is None:
        uris = sorted(graph.id for graph in parse_results.graph_document.graphs)
        raise ValueError(f"need a graph_uri for {prefix} since it has multiple graphs: {uris}.")
    return next(graph for graph in parse_results.graph_document.graphs if graph.id == graph_uri)


def get_primary_mappings(prefix: str, graph_uri: str, external_prefix: str, cache_path: Path):
    if cache_path.is_file():
        d = json.loads(cache_path.read_text())
        return d["version"], d["mappings"]

    graph = get_graph(prefix, graph_uri)
    rv = {}
    for node in tqdm(
        graph.nodes,
        unit="node",
        unit_scale=True,
        desc=f"Extracting {external_prefix} from {prefix}",
    ):
        try:
            node_prefix, node_id = _compress_uri(node.id)
        except ValueError:
            continue

        if node_prefix is None or bioregistry.normalize_prefix(node_prefix) != prefix:
            continue

        for xref in node.xrefs:
            xref_prefix, xref_identifier = bioregistry.parse_curie(xref.val)
            if xref_prefix != external_prefix:
                continue
            rv[xref_identifier] = node_id

    version = graph.version or graph.version_iri
    d = {"mappings": rv, "version": version}
    cache_path.write_text(json.dumps(d, indent=2, sort_keys=True))
    return version, rv


def index_mappings(mappings):
    rv = defaultdict(lambda: defaultdict(dict))

    for mapping in tqdm(mappings, unit_scale=True, unit="mapping"):
        source_prefix = mapping["source prefix"]
        source_resource = manager.registry[source_prefix]
        source_id = source_resource.standardize_identifier(mapping["source identifier"])
        target_prefix = mapping["target prefix"]
        target_resource = manager.registry[target_prefix]
        target_id = target_resource.standardize_identifier(mapping["target identifier"])
        rv[source_prefix][target_prefix][source_id] = target_id
        rv[target_prefix][source_prefix][target_id] = source_id

    return {k: dict(v) for k, v in rv.items()}
