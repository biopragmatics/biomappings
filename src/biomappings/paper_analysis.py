"""Code for the paper analysis."""

import json
import pickle
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import bioontologies
import bioregistry
import pyobo
import pystow
from bioontologies.obograph import _parse_uri_or_curie_or_str
from bioregistry import manager
from tabulate import tabulate
from tqdm.auto import tqdm

__all__ = [
    "Result",
    "get_non_obo_mappings",
    "get_obo_mappings",
    "get_primary_mappings",
    "index_mappings",
]

EVALUATION = pystow.module("biomappings", "evaluation")


@dataclass
class Result:
    """Added value result set."""

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
        """Create a value added summary object with analysis over several dictionaries."""
        return cls._from_dicts(
            dataset=dataset,
            source=source,
            target=target,
            datasource_identifiers=datasource_identifiers,
            ontology_external_identifiers=set(primary.get(source, {}).get(target, {})),
            biomappings_external_identifiers=set(secondary.get(source, {}).get(target, {})),
            biomappings_prediction_identifiers=set(tertiary.get(source, {}).get(target, {})),
        )

    @classmethod
    def _from_dicts(
        cls,
        dataset,
        source,
        target,
        datasource_identifiers,
        ontology_external_identifiers,
        biomappings_external_identifiers,
        biomappings_prediction_identifiers,
    ):
        """Create a value added summary object with analysis over several dictionaries."""
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
        """Print a summary of value added statistics."""
        print(  # noqa:T201
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


def get_primary_mappings(
    prefix: str,
    external_prefix: str,
    cache_path: Path,
) -> tuple[str, Mapping[str, str]]:
    """Get mappings from a given ontology (prefix) to another resource (external prefix)."""
    if cache_path.is_file():
        d = json.loads(cache_path.read_text())
        return d["version"], d["mappings"]

    parse_results = bioontologies.get_obograph_by_prefix(prefix)
    version = parse_results.guess_version(prefix)
    graphs = parse_results.graph_document.graphs if parse_results.graph_document else []
    rv: dict[str, str] = {}
    for graph in graphs:
        for node in tqdm(
            graph.nodes,
            unit="node",
            unit_scale=True,
            leave=False,
            desc=f"Extracting {external_prefix} from {prefix}",
        ):
            try:
                node_prefix, node_luid = _parse_uri_or_curie_or_str(node.id)
            except ValueError:
                continue

            if node_prefix is None or bioregistry.normalize_prefix(node_prefix) != prefix:
                continue

            for xref in node.xrefs:
                xref_prefix, xref_luid = bioregistry.parse_curie(xref.val)
                if xref_prefix != external_prefix:
                    continue
                rv[xref_luid] = node_luid

    d = {"mappings": rv, "version": version}
    cache_path.write_text(json.dumps(d, indent=2, sort_keys=True))
    return version, rv


def index_mappings(mappings: Iterable[Mapping[str, str]], path=None, force: bool = False):
    """Create an index of mappings."""
    if path and path.is_file() and not force:
        with open(path, "rb") as file:
            return pickle.load(file)

    rv: defaultdict[str, defaultdict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))

    for mapping in tqdm(mappings, unit_scale=True, unit="mapping"):
        source_prefix = mapping["source prefix"]
        source_resource = manager.registry[source_prefix]
        source_id = source_resource.standardize_identifier(mapping["source identifier"])
        target_prefix = mapping["target prefix"]
        target_resource = manager.registry[target_prefix]
        target_id = target_resource.standardize_identifier(mapping["target identifier"])
        rv[source_prefix][target_prefix][source_id] = target_id
        rv[target_prefix][source_prefix][target_id] = source_id

    rvp = {k: dict(v) for k, v in rv.items()}
    if path:
        with open(path, "wb") as file:
            pickle.dump(rvp, file)
    return rvp


PRIMARY_MAPPING_CONFIG = [
    ("doid", "umls", "http://purl.obolibrary.org/obo/doid.owl"),
    ("doid", "mesh", "http://purl.obolibrary.org/obo/doid.owl"),
    ("doid", "mondo", "http://purl.obolibrary.org/obo/doid.owl"),
    ("doid", "efo", "http://purl.obolibrary.org/obo/doid.owl"),
    ("mondo", "umls", "http://purl.obolibrary.org/obo/mondo.owl"),
    ("mondo", "mesh", "http://purl.obolibrary.org/obo/mondo.owl"),
    ("mondo", "doid", "http://purl.obolibrary.org/obo/mondo.owl"),
    ("mondo", "efo", "http://purl.obolibrary.org/obo/mondo.owl"),
    ("efo", "mesh", "http://www.ebi.ac.uk/efo/efo.obo"),
    ("efo", "doid", "http://www.ebi.ac.uk/efo/efo.obo"),
    ("efo", "cl", "http://www.ebi.ac.uk/efo/efo.obo"),
    ("efo", "ccle", "http://www.ebi.ac.uk/efo/efo.obo"),
    ("hp", "mesh", "http://purl.obolibrary.org/obo/hp.owl"),
    ("go", "mesh", "http://purl.obolibrary.org/obo/go.owl"),
    ("go", "reactome", "http://purl.obolibrary.org/obo/go.owl"),
    ("go", "wikipathways", "http://purl.obolibrary.org/obo/go.owl"),
    # ("clo", "efo", "http://purl.obolibrary.org/obo/clo.owl"),
    # ("clo", "ccle", "http://purl.obolibrary.org/obo/clo.owl"),
    # ("clo", "depmap", "http://purl.obolibrary.org/obo/clo.owl"),
    # ("clo", "cellosaurus", "http://purl.obolibrary.org/obo/clo.owl"),
    ("uberon", "mesh", "http://purl.obolibrary.org/obo/uberon.owl"),
    ("cl", "efo", "http://purl.obolibrary.org/obo/cl.owl"),
    ("cl", "mesh", "http://purl.obolibrary.org/obo/cl.owl"),
    ("chebi", "mesh", "http://purl.obolibrary.org/obo/chebi.owl"),
    ("chebi", "ncit", "http://purl.obolibrary.org/obo/chebi.owl"),
]


def _clean_version(version: str, prefix) -> str:
    return (
        version.removeprefix(f"http://purl.obolibrary.org/obo/{prefix}/")
        .removeprefix("releases/")
        .removesuffix(f"/{prefix}.owl")
    )


def get_obo_mappings(primary_dd, biomappings_dd):
    """Fill the primary mappings for ontologies and calculate a value added summary."""
    summary_rows = []
    for prefix, external, _uri in PRIMARY_MAPPING_CONFIG:
        cache_path = EVALUATION.join("mappings", name=f"{prefix}_{external}.json")
        version, primary = get_primary_mappings(prefix, external, cache_path=cache_path)
        primary_dd[external][prefix] = primary

        primary_set = set(primary)
        bm = set(biomappings_dd.get(external, {}).get(prefix, {})).union(
            biomappings_dd.get(prefix, {}).get(external, {})
        )
        n_primary = len(primary_set.difference(bm))
        n_biomappings = len(bm)
        n_total = len(primary_set.union(bm))

        if not n_primary and n_biomappings:
            gain = float("inf")
        elif not n_primary and not n_biomappings:
            continue  # skip this
            # gain = "-"
        else:
            gain = round(100 * n_biomappings / n_primary, 1) if n_primary else None

        summary_rows.append(
            (
                prefix,
                _clean_version(version, prefix),
                external,
                n_primary,
                n_biomappings,
                n_total,
                gain,
            )
        )
    return summary_rows


PYOBO_CONFIGS = [
    ("cellosaurus", "efo", "CVCL_", "EFO_"),
    ("cellosaurus", "ccle", "CVCL_", ""),
    # ("cellosaurus", "cl", "CVCL_", ""),
]


def get_non_obo_mappings(primary_dd, biomappings_dd):
    """Fill the primary mappings for non-obo sources calculate a value added summary."""
    summary_rows = []
    for prefix, external, source_banana, target_banana in PYOBO_CONFIGS:
        xrefs_df = pyobo.get_xrefs_df(prefix)
        xrefs_slim_df = xrefs_df[xrefs_df["target_ns"] == external]

        version = "unknown"  # FIXME, e.g., with bioversions.get_version(prefix)
        primary = primary_dd[external][prefix] = {
            target_id.removeprefix(target_banana): source_id.removeprefix(source_banana)
            for source_id, target_id in xrefs_slim_df[[f"{prefix}_id", "target_id"]].values
        }
        n_primary = len(primary)

        bm = set(biomappings_dd.get(external, {}).get(prefix, {})).union(
            biomappings_dd.get(prefix, {}).get(external, {})
        )
        n_biomappings = len(bm)
        n_total = len(set(primary).union(bm))

        if not n_primary and n_biomappings:
            gain = float("inf")
        elif not n_primary and not n_biomappings:
            gain = "-"
        else:
            gain = round(100 * n_biomappings / n_primary, 1) if n_primary else None

        summary_rows.append(
            (
                prefix,
                _clean_version(version, prefix),
                external,
                n_primary,
                n_biomappings,
                n_total,
                gain,
            )
        )
    return summary_rows
