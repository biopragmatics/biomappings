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

# A mapping from your computer's user, returned by getuser.getpass()
KNOWN_USERS = {
    'cthoyt': '0000-0003-4423-4370',
    'ben': '0000-0001-9439-5346',
}


class Controller:
    """A module for interacting with the predictions and mappings."""

    def __init__(self):  # noqa: D107
        self._predictions = load_predictions()
        self._marked = {}
        self.total = 0

    def predictions(self, *, offset: Optional[int] = None, limit: Optional[int] = None):
        """Iterate over predictions.

        :param limit: If given, only iterate this number of predictions.
        """
        it = (
            (i, p)
            for i, p in enumerate(self._predictions)
            if i not in self._marked
        )
        if offset is not None:
            for _ in range(offset):
                next(it)
        if limit is None:
            yield from it
        else:
            for x, _ in zip(it, range(limit)):
                yield x

    def mark(self, i: int, correct: bool):
        """Mark the given equivalency as correct."""
        if i not in self._marked:
            self.total += 1
        self._marked[i] = correct

    def persist(self):
        """Save the current markings to the source files."""
        curated_true_entries = []
        curated_false_entries = []

        for i, correct in sorted(self._marked.items(), reverse=True):
            prediction = self._predictions.pop(i)
            known_user = KNOWN_USERS.get(getpass.getuser())
            prediction['source'] = f'orcid:{known_user}' if known_user else 'web'
            prediction['type'] = 'manually_reviewed'
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
    limit = flask.request.args.get('limit', type=int, default=10)
    offset = flask.request.args.get('offset', type=int, default=0)
    return flask.render_template(
        'home.html',
        controller=controller,
        limit=limit,
        offset=offset,
    )


@app.route('/commit')
def run_commit():
    """Make a commit then redirect to the the home page."""
    commit(f'Curated {controller.total} mappings ({getpass.getuser()})')
    controller.total = 0
    return flask.redirect(flask.url_for('home'))


@app.route('/mark/<int:line>/<value>')
def mark(line: int, value: str):
    """Mark the given line as correct or not."""
    controller.mark(line, value.lower() in {'yup', 'true', 't', 'correct', 'right', 'close enough', 'disco'})
    controller.persist()
    return flask.redirect(flask.url_for(
        'home',
        limit=flask.request.args.get('limit', type=int),
        offset=flask.request.args.get('offset', type=int),
    ))


if __name__ == '__main__':
    app.run()
