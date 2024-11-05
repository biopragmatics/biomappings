import argparse
import subprocess
import os
from deeponto.align.bertmap import BERTMapPipeline, DEFAULT_CONFIG_FILE
from deeponto.onto import Ontology
import biomappings
from biomappings.resources import append_prediction_tuples
from functools import reduce
import torch
from itertools import product
from huggingface_hub import snapshot_download

parser = argparse.ArgumentParser(description="Train BERTMap Model")
parser.add_argument("--config", default=DEFAULT_CONFIG_FILE, help="Path to Config File")
parser.add_argument(
    "--sourceOntologyTrain",
    default="MESH",
    help="Ontologies to match as source during training",
)
parser.add_argument(
    "--targetOntologyTrain",
    default="DOID",
    help="Ontologies to match as target during training",
)
parser.add_argument(
    "--sourceOntologiesInference",
    nargs="+",
    default=["MESH2024"],
    help="Ontologies to match as source during inference",
)
parser.add_argument(
    "--targetOntologiesInference",
    nargs="+",
    default=[ "DOID", "CHEBI", "HGNC", "GO"],
    help="Ontologies to match as target during inference",
)
parser.add_argument(
    "--ontologiesPath", default="resources", help="Directory with ontology files"
)
parser.add_argument(
    "--mappingsPath",
    default="mesh_ambig_mappings.tsv",
    help="Path with mappings to be evaluated with BERRTMap",
)
parser.add_argument(
    "--trainModel",
    action="store_true",
    help="If present will locally train a model otherwise will pull from hugging face.",
)
parser.add_argument("--resultsPath", default="results/", help="Path to write results")
ENDPOINTS = {
    "GO": "https://purl.obolibrary.org/obo/go.owl",
    "CHEBI": "https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl",
    "DOID": "https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/refs/heads/main/src/ontology/doid.owl",
    "HGNC": "https://storage.googleapis.com/public-download-files/hgnc/owl/owl/hgnc.owl",
    "MESH": "https://data.bioontology.org/ontologies/RH-MESH/submissions/3/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  ## SMALLER 2014 VERSION
    "MESH2024": "https://data.bioontology.org/ontologies/MESH/submissions/28/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb",  ## Larger 2024 version in TTL format
}

sourcePrefixIRIMaps = {
    "mesh": lambda x: "http://phenomebrowser.net/ontologies/mesh/mesh.owl#" + x,
    "mesh2024": lambda x: "http://purl.bioontology.org/ontology/MESH/" + x,
    "doid": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "hgnc": lambda x: "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:"
    + x,
    "chebi": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
    "go": lambda x: "http://purl.obolibrary.org/obo/" + x.replace(":", "_"),
}
IRIsourcePrefixMaps = {
    "mesh": lambda x: x.strip("http://phenomebrowser.net/ontologies/mesh/mesh.owl#"),
    "mesh2024": lambda x: x.strip("http://purl.bioontology.org/ontology/MESH/"),
    "doid": lambda x: x.strip("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "hgnc": lambda x: x.strip(
        "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/"
    ),
    "chebi": lambda x: x.strip("http://purl.obolibrary.org/obo/").replace("_", ":"),
    "go": lambda x: x.strip("http://purl.obolibrary.org/obo/").replace("_", ":"),
}


## pull
def DownloadOntologies(
    targetOntologyTrain: str,
    sourceOntologyTrain: str,
    sourceOntologiesInference: list,
    targetOntologiesInference: list,
    ontologiesPath: str,
):
    os.makedirs(ontologiesPath, exist_ok=True)
    ontology_paths = {}
    for ontology in (
        [targetOntologyTrain, sourceOntologyTrain]
        + sourceOntologiesInference
        + targetOntologiesInference
    ):
        ext = ".ttl" if ontology.upper() == "MESH2024" else ".owl"
        ontology_path = os.path.join(ontologiesPath, ontology.lower() + ext)
        ontology_paths[ontology.lower()] = ontology_path
        if not os.path.isfile(ontology_path):
            print("Downloading {0}".format(ontology))
            cmd = "wget -O {0} {1}".format(ontology_path, ENDPOINTS[ontology.upper()])
            subprocess.run(cmd, shell=True)
        else:
            print("found {0} at {1}".format(ontology.lower(), ontology_path))
    return ontology_paths


## train
def LoadBERTMAP(
    config: str,
    targetOntologyTrain: str,
    sourceOntologyTrain: str,
    ontology_paths: dict,
    useBiomappings: bool = False,
    trainModel: bool = False,
):
    config = BERTMapPipeline.load_bertmap_config(config)

    if useBiomappings:
        print("-" * 100)
        print("generating known mappings")
        config.known_mappings = SaveKnownMaps(
            targetOntologyTrain=targetOntologyTrain,
            sourceOntologyTrain=sourceOntologyTrain,
            mappingsPath="knownMaps",
        )
    print("-" * 100)
    print("Using config: \n{0}".format(config))
    print("-" * 100)
    if not trainModel:
        config.global_matching.enabled = False
        if not os.path.isdir("bertmap"):
            print("downloading model from hugging face")
            snapshot_download(
                repo_id="buzgalbraith/BERTMAP-BioMappings", local_dir="./"
            )
        else:
            print("Model found at bertmap")
    src_onto = Ontology(ontology_paths[sourceOntologyTrain.lower()])
    target_onto = Ontology(ontology_paths[targetOntologyTrain.lower()])     
    return BERTMapPipeline(src_onto, target_onto, config)

def SaveKnownMaps(
    targetOntologyTrain: str, sourceOntologyTrain: str, mappingsPath="knownMaps"
):

    ## for now only take curated mappings as true
    true_mappings = biomappings.load_mappings()

    onto_filter = lambda x: (
        x["target prefix"].lower() == targetOntologyTrain.lower()
    ) & (x["source prefix"].lower() == sourceOntologyTrain.lower())
    iri_map = lambda x: (
        sourcePrefixIRIMaps[sourceOntologyTrain.lower()](x["source identifier"])
        + "\t"
        + sourcePrefixIRIMaps[targetOntologyTrain.lower()](x["target identifier"])
        + "\t1.0\n"
    )
    known_maps = map(iri_map, filter(onto_filter, true_mappings))

    os.makedirs(mappingsPath, exist_ok=True)
    KnownmapsPath = os.path.join(
        mappingsPath,
        sourceOntologyTrain.lower() + "-" + targetOntologyTrain.lower() + ".tsv",
    )

    f = open(KnownmapsPath, mode="w")
    f.write("SrcEntity\tTgtEntity\tScore\n")
    f.writelines(known_maps)
    f.close()
    return KnownmapsPath


## inference
def strip_digits(x):
    return "".join(filter(lambda x: not x.isdigit(), x))


def AmbagiousInference(
    MapsToCheck,
    resultsPath: str,
    targetOnto: str,
    sourceOnto: str,
    bertmap,
    target_onto,
    source_onto,
):
    target_name = targetOnto.lower()
    source_name = sourceOnto.lower()
    os.makedirs(resultsPath, exist_ok=True)
    save_path = os.path.join(
        resultsPath, "{0}_to_{1}_Ambagious.tsv".format(target_name, source_name)
    )
    f = open(save_path, mode="w")
    f.write(
        "SRC_IRI\tSRC_NAME\tTARGET_IRI\tTarget_NAME\tBERTMAP_SCORE\tBERTMAPLT_SCORE\tSRC_TAGS\tTARGET_SCORE\n"
    )
    for src_class_iri, src_name, tgt_class_iri, target_name in MapsToCheck:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]
        class_annotation_pairs = list(
            product(src_class_annotations, tgt_class_annotations)
        )
        synonym_scores = bertmap.bert_synonym_classifier.predict(class_annotation_pairs)
        # only one element tensor is able to be extracted as a scalar by .item()
        bert_score = float(torch.mean(synonym_scores).item())
        bertmaplt_score = bertmap.mapping_predictor.edit_similarity_mapping_score(
            src_class_annotations, tgt_class_annotations
        )
        ## check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_name).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_name).upper() in x
        ]
        ## if it is mapped at all that means the mapping is either already done or wrong so just skip
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        else:
            f.write(
                "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n".format(
                    src_class_iri,
                    src_name,
                    tgt_class_iri,
                    target_name,
                    bert_score,
                    bertmaplt_score,
                    src_class_annotations,
                    tgt_class_annotations,
                )
            )
    f.close()


def NonAmbagiousInference(
    MapsToCheck,
    resultsPath: str,
    targetOnto: str,
    sourceOnto: str,
    bertmap,
    target_onto,
    source_onto,
):
    target_name = targetOnto.lower()
    source_name = sourceOnto.lower()
    os.makedirs(resultsPath, exist_ok=True)
    save_path = os.path.join(
        resultsPath, "{0}_to_{1}_NonAmbagious.tsv".format(source_name, target_name)
    )
    f = open(save_path, mode="w")
    f.write(
        "SRC_IRI\tSRC_NAME\tTARGET_IRI\tTarget_NAME\tBERTMAP_SCORE\tBERTMAPLT_SCORE\tSRC_TAGS\tTARGET_SCORE\n"
    )
    for src_class_iri, src_name, tgt_class_iri, target_name in MapsToCheck:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]
        bertmap_score = bertmap.mapping_predictor.bert_mapping_score(
            src_class_annotations, tgt_class_annotations
        )
        bertmaplt_score = bertmap.mapping_predictor.edit_similarity_mapping_score(
            src_class_annotations, tgt_class_annotations
        )
        ## check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_name).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_name).upper() in x
        ]
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        else:
            f.write(
                "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n".format(
                    src_class_iri,
                    src_name,
                    tgt_class_iri,
                    target_name,
                    bertmap_score,
                    bertmaplt_score,
                    src_class_annotations,
                    tgt_class_annotations,
                )
            )
    f.close()


def biomappingsInference(
    ambigMapsToCheck,
    nonAmbigMapsToCheck,
    targetOnto: str,
    sourceOnto: str,
    bertmap,
    target_onto,
    source_onto,
):
    target_prefix = targetOnto.lower()
    source_prefix = sourceOnto.lower()
    ## setting constants
    relation = "skos:exactMatch"
    match_type = "semapv:SemanticSimilarityThresholdMatching"
    source = "generate_BERTMap_predictions.py"
    ## re-write this as a new lst 
    rows = []
    for src_class_iri, src_name, tgt_class_iri, target_name in nonAmbigMapsToCheck:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]
        conf = bertmap.mapping_predictor.bert_mapping_score(
            src_class_annotations, tgt_class_annotations
        )

        source_identifier = IRIsourcePrefixMaps[source_prefix](src_class_iri)
        target_identifier = IRIsourcePrefixMaps[target_prefix](tgt_class_iri)
        ## check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_prefix).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_prefix).upper() in x
        ]
        ## if it is mapped at all that means the mapping is either already done or wrong so just skip
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        elif conf < 0.5:
            pass
        else:
            
            rows.append(biomappings.PredictionTuple(strip_digits(source_prefix),
                    source_identifier,
                    src_name,
                    relation,
                    strip_digits(target_prefix),
                    target_identifier,
                    target_name,
                    match_type,
                    conf,
                    source))
    for src_class_iri, src_name, tgt_class_iri, target_name in ambigMapsToCheck:
        src_class_annotations = bertmap.src_annotation_index[src_class_iri]
        tgt_class_annotations = bertmap.tgt_annotation_index[tgt_class_iri]

        class_annotation_pairs = list(
            product(src_class_annotations, tgt_class_annotations)
        )
        synonym_scores = bertmap.bert_synonym_classifier.predict(class_annotation_pairs)
        # only one element tensor is able to be extracted as a scalar by .item()
        conf = float(torch.mean(synonym_scores).item())
        source_identifier = IRIsourcePrefixMaps[source_prefix](src_class_iri)
        target_identifier = IRIsourcePrefixMaps[target_prefix](tgt_class_iri)
        ## check if in provided map
        target_annotations = target_onto.get_annotations(tgt_class_iri)
        target_known_maps = [
            x for x in target_annotations if strip_digits(source_prefix).upper() in x
        ]
        source_annotations = source_onto.get_annotations(src_class_iri)
        source_known_maps = [
            x for x in source_annotations if strip_digits(target_prefix).upper() in x
        ]
        ## if it is mapped at all that means the mapping is either already done or wrong so just skip
        if len(target_known_maps) > 0 or len(source_known_maps) > 0:
            pass
        elif len(src_class_annotations) == 0 or len(tgt_class_annotations) == 0:
            pass
        elif conf < 0.5:
            pass
        else:            
            rows.append(biomappings.PredictionTuple(strip_digits(source_prefix),
                    source_identifier,
                    src_name,
                    relation,
                    strip_digits(target_prefix),
                    target_identifier,
                    target_name,
                    match_type,
                    conf,
                    source))
    return rows

def GetNovelMappings(targetOnto: str, sourceOnto: str, mapsPath: str):
    ## get all potential mappings
    maps_to_check = getMapsToEvaluate(
        targetOnto=targetOnto, sourceOnto=sourceOnto, mapsPath=mapsPath
    )
    ## filter out those already in biomappings
    maps_not_in_biomappings = filterForBiomappings(
        targetOnto=targetOnto, sourceOnto=sourceOnto, maps_to_check=maps_to_check
    )
    # break the remaining into an ambagious an non-ambagious set
    ambagious_maps, non_ambagious_maps = check_ambagious_maps(
        maps_not_in_biomappings=maps_not_in_biomappings
    )
    return ambagious_maps, non_ambagious_maps


def getMapsToEvaluate(targetOnto: str, sourceOnto: str, mapsPath: str):
    target_name = targetOnto.lower()
    source_name = sourceOnto.lower()
    mappings = open(mapsPath).readlines()
    split_map = lambda x: x.split("\t")
    onto_filter = lambda x: (x[0].lower() == strip_digits(source_name)) & (
        x[3].lower() == strip_digits(target_name)
    )
    iri_map = lambda x: (
        sourcePrefixIRIMaps[source_name](x[1]),
        x[2],
        sourcePrefixIRIMaps[target_name](x[4]),
        x[5].strip(),
    )

    maps_to_check = map(iri_map, filter(onto_filter, map(split_map, mappings)))
    return maps_to_check


def filterForBiomappings(targetOnto: str, sourceOnto: str, maps_to_check):
    target_name = targetOnto.lower()
    source_name = sourceOnto.lower()
    biomappings_maps = (
        biomappings.load_mappings()
        + biomappings.load_false_mappings()
        + biomappings.load_predictions()
    )
    onto_filter = lambda x: (
        x["target prefix"].lower() == strip_digits(target_name)
    ) & (x["source prefix"].lower() == strip_digits(source_name))
    iri_map = lambda x: (
        sourcePrefixIRIMaps[target_name](x["target identifier"]),
        sourcePrefixIRIMaps[source_name](x["source identifier"]),
    )
    biomappping_maps_to_check_against = set(
        map(iri_map, filter(onto_filter, biomappings_maps))
    )
    known_filter = lambda x: x not in biomappping_maps_to_check_against
    maps_not_in_biomappings = filter(known_filter, maps_to_check)
    return maps_not_in_biomappings


def check_ambagious_maps(maps_not_in_biomappings):
    maps_not_in_biomappings = list(maps_not_in_biomappings)
    value_counts = reduce(
        lambda acc, item: {
            **acc,
            **{
                f: {**acc.get(f, {}), item[f]: acc.get(f, {}).get(item[f], 0) + 1}
                for f in [0, 2]
            },
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


def BERTMapInference(
    config: str,
    targetOnto: str,
    sourceOnto: str,
    mapsPath: str,
    resultsPath: str,
    ontology_paths: dict,
    forBiomappings: bool = True,
):
    ## load mappings to evaluate
    print("Filtering Mappings")
    ambagious_maps, non_ambagious_maps = GetNovelMappings(
        targetOnto=targetOnto, sourceOnto=sourceOnto, mapsPath=mapsPath
    )
    print("loading ontologies")
    src_onto = Ontology(ontology_paths[sourceOnto.lower()])
    target_onto = Ontology(ontology_paths[targetOnto.lower()])
    config = BERTMapPipeline.load_bertmap_config(config)
    config.global_matching.enabled = False
    print("loading model")
    bertmap = BERTMapPipeline(src_onto, target_onto, config)
    if not forBiomappings:
        print("running inference on Non Ambagious mappings")
        NonAmbagiousInference(
            MapsToCheck=non_ambagious_maps,
            resultsPath=resultsPath,
            targetOnto=targetOnto,
            sourceOnto=sourceOnto,
            bertmap=bertmap,
            target_onto=target_onto,
            source_onto=src_onto,
        )
        print("running inference on Ambagious mappings")
        AmbagiousInference(
            MapsToCheck=ambagious_maps,
            resultsPath=resultsPath,
            targetOnto=targetOnto,
            sourceOnto=sourceOnto,
            bertmap=bertmap,
            target_onto=target_onto,
            source_onto=src_onto,
        )
    else:
        print("biomappings inference")
        rows = biomappingsInference(
            ambigMapsToCheck=ambagious_maps,
            nonAmbigMapsToCheck=non_ambagious_maps,
            targetOnto=targetOnto,
            sourceOnto=sourceOnto,
            bertmap=bertmap,
            target_onto=target_onto,
            source_onto=src_onto,
        )
        append_prediction_tuples(rows)

def inferenceAcrossOntologies(
    config: str,
    targetOntologiesInference: list,
    sourceOntologiesInference: list,
    mappingsPath: str,
    resultsPath: str,
    ontology_paths: dict,
    forBiomappings: bool = True,
):
    for targetOnto, sourceOnto in product(
        targetOntologiesInference, sourceOntologiesInference
    ):
        BERTMapInference(
            config=config,
            targetOnto=targetOnto,
            sourceOnto=sourceOnto,
            mapsPath=mappingsPath,
            resultsPath=resultsPath,
            ontology_paths=ontology_paths,
            forBiomappings=forBiomappings,
        )


if __name__ == "__main__":
    args = parser.parse_args()
    ontology_paths = DownloadOntologies(
        targetOntologyTrain=args.targetOntologyTrain,
        sourceOntologyTrain=args.sourceOntologyTrain,
        sourceOntologiesInference=args.sourceOntologiesInference,
        targetOntologiesInference=args.targetOntologiesInference,
        ontologiesPath=args.ontologiesPath,
    )
    model = LoadBERTMAP(
        config=args.config,
        targetOntologyTrain=args.targetOntologyTrain,
        sourceOntologyTrain=args.sourceOntologyTrain,
        ontology_paths=ontology_paths,
        useBiomappings=True,
        trainModel=args.trainModel,
    )
    inferenceAcrossOntologies(
        config=args.config,
        targetOntologiesInference=args.targetOntologiesInference,
        sourceOntologiesInference=args.sourceOntologiesInference,
        mappingsPath=args.mappingsPath,
        resultsPath=args.resultsPath,
        ontology_paths=ontology_paths,
        forBiomappings=True,
    )
