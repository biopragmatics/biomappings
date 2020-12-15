import itertools as itt
from typing import Optional

import flask
import flask_bootstrap

from biomappings.resources import load_mappings, load_predictions, write_mappings, write_predictions

app = flask.Flask(__name__)
flask_bootstrap.Bootstrap(app)


def delete_predictions_line(i):
    pass


def append_curated_line(x):
    pass


def append_negative_curated_line(x):
    pass


class Controller:
    def __init__(self):
        self._predictions = load_predictions()
        self._lookup = {
            (p['source prefix'], p['source identifier'], p['target prefix'], p['target identifier']): i
            for i, p in enumerate(self._predictions)
        }
        self._marked = {}

    def predictions(self, top=None):
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

    def lookup(self, p1, i1, p2, i2) -> Optional[int]:
        return self._lookup.get((p1, i1, p2, i2))

    def mark(self, i: int, correct: bool):
        self._marked[i] = correct

    def persist(self):
        curated_positive_lines = []
        curated_negative_lines = []

        for i, correct in self._marked.items():
            prediction = self._predictions.pop(i)
            if correct:
                curated_positive_lines.append(prediction)
            else:
                curated_negative_lines.append(prediction)

        write_mappings(itt.chain(
            load_mappings(),
            curated_positive_lines,
        ))
        write_predictions(self._predictions)


controller = Controller()


@app.route('/')
def home():
    """Serve the home page."""
    return flask.render_template('home.html', controller=controller)


@app.route('/mark/<p1>:<i1>/<p2>:<i2>/<v>')
def mark(p1, i1, p2, i2, v):
    i = controller.lookup(p1, i1, p2, i2)
    if i is None:
        flask.abort(500, f'invalid mapping: {p1}:{i1} = {p2}:{i2}')
    controller.mark(i, v.lower() == 'yup')
    controller.persist()
    return flask.redirect(flask.url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
