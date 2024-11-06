Adding Predictions
==================
The Biomappings workflow is generic and allows for any mapping prediction workflow to be used.
You can see several examples in the `scripts/ <https://github.com/biopragmatics/biomappings/tree/master/scripts>`_
directory of the canonical Biomappings repository.

Most are built using a lexical matching workflow based on `Gilda <https://github.com/gyorilab/gilda>`_.
This approach is fast, simple, and interpretable since it relies on the labels and synonyms for
concepts appearing in ontologies and other controlled vocabularies (e.g., MeSH). It takes
the following steps:

1. Index labels and synonyms from entities in various controlled vocabularies (e.g., MeSH, ChEBI)
2. Filter out concepts that have mappings in primary source or third-party mappings in Biomappings
3. Perform all-by-all comparison of indexes for each controlled vocabulary
4. Filter out mappings that have been previously marked as incorrect (e.g.,
   avoid `zombie mappings <https://doi.org/10.32388/DYZ5J3>`_)

Examples
--------
The following examples have already been used to predict mappings


1. `generate_mondo_mappings.py <https://github.com/biopragmatics/biomappings/blob/master/scripts/generate_mondo_mappings.py>`_
   uses a pre-configured workflow based on the :mod:`gilda` and :mod:`pyobo` integrations
2. `generate_ccle_mappings.py <https://github.com/biopragmatics/biomappings/blob/master/scripts/generate_ccle_mappings.py>`_
   uses same pre-configured workflow with a custom filter to include additional mappings
3. `generate_cl_mesh_mappings <https://github.com/biopragmatics/biomappings/blob/master/scripts/generate_cl_mesh_mappings.py>`_
   implements a fully custom matching workflow, also built on Gilda (in case you want to roll your own)
4. `generate_mesh_uniprot_mappings <https://github.com/biopragmatics/biomappings/blob/master/scripts/generate_mesh_uniprot_mappings.py>`_
   uses rule-based matching between MeSH and UniProt proteins that relies on the fact that the MeSH terms were
   generated from UniProt names.
5. `generate_wikipathways_orthologs <https://github.com/biopragmatics/biomappings/blob/master/scripts/generate_wikipathways_orthologs.py>`_
   uses a rule-based method for matching orthologous pathways in WikiPathways that relies on the fact that the names
   are procedurally generated with a certain template

We also have a work-in-progress example using :mod:`pykeen` for generating mappings based on knowledge graph embeddings
(both in the transductive and inductive setting).

.. warning::

    For people coming from the machine learning domain, there may be a desire to over-engineer matching methods.
    It actually turns out to be the case that lexical matching gets 80-90% of the job done most of the time
    when there are reasonable lexicalizations available. Resist the urge to make matching workflows overcomplicated!

Clone the Repository
--------------------
1. Fork the `upstream Biomappings repository <https://github.com/biopragmatics/biomappings>`_
2. Clone your fork, make a branch, and install it. Note that we're including the ``web`` and ``gilda`` extras, so we
   can run the curation interface locally as well as get all the tools we need for generating predictions.

    .. code-block::

       git clone https://github.com/<your namespace>/biomappings
       cd biomappings
       git checkout -b tutorial
       python -m pip install -e .[web,gilda]

3. Go into the `scripts/` directory

    .. code-block::

        cd scripts/

4. Make a Python file for predictions. In this example, we're going to generate mappings between the ChEBI ontology and
   Medical Subject Headings (MeSH).

    .. code-block::

       touch generate_chebi_mesh_example.py

Preparing the Mapping Script
----------------------------
Biomappings has a lot of first-party support for Gilda prediction workflows, so generating mappings
can be quite easy using a pre-defined workflow. Open your newly created ``generate_chebi_mesh_example.py``
in your favorite editor and add the following four lines:

.. code-block:: python

    # generate_chebi_mesh_example.py

    from biomappings.gilda_utils import append_gilda_predictions
    from biomappings.utils import get_script_url

    provenance = get_script_url(__file__)
    append_gilda_predictions("chebi", "mesh", provenance=provenance)

All generated mappings in Biomappings should point to the script that generated
them. :func:`biomappings.utils.get_script_url` is called in a sneaky way with
``__file__`` to get the name of the to generate a URI string , assuming that this
is in the ``scripts/`` directory of the Biomappings repository.

The hard work is done by :func:`biomappings.gilda_utils.append_gilda_predictions` when called
with ChEBI as the source prefix and MeSH as the target prefix along with the previously generated
provenance URI string. Under the hood, this does the following:

1. Looks up the names and synonyms for concepts in ChEBI and MeSH using :mod:`pyobo`, a
   unified interface for accessing ontologies and non-ontology controlled vocabularies (such as MeSH)
2. Runs the algorithm described above
3. Appends the predictions on to the local predictions TSV file

Finishing Up
------------
Execute the script from your command line and the predictions will be added to your local Biomappings cache.

.. code-block::

    python generate_chebi_mesh_example.py

This is a good time to review the changes and make a commit using

.. code-block::

    git add src/biomappings/resources/predictions.tsv
    git commit -m "Add predictions from ChEBI to MeSH"
    git push

Finally, you can run the web curation interface like normal and search for your new predictions to curate!

.. code-block::

    biomappings web

Custom Predictions File
-----------------------
While it's preferred that predictions generated using the Biomappings workflow
are contributed back to the `upstream repository <https://github.com/biopragmatics/biomappings>`_,
custom instances can be deployed, e.g., within a company that wants to curate mappings to its own
internal controlled vocabulary.

In order to accomplish this, you can use the ``path`` argument to
:func:`biomappings.gilda_utils.append_gilda_predictions`. By modifying the previous example,
we can store the predictions in a file in the same directory as the script called ``predictions.tsv``.

.. code-block:: python

    # generate_chebi_mesh_example.py

    from pathlib import Path

    from biomappings.gilda_utils import append_gilda_predictions
    from biomappings.utils import get_script_url

    HERE = Path(__file__).parent.resolve()
    PREDICTIONS_PATH = HERE.joinpath("predictions.tsv")

    provenance = get_script_url(__file__)
    append_gilda_predictions("chebi", "mesh", provenance=provenance, path=PREDICTIONS_PATH)
