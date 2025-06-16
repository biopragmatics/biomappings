"""Web curation interface for :mod:`biomappings`."""

from __future__ import annotations

import getpass
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, cast, get_args

import flask
import flask_bootstrap
import pydantic
import werkzeug
from bioregistry import NormalizedNamableReference, NormalizedNamedReference
from curies import ReferenceTuple
from flask import current_app
from flask_wtf import FlaskForm
from pydantic import BaseModel
from typing_extensions import TypeAlias
from werkzeug.local import LocalProxy
from wtforms import StringField, SubmitField

from biomappings.resources import (
    MappingTuple,
    append_false_mappings,
    append_true_mappings,
    append_unsure_mappings,
    load_curators,
    load_predictions,
    write_predictions,
)
from biomappings.utils import commit, get_branch, not_main, push

Mark: TypeAlias = Literal["correct", "incorrect", "unsure", "broad", "narrow"]
MARKS: set[Mark] = set(get_args(Mark))


class State(BaseModel):
    """Contains the state for queries to the curation app."""

    limit: int | None = 10
    offset: int | None = 0
    query: str | None = None
    source_query: str | None = None
    source_prefix: str | None = None
    target_query: str | None = None
    target_prefix: str | None = None
    provenance: str | None = None
    prefix: str | None = None
    sort: str | None = None
    same_text: bool | None = None
    show_relations: bool = True
    show_lines: bool = False

    @classmethod
    def from_flask_globals(cls) -> State:
        """Get the state from the flask current request."""
        return State(
            limit=flask.request.args.get("limit", type=int, default=10),
            offset=flask.request.args.get("offset", type=int, default=0),
            query=flask.request.args.get("query"),
            source_query=flask.request.args.get("source_query"),
            source_prefix=flask.request.args.get("source_prefix"),
            target_query=flask.request.args.get("target_query"),
            target_prefix=flask.request.args.get("target_prefix"),
            provenance=flask.request.args.get("provenance"),
            prefix=flask.request.args.get("prefix"),
            sort=flask.request.args.get("sort"),
            same_text=_get_bool_arg("same_text"),
            show_relations=_get_bool_arg("show_relations") or current_app.config["SHOW_RELATIONS"],
            show_lines=_get_bool_arg("show_lines") or current_app.config["SHOW_LINES"],
        )


def _get_bool_arg(name: str) -> bool | None:
    value: str | None = flask.request.args.get(name, type=str)
    if value is not None:
        return value.lower() in {"true", "t"}
    return None


def url_for_state(endpoint, state: State, **kwargs: Any) -> str:
    """Get the URL for an endpoint based on the state class."""
    vv = state.model_dump(exclude_none=True, exclude_defaults=True)
    vv.update(kwargs)  # make sure stuff explicitly set overrides state
    return flask.url_for(endpoint, **vv)


def get_app(
    target_references: Iterable[ReferenceTuple] | None = None,
    predictions_path: Path | None = None,
    positives_path: Path | None = None,
    negatives_path: Path | None = None,
    unsure_path: Path | None = None,
    controller: Controller | None = None,
) -> flask.Flask:
    """Get a curation flask app."""
    app_ = flask.Flask(__name__)
    app_.config["WTF_CSRF_ENABLED"] = False
    app_.config["SECRET_KEY"] = os.urandom(8)
    app_.config["SHOW_RELATIONS"] = True
    app_.config["SHOW_LINES"] = False
    if controller is None:
        controller = Controller(
            target_references=target_references,
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
        )
    if not controller._predictions and predictions_path is not None:
        raise RuntimeError(f"There are no predictions to curate in {predictions_path}")
    app_.config["controller"] = controller
    flask_bootstrap.Bootstrap4(app_)
    app_.register_blueprint(blueprint)
    app_.jinja_env.globals.update(
        controller=controller,
        url_for_state=url_for_state,
    )
    return app_


# A mapping from your computer's user, returned by getuser.getpass()
KNOWN_USERS: dict[str, NormalizedNamedReference] = load_curators()


# FIXME this will throw an error for new user, so ask them their ORCID and name if it's missing
def _manual_source() -> NormalizedNamableReference:
    return KNOWN_USERS[getpass.getuser()]


class Controller:
    """A module for interacting with the predictions and mappings."""

    def __init__(
        self,
        *,
        target_references: Iterable[NormalizedNamableReference] | None = None,
        predictions_path: Path | None = None,
        positives_path: Path | None = None,
        negatives_path: Path | None = None,
        unsure_path: Path | None = None,
    ) -> None:
        """Instantiate the web controller.

        :param target_references:
            Pairs of prefix, local unique identifiers that are the target
            of curation. If this is given, pre-filters will be made before on predictions
            to only show ones where either the source or target appears in this set
        :param predictions_path: A custom predictions file to curate from
        :param positives_path: A custom positives file to curate to
        :param negatives_path: A custom negatives file to curate to
        :param unsure_path: A custom unsure file to curate to
        """
        self.predictions_path = predictions_path
        self._predictions = load_predictions(path=self.predictions_path)

        self.positives_path = positives_path
        self.negatives_path = negatives_path
        self.unsure_path = unsure_path

        self._marked: dict[int, Mark] = {}
        self.total_curated = 0
        self._added_mappings: list[MappingTuple] = []
        self.target_references = set(target_references or [])

    def predictions_from_state(self, state: State) -> Iterable[tuple[int, MappingTuple]]:
        """Iterate over predictions from a state instance."""
        return self.predictions(
            offset=state.offset,
            limit=state.limit,
            query=state.query,
            source_query=state.source_query,
            source_prefix=state.source_prefix,
            target_query=state.target_query,
            target_prefix=state.target_prefix,
            prefix=state.prefix,
            sort=state.sort,
            same_text=state.same_text,
            provenance=state.provenance,
        )

    def predictions(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        query: str | None = None,
        source_query: str | None = None,
        source_prefix: str | None = None,
        target_query: str | None = None,
        target_prefix: str | None = None,
        prefix: str | None = None,
        sort: str | None = None,
        same_text: bool | None = None,
        provenance: str | None = None,
    ) -> Iterable[tuple[int, MappingTuple]]:
        """Iterate over predictions.

        :param offset: If given, offset the iteration by this number
        :param limit: If given, only iterate this number of predictions.
        :param query: If given, show only equivalences that have it appearing as a substring in one of the source
            or target fields.
        :param source_query: If given, show only equivalences that have it appearing as a substring in one of the source
            fields.
        :param source_prefix: If given, show only mappings that have it appearing in the source prefix field
        :param target_query: If given, show only equivalences that have it appearing as a substring in one of the target
            fields.
        :param target_prefix: If given, show only mappings that have it appearing in the target prefix field
        :param prefix: If given, show only equivalences that have it appearing as a substring in one of the prefixes.
        :param same_text: If true, filter to predictions with the same label
        :param sort: If "desc", sorts in descending confidence order. If "asc", sorts in increasing confidence order.
            Otherwise, do not sort.
        :param provenance: If given, filters to provenance values matching this
        :yields: Pairs of positions and prediction dictionaries
        """
        if same_text is None:
            same_text = False
        it = self._help_it_predictions(
            query=query,
            source_query=source_query,
            source_prefix=source_prefix,
            target_query=target_query,
            target_prefix=target_prefix,
            prefix=prefix,
            sort=sort,
            same_text=same_text,
            provenance=provenance,
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

    def count_predictions_from_state(self, state: State) -> int:
        """Count the number of predictions to check for the given filters."""
        return self.count_predictions(
            query=state.query,
            source_query=state.source_query,
            source_prefix=state.source_prefix,
            target_query=state.target_query,
            target_prefix=state.target_prefix,
            prefix=state.prefix,
            same_text=state.same_text,
            provenance=state.provenance,
        )

    def count_predictions(
        self,
        query: str | None = None,
        source_query: str | None = None,
        source_prefix: str | None = None,
        target_query: str | None = None,
        target_prefix: str | None = None,
        prefix: str | None = None,
        sort: str | None = None,
        same_text: bool | None = None,
        provenance: str | None = None,
    ) -> int:
        """Count the number of predictions to check for the given filters."""
        it = self._help_it_predictions(
            query=query,
            source_query=source_query,
            source_prefix=source_prefix,
            target_query=target_query,
            target_prefix=target_prefix,
            prefix=prefix,
            sort=sort,
            same_text=same_text,
            provenance=provenance,
        )
        return sum(1 for _ in it)

    def _help_it_predictions(
        self,
        query: str | None = None,
        source_query: str | None = None,
        source_prefix: str | None = None,
        target_query: str | None = None,
        target_prefix: str | None = None,
        prefix: str | None = None,
        sort: str | None = None,
        same_text: bool | None = None,
        provenance: str | None = None,
    ) -> Iterator[tuple[int, MappingTuple]]:
        it: Iterable[tuple[int, MappingTuple]] = enumerate(self._predictions)
        if self.target_references:
            it = (
                (line, p)
                for (line, p) in it
                if p.subject in self.target_references or p.object in self.target_references
            )

        if query is not None:
            it = self._help_filter(
                query,
                it,
                {
                    "subject_id",
                    "subject_label",
                    "object_id",
                    "object_label",
                    "mapping_tool",
                },
            )
        if source_prefix is not None:
            it = self._help_filter(source_prefix, it, {"subject_id"})
        if source_query is not None:
            it = self._help_filter(source_query, it, {"subject_id", "subject_label"})
        if target_query is not None:
            it = self._help_filter(target_query, it, {"object_id", "object_label"})
        if target_prefix is not None:
            it = self._help_filter(target_prefix, it, {"object_id"})
        if prefix is not None:
            it = self._help_filter(prefix, it, {"subject_id", "object_id"})
        if provenance is not None:
            it = self._help_filter(provenance, it, {"mapping_tool"})

        if sort is not None:
            if sort == "desc":
                it = iter(sorted(it, key=lambda l_p: l_p[1]["confidence"], reverse=True))
            elif sort == "asc":
                it = iter(sorted(it, key=lambda l_p: l_p[1]["confidence"], reverse=False))
            elif sort == "object":
                it = iter(sorted(it, key=lambda l_p: l_p[1]["target_id"]))
            else:
                raise ValueError

        if same_text:
            it = (
                (line, prediction)
                for line, prediction in it
                if prediction.subject.name.casefold() == prediction.object.name.casefold()
                and prediction.predicate.curie == "skos:exactMatch"
            )

        rv = ((line, prediction) for line, prediction in it if line not in self._marked)
        return rv

    @staticmethod
    def _help_filter(
        query: str, it: Iterable[tuple[int, MappingTuple]], elements: set[str]
    ) -> Iterable[tuple[int, MappingTuple]]:
        query = query.casefold()
        for line, prediction in it:
            if any(query in prediction[element].casefold() for element in elements):
                yield line, prediction

    @property
    def total_predictions(self) -> int:
        """Return the total number of yet unmarked predictions."""
        return len(self._predictions) - len(self._marked)

    def mark(self, line: int, value: Mark) -> None:
        """Mark the given equivalency as correct.

        :param line: Position of the prediction
        :param value: Value to mark the prediction with
        :raises ValueError: if an invalid value is used
        """
        if line > len(self._predictions):
            raise IndexError(
                f"given line {line} is larger than the number of predictions {len(self._predictions):,}"
            )
        if line not in self._marked:
            self.total_curated += 1
        if value not in MARKS:
            raise ValueError(f"illegal mark value given: {value}. Should be one of {MARKS}")
        self._marked[line] = value

    def add_mapping(
        self,
        subject: NormalizedNamableReference,
        obj: NormalizedNamableReference,
    ) -> None:
        """Add manually curated new mappings."""
        self._added_mappings.append(
            MappingTuple.model_validate(
                {
                    "subject": subject,
                    "predicate": NormalizedNamableReference.from_curie("skos:exactMatch"),
                    "object": obj,
                    "author": _manual_source(),
                    "mapping_justification": NormalizedNamableReference.from_curie(
                        "semapv:ManualMappingCuration"
                    ),
                }
            )
        )
        self.total_curated += 1

    def persist(self) -> None:
        """Save the current markings to the source files."""
        entries = defaultdict(list)

        for line, value in sorted(self._marked.items(), reverse=True):
            try:
                prediction = self._predictions.pop(line)
            except IndexError:
                raise IndexError(
                    f"you tried popping the {line} element from the predictions list, which only has {len(self._predictions):,} elements"
                ) from None
            prediction["mapping_tool"] = prediction.pop("mapping_tool")
            prediction["confidence"] = prediction.pop("confidence")
            prediction["author"] = _manual_source()
            prediction["mapping_justification"] = "semapv:ManualMappingCuration"

            # note these go backwards because of the way they are read
            if value == "broad":
                value = "correct"
                prediction["predicate_id"] = "skos:narrowMatch"
            elif value == "narrow":
                value = "correct"
                prediction["predicate_id"] = "skos:broadMatch"

            if value != "incorrect":
                prediction["predicate_modifier"] = ""
            else:
                prediction["predicate_modifier"] = "Not"

            entries[value].append(prediction)

        append_true_mappings(entries["correct"], path=self.positives_path)
        append_false_mappings(entries["incorrect"], path=self.negatives_path)
        append_unsure_mappings(entries["unsure"], path=self.unsure_path)
        write_predictions(self._predictions, path=self.predictions_path)
        self._marked.clear()

        # Now add manually curated mappings
        append_true_mappings(self._added_mappings, path=self.positives_path)
        self._added_mappings = []


CONTROLLER: Controller = cast(Controller, LocalProxy(lambda: current_app.config["controller"]))


class MappingForm(FlaskForm):
    """Form for entering new mappings."""

    source_prefix = StringField("Source Prefix", id="source_prefix")
    source_id = StringField("Source ID", id="source_id")
    source_name = StringField("Source Name", id="source_name")
    target_prefix = StringField("Target Prefix", id="target_prefix")
    target_id = StringField("Target ID", id="target_id")
    target_name = StringField("Target Name", id="target_name")
    submit = SubmitField("Add")

    def get_subject(self) -> NormalizedNamableReference:
        """Get the subject."""
        return NormalizedNamableReference(
            prefix=self.data["source_prefix"],
            identifier=self.data["source_id"],
            name=self.data["source_name"],
        )

    def get_object(self) -> NormalizedNamableReference:
        """Get the object."""
        return NormalizedNamableReference(
            prefix=self.data["target_prefix"],
            identifier=self.data["target_id"],
            name=self.data["target_name"],
        )


blueprint = flask.Blueprint("ui", __name__)


@blueprint.route("/")
def home() -> str:
    """Serve the home page."""
    form = MappingForm()
    state = State.from_flask_globals()
    predictions = CONTROLLER.predictions_from_state(state)
    remaining_rows = CONTROLLER.count_predictions_from_state(state)
    return flask.render_template(
        "home.html",
        predictions=predictions,
        form=form,
        state=state,
        remaining_rows=remaining_rows,
    )


@blueprint.route("/summary")
def summary() -> str:
    """Serve the summary page."""
    state = State.from_flask_globals()
    state.limit = None
    predictions = CONTROLLER.predictions_from_state(state)
    counter = Counter(
        (mapping["subject_id"].split(":")[0], mapping["object_id"].split(":")[0])
        for _, mapping in predictions
    )
    rows = []
    for (source_prefix, target_prefix), count in counter.most_common():
        row_state = deepcopy(state)
        row_state.source_prefix = source_prefix
        row_state.target_prefix = target_prefix
        rows.append((source_prefix, target_prefix, count, url_for_state(".home", row_state)))

    return flask.render_template(
        "summary.html",
        state=state,
        rows=rows,
    )


@blueprint.route("/add_mapping", methods=["POST"])
def add_mapping() -> werkzeug.Response:
    """Add a new mapping manually."""
    form = MappingForm()
    if form.is_submitted():
        try:
            subject = form.get_subject()
        except pydantic.ValidationError as e:
            flask.flash(f"Problem with source CURIE {e}", category="warning")
            return _go_home()

        try:
            obj = form.get_object()
        except pydantic.ValidationError as e:
            flask.flash(f"Problem with source CURIE {e}", category="warning")
            return _go_home()

        CONTROLLER.add_mapping(subject, obj)
        CONTROLLER.persist()
    else:
        flask.flash("missing form data", category="warning")
    return _go_home()


@blueprint.route("/commit")
def run_commit() -> werkzeug.Response:
    """Make a commit then redirect to the home page."""
    commit_info = commit(
        f"Curated {CONTROLLER.total_curated} mapping"
        f"{'s' if CONTROLLER.total_curated > 1 else ''}"
        f" ({getpass.getuser()})",
    )
    current_app.logger.warning("git commit res: %s", commit_info)
    if not_main():
        branch = get_branch()
        push_output = push(branch_name=branch)
        current_app.logger.warning("git push res: %s", push_output)
    else:
        flask.flash("did not push because on master branch")
        current_app.logger.warning("did not push because on master branch")
    CONTROLLER.total_curated = 0
    return _go_home()


CORRECT = {"yup", "true", "t", "correct", "right", "close enough", "disco"}
INCORRECT = {"no", "nope", "false", "f", "nada", "nein", "incorrect", "negative", "negatory"}
UNSURE = {"unsure", "maybe", "idk", "idgaf", "idgaff"}


def _normalize_mark(value: str) -> Mark:
    value = value.lower()
    if value in CORRECT:
        return "correct"
    elif value in INCORRECT:
        return "incorrect"
    elif value in UNSURE:
        return "unsure"
    elif value in {"broader", "broad"}:
        return "broad"
    elif value in {"narrow", "narrower"}:
        return "narrow"
    else:
        raise ValueError


@blueprint.route("/mark/<int:line>/<value>")
def mark(line: int, value: str) -> werkzeug.Response:
    """Mark the given line as correct or not."""
    CONTROLLER.mark(line, _normalize_mark(value))
    CONTROLLER.persist()
    return _go_home()


def _go_home() -> werkzeug.Response:
    state = State.from_flask_globals()
    return flask.redirect(url_for_state(".home", state))


app = get_app()

if __name__ == "__main__":
    app.run()
