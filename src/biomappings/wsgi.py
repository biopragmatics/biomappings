# -*- coding: utf-8 -*-

"""Web curation interface for :mod:`biomappings`."""

import getpass
from typing import Optional

import flask
import flask_bootstrap

from biomappings.resources import append_false_mappings, append_true_mappings, load_predictions, write_predictions
from biomappings.utils import commit

app = flask.Flask(__name__)
flask_bootstrap.Bootstrap(app)


class Controller:
    """A module for interacting with the predictions and mappings."""

    def __init__(self):  # noqa: D107
        self._predictions = load_predictions()
        self._marked = {}
        self.total = 0

    def predictions(self, top: Optional[int] = None):
        """Iterate over predictions.

        :param top: If given, only iterate this number of predictions.
        """
        if top is None:
            for i, p in enumerate(self._predictions):
                if i not in self._marked:
                    yield i, p
        else:
            counter = 0
            for i, p in enumerate(self._predictions):
                if i not in self._marked:
                    counter += 1
                    yield i, p
                if counter > top:
                    break

    def mark(self, i: int, correct: bool):
        """Mark the given equivalency as correct."""
        if i not in self._marked:
            self.total += 1
        self._marked[i] = correct

    def persist(self):
        """Save the current markings to the source files."""
        curated_true_entries = []
        curated_false_entries = []

        for i, correct in self._marked.items():
            prediction = self._predictions.pop(i)
            prediction['source'] = 'web-curation'
            if correct:
                curated_true_entries.append(prediction)
            else:
                curated_false_entries.append(prediction)

        append_true_mappings(curated_true_entries)
        append_false_mappings(curated_false_entries)
        write_predictions(self._predictions)

        self._marked.clear()


controller = Controller()


@app.route('/')
def home():
    """Serve the home page."""
    return flask.render_template('home.html', controller=controller)


@app.route('/commit')
def run_commit():
    """Make a commit then redirect to the the home page."""
    commit(f'Added mappings from {getpass.getuser()}')
    controller.total = 0
    return flask.redirect(flask.url_for('home'))


@app.route('/mark/<int:line>/<value>')
def mark(line: int, value: str):
    """Mark the given line as correct or not."""
    controller.mark(line, value.lower() in {'yup', 'true', 't', 'correct', 'right', 'close enough', 'disco'})
    controller.persist()
    return flask.redirect(flask.url_for('home'))


if __name__ == '__main__':
    app.run()
