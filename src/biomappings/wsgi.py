# -*- coding: utf-8 -*-

"""Web curation interface for :mod:`biomappings`."""

import getpass
import os
from typing import Any, Iterable, Mapping, Optional, Tuple

import flask
import flask_bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

from biomappings.resources import append_false_mappings, append_true_mappings, load_predictions, write_predictions
from biomappings.utils import MiriamValidator, commit, not_main, push

app = flask.Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = os.urandom(8)
app.config['SHOW_RELATIONS'] = True
flask_bootstrap.Bootstrap(app)

# A mapping from your computer's user, returned by getuser.getpass()
KNOWN_USERS = {
    'cthoyt': '0000-0003-4423-4370',
    'ben': '0000-0001-9439-5346',
}


def _manual_source():
    known_user = KNOWN_USERS.get(getpass.getuser())
    if known_user:
        return f'orcid:{known_user}'
    return 'web'


miriam_validator = MiriamValidator()


class Controller:
    """A module for interacting with the predictions and mappings."""

    def __init__(self):  # noqa: D107
        self._predictions = load_predictions()
        self._marked = {}
        self.total_curated = 0
        self._added_mappings = []

    def predictions(
        self,
        *,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> Iterable[Tuple[int, Mapping[str, Any]]]:
        """Iterate over predictions.

        :param offset: If given, offset the iteration by this number
        :param limit: If given, only iterate this number of predictions.
        :param query: If given, show only equivalences that have it appearing as a substring in one of the fields
        :param prefix: If given, show only equivalences that have it appearing as a substring in one of the prefixes
        :yields: Pairs of positions and prediction dictionaries
        """
        it = enumerate(self._predictions)
        if query is not None:
            query = query.casefold()
            it = (
                (line, prediction)
                for line, prediction in it
                if any(
                    query in prediction[x].casefold()
                    for x in ('source identifier', 'source name', 'target identifier', 'target name')
                )
            )
        if prefix is not None:
            prefix = prefix.casefold()
            it = (
                (line, prediction)
                for line, prediction in it
                if any(
                    prefix in prediction[x].casefold()
                    for x in ('source prefix', 'target prefix')
                )
            )

        it = (
            (line, prediction)
            for line, prediction in it
            if line not in self._marked
        )
        if offset is not None:
            try:
                for _ in range(offset):
                    next(it)
            except StopIteration:
                # if next() fails, then there are no remaining entries.
                # do not pass go, do not collect 200 euro $
                return
        if limit is None:
            yield from it
        else:
            for line_prediction, _ in zip(it, range(limit)):
                yield line_prediction

    @staticmethod
    def get_curie(prefix: str, identifier: str) -> str:
        """Return CURIE for a given prefix and identifier."""
        return miriam_validator.get_curie(prefix, identifier)

    @classmethod
    def get_url(cls, prefix: str, identifier: str) -> str:
        """Return URL for a given prefix and identifier."""
        return miriam_validator.get_url(prefix, identifier)

    @property
    def total_predictions(self) -> int:
        """Return the total number of yet unmarked predictions."""
        return len(self._predictions) - len(self._marked)

    def mark(self, line: int, correct: bool) -> None:
        """Mark the given equivalency as correct.

        :param line: Position of the prediction
        :param correct: Value to mark the prediction with
        """
        if line not in self._marked:
            self.total_curated += 1
        self._marked[line] = correct

    def add_mapping(
        self,
        source_prefix: str,
        source_id: str,
        source_name: str,
        target_prefix: str,
        target_id: str,
        target_name: str,
    ) -> None:
        """Add manually curated new mappings."""
        try:
            miriam_validator.check_valid_prefix_id(source_prefix, source_id)
        except ValueError as e:
            flask.flash(
                f'Problem with source CURIE {source_prefix}:{source_id}: {e.__class__.__name__}',
                category='warning',
            )
            return

        try:
            miriam_validator.check_valid_prefix_id(target_prefix, target_id)
        except ValueError as e:
            flask.flash(
                f'Problem with target CURIE {target_prefix}:{target_id}: {e.__class__.__name__}',
                category='warning',
            )
            return

        self._added_mappings.append({
            'source prefix': source_prefix,
            'source identifier': source_id,
            'source name': source_name,
            'relation': 'skos:exactMatch',
            'target prefix': target_prefix,
            'target identifier': target_id,
            'target name': target_name,
            'source': _manual_source(),
            'type': 'manual',
        })
        self.total_curated += 1

    def persist(self):
        """Save the current markings to the source files."""
        curated_true_entries = []
        curated_false_entries = []

        for line, correct in sorted(self._marked.items(), reverse=True):
            prediction = self._predictions.pop(line)
            prediction['source'] = _manual_source()
            prediction['type'] = 'manually_reviewed'
            if correct:
                curated_true_entries.append(prediction)
            else:
                curated_false_entries.append(prediction)

        append_true_mappings(curated_true_entries)
        append_false_mappings(curated_false_entries)
        write_predictions(self._predictions)
        self._marked.clear()

        # Now add manually curated mappings
        append_true_mappings(self._added_mappings)
        self._added_mappings = []


controller = Controller()


class MappingForm(FlaskForm):
    """Form for entering new mappings."""

    source_prefix = StringField('Source Prefix', id='source_prefix')
    source_id = StringField('Source ID', id='source_id')
    source_name = StringField('Source Name', id='source_name')
    target_prefix = StringField('Target Prefix', id='target_prefix')
    target_id = StringField('Target ID', id='target_id')
    target_name = StringField('Target Name', id='target_name')
    submit = SubmitField('Add')


@app.route('/')
def home():
    """Serve the home page."""
    form = MappingForm()
    limit = flask.request.args.get('limit', type=int, default=10)
    offset = flask.request.args.get('offset', type=int, default=0)
    query = flask.request.args.get('query')
    prefix = flask.request.args.get('prefix')
    show_relations = app.config['SHOW_RELATIONS']
    return flask.render_template(
        'home.html',
        controller=controller,
        form=form,
        limit=limit,
        offset=offset,
        query=query,
        prefix=prefix,
        show_relations=show_relations,
    )


@app.route('/add_mapping', methods=['POST'])
def add_mapping():
    """Add a new mapping manually."""
    form = MappingForm()
    if form.is_submitted():
        controller.add_mapping(
            form.data['source_prefix'], form.data['source_id'], form.data['source_name'],
            form.data['target_prefix'], form.data['target_id'], form.data['target_name'],
        )
        controller.persist()
    else:
        flask.flash('missing form data', category='warning')
    return _go_home()


@app.route('/commit')
def run_commit():
    """Make a commit then redirect to the the home page."""
    commit(
        f'Curated {controller.total_curated} mapping{"s" if controller.total_curated > 1 else ""}'
        f' ({getpass.getuser()})',
    )
    if not_main():
        push()
    controller.total_curated = 0
    return _go_home()


@app.route('/mark/<int:line>/<value>')
def mark(line: int, value: str):
    """Mark the given line as correct or not."""
    controller.mark(line, value.lower() in {'yup', 'true', 't', 'correct', 'right', 'close enough', 'disco'})
    controller.persist()
    return _go_home()


def _go_home():
    return flask.redirect(flask.url_for(
        'home',
        limit=flask.request.args.get('limit', type=int),
        offset=flask.request.args.get('offset', type=int),
        query=flask.request.args.get('query'),
        prefix=flask.request.args.get('prefix'),
        show_relations=app.config['SHOW_RELATIONS'],
    ))


if __name__ == '__main__':
    app.run()
