"""Generate mappings using BERTmap."""

import argparse
import os
import subprocess
from functools import reduce
from itertools import product

import torch
from deeponto.align.bertmap import DEFAULT_CONFIG_FILE, BERTMapPipeline
from deeponto.onto import Ontology
from huggingface_hub import snapshot_download

import biomappings
from biomappings.resources import append_prediction_tuples

parser = argparse.ArgumentParser(description="Train BERTMap Model")
parser.add_argument("--config", default=DEFAULT_CONFIG_FILE, help="Path to Config File")
parser.add_argument(
    "--source_ontology_train",
    default="MESH",
    help="Ontologies to match as source during training",
)
parser.add_argument(
    "--target_ontology_train",
    default="DOID",
    help="Ontologies to match as target during training",
)
parser.add_argument(
    "--source_ontologies_inference",
    nargs="+",
    default=["MESH2024"],
    help="Ontologies to match as source during inference",
)
parser.add_argument(
    "--target_ontologies_inference",
    nargs="+",
    default=["DOID", "CHEBI", "HGNC", "GO"],
    help="Ontologies to match as target during inference",
)
parser.add_argument("--ontologies_path", default="resources", help="Directory with ontology files")
parser.add_argument(
    "--mappings_path",
    default="mesh_ambig_mappings.tsv",
    help="Path with mappings to be evaluated with BERRTMap",
)
parser.add_argument(
    "--train_model",
    action="store_true",
    help="If present will locally train a model otherwise will pull from hugging face.",
)
ENDPOINTS = {
    "GO": "https://purl.obolibrary.org/obo/go.owl",
    "CHEBI": "https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl",
    "DOID": "https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/refs/heads/main/src/ontology/doid.owl",
    "HGNC": "https://storage.googleapis.com/public-download-files/hgnc/owl/owl/hgnc.owl",
    "MESH": "https://data.bioontology.org/ontologies/RH-MESH/submissions"
    "/3/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  # SMALLER 2014 VERSION
    "MESH2024": "https://data.bioontology.org/ontologies/MESH/submissions"
    "/28/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  # Larger 2024 version in TTL format
}

SOURCE_PREFIX_IRI_MAPS = {
    "mesh": lambda x: "http://phenomebrowser.net/ontologies/mesh/mesh.owl#" + x,
    "mesh2024": lambda x: "http://purl.bioontology.org/ontology/MESH/" + x,
    "doid": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "hgnc": lambda x: "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:" + x,
    "chebi": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "go": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
}
IRIsourcePrefixMaps = {
    "mesh": lambda x: x.removeprefix("http://phenomebrowser.net/ontologies/mesh/mesh.owl#"),
    "mesh2024": lambda x: x.removeprefix("http://purl.bioontology.org/ontology/MESH/"),
    "doid": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "hgnc": lambda x: x.removeprefix(
        "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/"
    ),
    "chebi": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "go": lambda x: x.removeprefix("http://purl.obolibrary.org/obo/").replace("_", ":"),
}


# pull
def download_ontologies(
    target_ontology_train: str,
    source_ontology_train: str,
    source_ontologies_inference: list,
    target_ontologies_inference: list,
    ontologies_path: str,
):
    """Download OWL Files for specified ontologies."""
    os.makedirs(ontologies_path, exist_ok=True)
    ontology_paths = {}
    for ontology in [
        target_ontology_train,
        source_ontology_train,
        *source_ontologies_inference,
        *target_ontologies_inference,
    ]:
        ext = ".ttl" if ontology.upper() == "MESH2024" else ".owl"
        ontology_path = os.path.join(ontologies_path, ontology.lower() + ext)
        ontology_paths[ontology.lower()] = ontology_path
        if not os.path.isfile(ontology_path):
            print(f"Downloading {ontology}")
            cmd = ["wget", "-O", ontology_path, ENDPOINTS[ontology.upper()]]
            subprocess.run(cmd)
        else:
            print(f"found {ontology.lower()} at {ontology_path}")
    return ontology_paths


def load_bertmap(
    config: str,
    target_ontology_train: str,
    source_ontology_train: str,
    ontology_paths: dict,
    use_biomappings: bool = False,
    train_model: bool = False,
):
    """Load in the bertmap model (will download from hugging face if not present in ./bertmap)."""
    config = BERTMapPipeline.load_bertmap_config(config)

    if use_biomappings:
        print("-" * 100)
        print("generating known mappings")
        config.known_mappings = save_known_maps(
            target_ontology_train=target_ontology_train,
            source_ontology_train=source_ontology_train,
            mappings_path="knownMaps",
        )
    print("-" * 100)
    print(f"Using config: \n{config}")
    print("-" * 100)
    if not train_model:
        config.global_matching.enabled = False
        if not os.path.isdir("bertmap"):
            print("downloading model from hugging face")
            snapshot_download(repo_id="buzgalbraith/BERTMAP-BioMappings", local_dir="./")
        else:
            print("Model found at bertmap")
    src_onto = Ontology(ontology_paths[source_ontology_train.lower()])
    target_onto = Ontology(ontology_paths[target_ontology_train.lower()])
    return BERTMapPipeline(src_onto, target_onto, config)


def save_known_maps(
    target_ontology_train: str, source_ontology_train: str, mappings_path="knownMaps"
):
    """Use true mappings from Biomappings as ground truth for training BertMap Model."""
    true_mappings = biomappings.load_mappings()

    # onto_filter = lambda x: (x["target prefix"].lower() == target_ontology_train.lower()) & (
    #     x["source prefix"].lower() == source_ontology_train.lower()
    # )
    # iri_map = lambda x: (
    #     SOURCE_PREFIX_IRI_MAPS[source_ontology_train.lower()](x["source identifier"])
    #     + "\t"
    #     + SOURCE_PREFIX_IRI_MAPS[target_ontology_train.lower()](x["target identifier"])
    #     + "\t1.0\n"
    # )
    def onto_filter(x):
        return (x["target prefix"].lower() == target_ontology_train.lower()) & (
            x["source prefix"].lower() == source_ontology_train.lower()
        )

    def iri_map(x):
        return (
            SOURCE_PREFIX_IRI_MAPS[source_ontology_train.lower()](x["source identifier"])
            + "\t"
            + SOURCE_PREFIX_IRI_MAPS[target_ontology_train.lower()](x["target identifier"])
            + "\t1.0\n"
        )

    known_maps = map(iri_map, filter(onto_filter, true_mappings))

    os.makedirs(mappings_path, exist_ok=True)
    known_maps_path = os.path.join(
        mappings_path,
        source_ontology_train.lower() + "-" + target_ontology_train.lower() + ".tsv",
    )

    f = open(known_maps_path, mode="w")
    f.write("SrcEntity\tTgtEntity\tScore\n")
    f.writelines(known_maps)
    f.close()
    return known_maps_path


# inference
def strip_digits(x):
    """Remove numeric characters from a string."""
    return "".join(filter(lambda x: not x.isdigit(), x))


def bertmap_inference(
    ambig_maps_to_check,
    nonambig_maps_to_check,
    target_onto_prefix: str,
    source_onto_prefix: str,
    bertmap,
    target_onto,
    source_onto,
):
    """Run inference on a single pair of ontologies using BertMap."""
    target_prefix = target_onto_prefix.lower()
    source_prefix = source_onto_prefix.lower()
    # setting constants
    relation = "skos:exactMatch"
    match_type = "semapv:SemanticSimilarityThresholdMatching"
    source = "generate_BERTMap_predictions.py"
    # re-write this as a new lst
    rows = []
    for src_class_iri, src_name, tgt_class_iri, target_name in nonambig_maps_to_check:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]
        conf = bertmap.mapping_predictor.bert_mapping_score(
            src_class_annotations, tgt_class_annotations
        )

        source_identifier = IRIsourcePrefixMaps[source_prefix](src_class_iri)
        target_identifier = IRIsourcePrefixMaps[target_prefix](tgt_class_iri)
        # check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_prefix).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_prefix).upper() in x
        ]
        # if it is mapped at all that means the mapping is either already done or wrong so just skip
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        elif conf < 0.5:
            pass
        else:
            rows.append(
                biomappings.PredictionTuple(
                    strip_digits(source_prefix),
                    source_identifier,
                    src_name,
                    relation,
                    strip_digits(target_prefix),
                    target_identifier,
                    target_name,
                    match_type,
                    conf,
                    source,
                )
            )
    for src_class_iri, src_name, tgt_class_iri, target_name in ambig_maps_to_check:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]

        class_annotation_pairs = list(product(src_class_annotations, tgt_class_annotations))
        synonym_scores = bertmap.bert_synonym_classifier.predict(class_annotation_pairs)
        # only one element tensor is able to be extracted as a scalar by .item()
        conf = float(torch.mean(synonym_scores).item())
        source_identifier = IRIsourcePrefixMaps[source_prefix](src_class_iri)
        target_identifier = IRIsourcePrefixMaps[target_prefix](tgt_class_iri)
        # check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_prefix).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_prefix).upper() in x
        ]
        # if it is mapped at all that means the mapping is either already done or wrong so just skip
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        elif conf < 0.5:
            pass
        else:
            rows.append(
                biomappings.PredictionTuple(
                    strip_digits(source_prefix),
                    source_identifier,
                    src_name,
                    relation,
                    strip_digits(target_prefix),
                    target_identifier,
                    target_name,
                    match_type,
                    conf,
                    source,
                )
            )
    return rows


def get_novel_mappings(target_onto_prefix: str, source_onto_prefix: str, maps_path: str):
    """Get mappings to use for inference."""
    # get all potential mappings
    maps_to_check = get_maps_to_evaluate(
        target_onto_prefix=target_onto_prefix,
        source_onto_prefix=source_onto_prefix,
        maps_path=maps_path,
    )
    # filter out those already in biomappings
    maps_not_in_biomappings = filter_for_biomappings(
        target_onto_prefix=target_onto_prefix,
        source_onto_prefix=source_onto_prefix,
        maps_to_check=maps_to_check,
    )
    # break the remaining into an ambagious an non-ambagious set
    ambagious_maps, non_ambagious_maps = check_ambagious_maps(
        maps_not_in_biomappings=maps_not_in_biomappings
    )
    return ambagious_maps, non_ambagious_maps


def get_maps_to_evaluate(target_onto_prefix: str, source_onto_prefix: str, maps_path: str):
    """Read in the initial set of mappings from a file."""
    target_name = target_onto_prefix.lower()
    source_name = source_onto_prefix.lower()
    mappings = open(maps_path).readlines()

    # split_map = lambda x: x.split("\t")
    # onto_filter = lambda x: (x[0].lower() == strip_digits(source_name)) & (
    #     x[3].lower() == strip_digits(target_name)
    # )
    # iri_map = lambda x: (
    #     SOURCE_PREFIX_IRI_MAPS[source_name](x[1]),
    #     x[2],
    #     SOURCE_PREFIX_IRI_MAPS[target_name](x[4]),
    #     x[5].strip(),
    # )
    def split_map(x):
        """Split an iterable of strings by tab."""
        return x.split("\t")

    def onto_filter(x):
        """Filter to ensure that maps are in the right ontology."""
        return (x[0].lower() == strip_digits(source_name)) & (
            x[3].lower() == strip_digits(target_name)
        )

    def iri_map(x):
        """Map to IRI."""
        return (
            SOURCE_PREFIX_IRI_MAPS[source_name](x[1]),
            x[2],
            SOURCE_PREFIX_IRI_MAPS[target_name](x[4]),
            x[5].strip(),
        )

    maps_to_check = map(iri_map, filter(onto_filter, map(split_map, mappings)))
    return maps_to_check


def filter_for_biomappings(target_onto_prefix: str, source_onto_prefix: str, maps_to_check):
    """Ensure that none of the mappings being evaluated are in biomappings already."""
    target_name = target_onto_prefix.lower()
    source_name = source_onto_prefix.lower()
    biomappings_maps = (
        biomappings.load_mappings()
        + biomappings.load_false_mappings()
        + biomappings.load_predictions()
    )

    # onto_filter = lambda x: (x["target prefix"].lower() == strip_digits(target_name)) & (
    #     x["source prefix"].lower() == strip_digits(source_name)
    # )
    # iri_map = lambda x: (
    #     SOURCE_PREFIX_IRI_MAPS[target_name](x["target identifier"]),
    #     SOURCE_PREFIX_IRI_MAPS[source_name](x["source identifier"]),
    # )
    # known_filter = lambda x: x not in biomappping_maps_to_check_against
    def onto_filter(x):
        """Filter to ensure that maps are in the right ontology."""
        return (x["target prefix"].lower() == strip_digits(target_name)) & (
            x["source prefix"].lower() == strip_digits(source_name)
        )

    def iri_map(x):
        """Map each row to it's iri."""
        return (
            SOURCE_PREFIX_IRI_MAPS[target_name](x["target identifier"]),
            SOURCE_PREFIX_IRI_MAPS[source_name](x["source identifier"]),
        )

    def known_filter(x):
        """Filter for mappings not in biomappings."""
        return x not in biomappping_maps_to_check_against

    biomappping_maps_to_check_against = set(map(iri_map, filter(onto_filter, biomappings_maps)))
    maps_not_in_biomappings = filter(known_filter, maps_to_check)
    return maps_not_in_biomappings


def check_ambagious_maps(maps_not_in_biomappings):
    """Split maps into ambagious and non-ambagious."""
    maps_not_in_biomappings = list(maps_not_in_biomappings)
    value_counts = reduce(
        lambda acc, item: {
            **acc,
            **{f: {**acc.get(f, {}), item[f]: acc.get(f, {}).get(item[f], 0) + 1} for f in [0, 2]},
        },
        maps_not_in_biomappings,
        {},
    )
    value_counts = {**value_counts[0], **value_counts[2]}
    ambagious_iris = set(filter(lambda x: value_counts[x] > 1, value_counts))
    ambagious_maps = filter(
        lambda x: (x[0] in ambagious_iris) or (x[2] in ambagious_iris),
        maps_not_in_biomappings,
    )
    non_ambagious_maps = filter(
        lambda x: (x[0] not in ambagious_iris) and (x[2] not in ambagious_iris),
        maps_not_in_biomappings,
    )
    return ambagious_maps, non_ambagious_maps


def inference_across_ontologies(
    config_path: str,
    target_ontologies_inference: list,
    source_ontologies_inference: list,
    mappings_path: str,
    ontology_paths: dict,
):
    """Run inference using BERTMap model over multiple ontologies."""
    for target_onto_prefix, source_onto_prefix in product(
        target_ontologies_inference, source_ontologies_inference
    ):
        print("Filtering Mappings")
        ambagious_maps, non_ambagious_maps = get_novel_mappings(
            target_onto_prefix=target_onto_prefix,
            source_onto_prefix=source_onto_prefix,
            maps_path=mappings_path,
        )
        print("loading ontologies")
        src_onto = Ontology(ontology_paths[source_onto_prefix.lower()])
        target_onto = Ontology(ontology_paths[target_onto_prefix.lower()])
        config = BERTMapPipeline.load_bertmap_config(config_path)
        config.global_matching.enabled = False
        print("loading model")
        bertmap = BERTMapPipeline(src_onto, target_onto, config)
        print("running inference")
        rows = bertmap_inference(
            ambig_maps_to_check=ambagious_maps,
            nonambig_maps_to_check=non_ambagious_maps,
            target_onto_prefix=target_onto_prefix,
            source_onto_prefix=source_onto_prefix,
            bertmap=bertmap,
            target_onto=target_onto,
            source_onto=src_onto,
        )
        append_prediction_tuples(rows)


def main():
    """Run the BERTMap prediction workflow."""
    args = parser.parse_args()
    ontology_paths = download_ontologies(
        target_ontology_train=args.target_ontology_train,
        source_ontology_train=args.source_ontology_train,
        source_ontologies_inference=args.source_ontologies_inference,
        target_ontologies_inference=args.target_ontologies_inference,
        ontologies_path=args.ontologies_path,
    )
    # FIXME why isn't the model variable used anywhere?
    load_bertmap(
        config=args.config,
        target_ontology_train=args.target_ontology_train,
        source_ontology_train=args.source_ontology_train,
        ontology_paths=ontology_paths,
        use_biomappings=True,
        train_model=args.train_model,
    )
    inference_across_ontologies(
        config_path=args.config,
        target_ontologies_inference=args.target_ontologies_inference,
        source_ontologies_inference=args.source_ontologies_inference,
        mappings_path=args.mappings_path,
        ontology_paths=ontology_paths,
    )


if __name__ == "__main__":
    main()
