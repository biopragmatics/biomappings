Deploying a Custom Biomappings Instance
=======================================
While it's preferred that curations using the Biomappings workflow
are contributed back to the `upstream repository <https://github.com/biopragmatics/biomappings>`_,
custom instances can be deployed, e.g., within a company that wants to curate mappings to its own
internal controlled vocabulary.

You can get started by creating the following file:

.. code-block:: python

    # biomappings_custom.py

    """A custom Biomappings script.

    - Run the web curation app with: ``python biomappings_custom.py``.
    - Run integrity tests with ``python -m pytest biomappings_custom.py``.
    """

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
