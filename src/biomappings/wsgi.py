"""Web curation interface for :mod:`biomappings`."""

from __future__ import annotations

import getpass
import os
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast, get_args

import bioregistry
import curies
import flask
import flask_bootstrap
import pydantic
import sssom_pydantic
import werkzeug
from bioregistry import NormalizedNamableReference
from curies import NamableReference, Reference
from curies.vocabulary import broad_match, exact_match, manual_mapping_curation, narrow_match
from flask import current_app
from flask_wtf import FlaskForm
from pydantic import BaseModel
from sssom_pydantic import SemanticMapping
from werkzeug.local import LocalProxy
from wtforms import StringField, SubmitField

from .wsgi_utils import commit, get_branch, insert, not_main, push

__all__ = [
    "get_app",
]

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


def url_for_state(endpoint: str, state: State, **kwargs: Any) -> str:
    """Get the URL for an endpoint based on the state class."""
    vv = state.model_dump(exclude_none=True, exclude_defaults=True)
    vv.update(kwargs)  # make sure stuff explicitly set overrides state
    return flask.url_for(endpoint, **vv)


def get_app(
    *,
    target_references: Iterable[Reference] | None = None,
    predictions_path: Path | None = None,
    positives_path: Path | None = None,
    negatives_path: Path | None = None,
    unsure_path: Path | None = None,
    controller: Controller | None = None,
    user: NormalizedNamableReference | None = None,
    resolver_base: str | None = None,
) -> flask.Flask:
    """Get a curation flask app."""
    app_ = flask.Flask(__name__)
    app_.config["WTF_CSRF_ENABLED"] = False
    app_.config["SECRET_KEY"] = os.urandom(8)
    app_.config["SHOW_RELATIONS"] = True
    app_.config["SHOW_LINES"] = False
    if controller is None:
        if (
            predictions_path is None
            or positives_path is None
            or negatives_path is None
            or unsure_path is None
            or user is None
        ):
            raise ValueError
        controller = Controller(
            target_references=target_references,
            predictions_path=predictions_path,
            positives_path=positives_path,
            negatives_path=negatives_path,
            unsure_path=unsure_path,
            user=user,
        )
    if not controller._predictions and predictions_path is not None:
        raise RuntimeError(f"There are no predictions to curate in {predictions_path}")
    app_.config["controller"] = controller
    flask_bootstrap.Bootstrap4(app_)
    app_.register_blueprint(blueprint)

    if not resolver_base:
        resolver_base = "https://bioregistry.io"

    app_.jinja_env.globals.update(
        controller=controller,
        url_for_state=url_for_state,
        resolver_base=resolver_base,
    )
    return app_


class Controller:
    """A module for interacting with the predictions and mappings."""

    _user: NamableReference
    _predictions: list[SemanticMapping]
    converter: curies.Converter

    def __init__(
        self,
        *,
        target_references: Iterable[Reference] | None = None,
        predictions_path: Path,
        positives_path: Path,
        negatives_path: Path,
        unsure_path: Path,
        user: NamableReference,
        converter: curies.Converter | None = None,
    ) -> None:
        """Instantiate the web controller.

        :param target_references: Pairs of prefix, local unique identifiers that are the
            target of curation. If this is given, pre-filters will be made before on
            predictions to only show ones where either the source or target appears in
            this set
        :param predictions_path: A custom predictions file to curate from
        :param positives_path: A custom positives file to curate to
        :param negatives_path: A custom negatives file to curate to
        :param unsure_path: A custom unsure file to curate to
        """
        self.predictions_path = predictions_path
        self._predictions, _, self._predictions_metadata = sssom_pydantic.read(
            self.predictions_path
        )

        self.positives_path = positives_path
        self.negatives_path = negatives_path
        self.unsure_path = unsure_path

        self._marked: dict[int, Mark] = {}
        self.total_curated = 0
        self._added_mappings: list[SemanticMapping] = []
        self.target_references = set(target_references or [])

        if converter:
            self.converter = converter
        else:
            self.converter = bioregistry.get_converter()

        self._current_author = user

    def _get_current_author(self) -> NamableReference:
        return self._current_author

    def predictions_from_state(self, state: State) -> Iterable[tuple[int, SemanticMapping]]:
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
    ) -> Iterable[tuple[int, SemanticMapping]]:
        """Iterate over predictions.

        :param offset: If given, offset the iteration by this number
        :param limit: If given, only iterate this number of predictions.
        :param query: If given, show only equivalences that have it appearing as a
            substring in one of the source or target fields.
        :param source_query: If given, show only equivalences that have it appearing as
            a substring in one of the source fields.
        :param source_prefix: If given, show only mappings that have it appearing in the
            source prefix field
        :param target_query: If given, show only equivalences that have it appearing as
            a substring in one of the target fields.
        :param target_prefix: If given, show only mappings that have it appearing in the
            target prefix field
        :param prefix: If given, show only equivalences that have it appearing as a
            substring in one of the prefixes.
        :param same_text: If true, filter to predictions with the same label
        :param sort: If "desc", sorts in descending confidence order. If "asc", sorts in
            increasing confidence order. Otherwise, do not sort.
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
            for line_prediction, _ in zip(it, range(limit), strict=False):
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
    ) -> Iterator[tuple[int, SemanticMapping]]:
        it: Iterable[tuple[int, SemanticMapping]] = enumerate(self._predictions)
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
                lambda mapping: [
                    mapping.subject.curie,
                    mapping.subject_name,
                    mapping.object.curie,
                    mapping.object_name,
                    mapping.mapping_tool_name,
                ],
            )
        if source_prefix is not None:
            it = self._help_filter(source_prefix, it, lambda mapping: [mapping.subject.curie])
        if source_query is not None:
            it = self._help_filter(
                source_query, it, lambda mapping: [mapping.subject.curie, mapping.subject_name]
            )
        if target_query is not None:
            it = self._help_filter(
                target_query, it, lambda mapping: [mapping.object.curie, mapping.object_name]
            )
        if target_prefix is not None:
            it = self._help_filter(target_prefix, it, lambda mapping: [mapping.object.curie])
        if prefix is not None:
            it = self._help_filter(
                prefix, it, lambda mapping: [mapping.subject.curie, mapping.object.curie]
            )
        if provenance is not None:
            it = self._help_filter(
                provenance,
                it,
                lambda mapping: [mapping.mapping_tool_name],
            )

        def _get_confidence(t: tuple[int, SemanticMapping]) -> float:
            return t[1].confidence or 0.0

        if sort is not None:
            if sort == "desc":
                it = iter(sorted(it, key=_get_confidence, reverse=True))
            elif sort == "asc":
                it = iter(sorted(it, key=_get_confidence, reverse=False))
            elif sort == "subject":
                it = iter(sorted(it, key=lambda l_p: l_p[1].subject.curie))
            elif sort == "object":
                it = iter(sorted(it, key=lambda l_p: l_p[1].object.curie))
            else:
                raise ValueError(f"unknown sort type: {sort}")

        if same_text:
            it = (
                (line, mapping)
                for line, mapping in it
                if mapping.subject_name
                and mapping.object_name
                and mapping.subject_name.casefold() == mapping.object_name.casefold()
                and mapping.predicate.curie == "skos:exactMatch"
            )

        rv = ((line, prediction) for line, prediction in it if line not in self._marked)
        return rv

    @staticmethod
    def _help_filter(
        query: str,
        it: Iterable[tuple[int, SemanticMapping]],
        func: Callable[[SemanticMapping], list[str | None]],
    ) -> Iterable[tuple[int, SemanticMapping]]:
        query = query.casefold()
        for line, mapping in it:
            if any(query in element.casefold() for element in func(mapping) if element):
                yield line, mapping

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
            SemanticMapping.model_validate(
                {
                    "subject": subject,
                    "predicate": exact_match,
                    "object": obj,
                    "authors": [self._get_current_author()],
                    "justification": manual_mapping_curation,
                }
            )
        )
        self.total_curated += 1

    def _insert(self, mappings: Iterable[SemanticMapping], path: Path) -> None:
        insert(path=path, converter=self.converter, include_mappings=mappings)

    def persist(self) -> None:
        """Save the current markings to the source files."""
        if not self._marked:
            # no need to persist if there are no marks
            return None

        entries: defaultdict[Literal["correct", "incorrect", "unsure"], list[SemanticMapping]] = (
            defaultdict(list)
        )

        for line, value in sorted(self._marked.items(), reverse=True):
            try:
                mapping = self._predictions.pop(line)
            except IndexError:
                raise IndexError(
                    f"you tried popping the {line} element from the predictions list, which only has {len(self._predictions):,} elements"
                ) from None

            update: dict[str, Any] = {
                "authors": [self._get_current_author()],
                "justification": manual_mapping_curation,
                # throw the predicted confidence away, since it's been manually curated now
                "confidence": None,
            }

            entry_key: Literal["correct", "incorrect", "unsure"]
            # note these go backwards because of the way they are read
            if value == "broad":
                entry_key = "correct"
                update["predicate"] = narrow_match
            elif value == "narrow":
                entry_key = "correct"
                update["predicate"] = broad_match
            elif value == "incorrect":
                entry_key = "incorrect"
                update["predicate_modifier"] = "Not"
            elif value == "correct":
                entry_key = "correct"
            elif value == "unsure":
                entry_key = "unsure"
            else:
                raise NotImplementedError

            # replace some values using model_copy since the model is frozen
            new_mapping = mapping.model_copy(update=update)

            entries[entry_key].append(new_mapping)

        # no need to standardize since we assume everything was correct on load.
        # only write files that have some values to go in them!
        if entries["correct"]:
            self._insert(entries["correct"], path=self.positives_path)
        if entries["incorrect"]:
            self._insert(entries["incorrect"], path=self.negatives_path)
        if entries["unsure"]:
            self._insert(entries["unsure"], path=self.unsure_path)

        sssom_pydantic.write(
            self._predictions,
            self.predictions_path,
            metadata=self._predictions_metadata,
            converter=self.converter,
            drop_duplicates=True,
            sort=True,
        )
        self._marked.clear()

        # Now add manually curated mappings, if there are any
        if self._added_mappings:
            self._insert(self._added_mappings, path=self.positives_path)
            self._added_mappings = []

        return None


CONTROLLER: Controller = cast(Controller, LocalProxy(lambda: current_app.config["controller"]))


# TODO how to get types for flask-wtf
class MappingForm(FlaskForm):  # type:ignore[misc]
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
    counter = Counter((mapping.subject.prefix, mapping.object.prefix) for _, mapping in predictions)
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
