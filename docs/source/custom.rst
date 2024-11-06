Deploying a Custom Biomappings Instance
=======================================
While it's preferred that curations using the Biomappings workflow
are contributed back to the `upstream repository <https://github.com/biopragmatics/biomappings>`_,
custom instances can be deployed, e.g., within a company that wants to curate mappings to its own
internal controlled vocabulary.

You can get started by creating a file called ``biomappings_custom.py``. You can name this file whatever
you want, just make sure to update the names in the various parts of the tutorial:

.. code-block:: python

    # biomappings_custom.py

    from pathlib import Path

    from biomappings.testing import PathIntegrityTestCase
    from biomappings.wsgi import get_app

    HERE = Path(__file__).parent.resolve()

    PREDICTIONS = HERE.joinpath("predictions.tsv")
    POSITIVES = HERE.joinpath("positive.tsv")
    NEGATIVES = HERE.joinpath("negative.tsv")
    UNSURE = HERE.joinpath("unsure.tsv")


    class TestCustom(PathIntegrityTestCase):
        """A custom test case for integrity."""

        predictions_path = PREDICTIONS
        positives_path = POSITIVES
        negatives_path = NEGATIVES
        unsure_path = UNSURE


    def ensure_example_predictions():
        """Ensure that there are some predictions for use."""
        if PREDICTIONS.is_file():
            return
        from random import Random
        from biomappings.resources import load_predictions, write_predictions

        mappings = load_predictions()
        Random(0).shuffle(mappings)
        write_predictions(mappings[:100], path=PREDICTIONS)


    def main():
        """Run a custom Biomappings curation service."""
        ensure_example_predictions()

        app = get_app(
            predictions_path=PREDICTIONS,
            positives_path=POSITIVES,
            negatives_path=NEGATIVES,
            unsure_path=UNSURE,
        )
        app.run()


    if __name__ == "__main__":
        main()

Running the Curation Interface
------------------------------
The curation app can be run by installing Biomappings and invoking the script directly:

.. code-block::

    python -m pip install biomappings[web]
    python python biomappings_custom.py


Running Tests
-------------
Biomappings implements a generic testing suite inside :class:`biomappings.testing.PathIntegrityTestCase`,
which itself is based on :class:`unittest.TestCase` and is paremetrized
by the paths to the curation files.

This means that this file can also be run by any test runnier that can discover test cases such
as :class:`unittest` itself, :mod:`pytest`, or others. Therefore you can run the tests with:

.. code-block::

    python -m pip install biomappings[tests]
    python -m pytest biomappings_custom.py
