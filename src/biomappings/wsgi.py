# -*- coding: utf-8 -*-

"""Web curation interface for :mod:`biomappings`."""

import getpass
import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union

import bioregistry
import flask
import flask_bootstrap
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

from biomappings.resources import (
    append_false_mappings,
    append_true_mappings,
    append_unsure_mappings,
    load_curators,
    load_predictions,
    write_predictions,
)
from biomappings.utils import (
    check_valid_prefix_id,
    commit,
    get_branch,
    get_curie,
    not_main,
    push,
)


def get_app(target_curies: Optional[Iterable[Tuple[str, str]]] = None) -> flask.Flask:
    """Get a curation flask app."""
    app_ = flask.Flask(__name__)
    app_.config["WTF_CSRF_ENABLED"] = False
    app_.config["SECRET_KEY"] = os.urandom(8)
    app_.config["SHOW_RELATIONS"] = True
    app_.config["SHOW_LINES"] = False
    controller = Controller(target_curies=target_curies)
    app_.config["controller"] = controller
    flask_bootstrap.Bootstrap4(app_)
    app_.register_blueprint(blueprint)
    return app_


# A mapping from your computer's user, returned by getuser.getpass()
KNOWN_USERS = {record["user"]: record["orcid"] for record in load_curators()}


def _manual_source():
    known_user = KNOWN_USERS.get(getpass.getuser())
    if known_user:
        return f"orcid:{known_user}"
    return "web"


class Controller:
    """A module for interacting with the predictions and mappings."""

    def __init__(self, target_curies: Optional[Iterable[Tuple[str, str]]] = None):
        """Instantiate the web controller.

        :param target_curies: Pairs of prefix, local unique identifiers that are the target
            of curation. If this is given, pre-filters will be made before on predictions
            to only show ones where either the source or target appears in this set
        """
        self._predictions = load_predictions()
        self._marked: Dict[int, str] = {}
        self.total_curated = 0
        self._added_mappings: List[Dict[str, Union[None, str, float]]] = []
        self.target_ids = set(target_curies or [])

    def predictions(
        self,
        *,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        source_query: Optional[str] = None,
        source_prefix: Optional[str] = None,
        target_query: Optional[str] = None,
        target_prefix: Optional[str] = None,
        prefix: Optional[str] = None,
        sort: Optional[str] = None,
        same_text: bool = False,
        provenance: Optional[str] = None,
    ) -> Iterable[Tuple[int, Mapping[str, Any]]]:
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

    def count_predictions(
        self,
        query: Optional[str] = None,
        source_query: Optional[str] = None,
        source_prefix: Optional[str] = None,
        target_query: Optional[str] = None,
        target_prefix: Optional[str] = None,
        prefix: Optional[str] = None,
        sort: Optional[str] = None,
        same_text: bool = False,
        provenance: Optional[str] = None,
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
        query: Optional[str] = None,
        source_query: Optional[str] = None,
        source_prefix: Optional[str] = None,
        target_query: Optional[str] = None,
        target_prefix: Optional[str] = None,
        prefix: Optional[str] = None,
        sort: Optional[str] = None,
        same_text: bool = False,
        provenance: Optional[str] = None,
    ):
        it: Iterable[Tuple[int, Mapping[str, Any]]] = enumerate(self._predictions)
        if self.target_ids:
            it = (
                (line, p)
                for (line, p) in it
                if (p["source prefix"], p["source identifier"]) in self.target_ids
                or (p["target prefix"], p["target identifier"]) in self.target_ids
            )

        if query is not None:
            it = self._help_filter(
                query,
                it,
                {
                    "source prefix",
                    "source identifier",
                    "source name",
                    "target prefix",
                    "target identifier",
                    "target name",
                },
            )
        if source_prefix is not None:
            it = self._help_filter(source_prefix, it, {"source prefix"})
        if source_query is not None:
            it = self._help_filter(
                source_query, it, {"source prefix", "source identifier", "source name"}
            )
        if target_query is not None:
            it = self._help_filter(
                target_query, it, {"target prefix", "target identifier", "target name"}
            )
        if target_prefix is not None:
            it = self._help_filter(target_prefix, it, {"target prefix"})
        if prefix is not None:
            it = self._help_filter(prefix, it, {"source prefix", "target prefix"})
        if provenance is not None:
            it = self._help_filter(provenance, it, {"source"})

        if sort is not None:
            it = iter(sorted(it, key=lambda l_p: l_p[1]["confidence"], reverse=sort == "desc"))

        if same_text:
            it = (
                (line, prediction)
                for line, prediction in it
                if prediction["source name"].casefold() == prediction["target name"].casefold()
                and prediction["relation"] == "skos:exactMatch"
            )

        rv = ((line, prediction) for line, prediction in it if line not in self._marked)
        return rv

    @staticmethod
    def _help_filter(query: str, it, elements: Set[str]):
        query = query.casefold()
        return (
            (line, prediction)
            for line, prediction in it
            if any(query in prediction[element].casefold() for element in elements)
        )

    @staticmethod
    def get_curie(prefix: str, identifier: str) -> str:
        """Return CURIE for a given prefix and identifier."""
        return get_curie(prefix, identifier)

    @classmethod
    def get_url(cls, prefix: str, identifier: str) -> str:
        """Return URL for a given prefix and identifier."""
        identifier = bioregistry.standardize_identifier(prefix, identifier)
        if bioregistry.get_obofoundry_prefix(prefix):
            return bioregistry.get_ols_iri(prefix, identifier)
        return bioregistry.get_bioregistry_iri(prefix, identifier)

    @property
    def total_predictions(self) -> int:
        """Return the total number of yet unmarked predictions."""
        return len(self._predictions) - len(self._marked)

    def mark(self, line: int, value: str) -> None:
        """Mark the given equivalency as correct.

        :param line: Position of the prediction
        :param value: Value to mark the prediction with
        :raises ValueError: if an invalid value is used
        """
        if line not in self._marked:
            self.total_curated += 1
        if value not in {"correct", "incorrect", "unsure"}:
            raise ValueError
        self._marked[line] = value

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
            check_valid_prefix_id(source_prefix, source_id)
        except ValueError as e:
            flask.flash(
                f"Problem with source CURIE {source_prefix}:{source_id}: {e.__class__.__name__}",
                category="warning",
            )
            return

        try:
            check_valid_prefix_id(target_prefix, target_id)
        except ValueError as e:
            flask.flash(
                f"Problem with target CURIE {target_prefix}:{target_id}: {e.__class__.__name__}",
                category="warning",
            )
            return

        self._added_mappings.append(
            {
                "source prefix": source_prefix,
                "source identifier": source_id,
                "source name": source_name,
                "relation": "skos:exactMatch",
                "target prefix": target_prefix,
                "target identifier": target_id,
                "target name": target_name,
                "source": _manual_source(),
                "type": "manual",
                "prediction_type": None,
                "prediction_source": None,
                "prediction_confidence": None,
            }
        )
        self.total_curated += 1

    def persist(self):
        """Save the current markings to the source files."""
        entries = defaultdict(list)

        for line, value in sorted(self._marked.items(), reverse=True):
            prediction = self._predictions.pop(line)
            prediction["prediction_type"] = prediction.pop("type")
            prediction["prediction_source"] = prediction.pop("source")
            prediction["prediction_confidence"] = prediction.pop("confidence")
            prediction["source"] = _manual_source()
            prediction["type"] = "semapv:ManualMappingCuration"
            entries[value].append(prediction)

        append_true_mappings(entries["correct"])
        append_false_mappings(entries["incorrect"])
        append_unsure_mappings(entries["unsure"])
        write_predictions(self._predictions)
        self._marked.clear()

        # Now add manually curated mappings
        append_true_mappings(self._added_mappings)
        self._added_mappings = []


class MappingForm(FlaskForm):
    """Form for entering new mappings."""

    source_prefix = StringField("Source Prefix", id="source_prefix")
    source_id = StringField("Source ID", id="source_id")
    source_name = StringField("Source Name", id="source_name")
    target_prefix = StringField("Target Prefix", id="target_prefix")
    target_id = StringField("Target ID", id="target_id")
    target_name = StringField("Target Name", id="target_name")
    submit = SubmitField("Add")


blueprint = flask.Blueprint("ui", __name__)


@blueprint.route("/")
def home():
    """Serve the home page."""
    form = MappingForm()
    limit = flask.request.args.get("limit", type=int, default=10)
    offset = flask.request.args.get("offset", type=int, default=0)
    query = flask.request.args.get("query")
    source_query = flask.request.args.get("source_query")
    source_prefix = flask.request.args.get("source_prefix")
    target_query = flask.request.args.get("target_query")
    target_prefix = flask.request.args.get("target_prefix")
    provenance = flask.request.args.get("provenance")
    prefix = flask.request.args.get("prefix")
    sort = flask.request.args.get("sort")
    same_text = flask.request.args.get("same_text", default="false").lower() in {"true", "t"}
    show_relations = current_app.config["SHOW_RELATIONS"]
    show_lines = current_app.config["SHOW_LINES"]
    return flask.render_template(
        "home.html",
        controller=current_app.config["controller"],
        form=form,
        limit=limit,
        offset=offset,
        query=query,
        source_query=source_query,
        source_prefix=source_prefix,
        target_query=target_query,
        target_prefix=target_prefix,
        prefix=prefix,
        sort=sort,
        same_text=same_text,
        provenance=provenance,
        # configured
        show_relations=show_relations,
        show_lines=show_lines,
    )


@blueprint.route("/add_mapping", methods=["POST"])
def add_mapping():
    """Add a new mapping manually."""
    form = MappingForm()
    if form.is_submitted():
        current_app.config["controller"].add_mapping(
            form.data["source_prefix"],
            form.data["source_id"],
            form.data["source_name"],
            form.data["target_prefix"],
            form.data["target_id"],
            form.data["target_name"],
        )
        current_app.config["controller"].persist()
    else:
        flask.flash("missing form data", category="warning")
    return _go_home()


@blueprint.route("/commit")
def run_commit():
    """Make a commit then redirect to the the home page."""
    commit_info = commit(
        f'Curated {current_app.config["controller"].total_curated} mapping'
        f'{"s" if current_app.config["controller"].total_curated > 1 else ""}'
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
    current_app.config["controller"].total_curated = 0
    return _go_home()


CORRECT = {"yup", "true", "t", "correct", "right", "close enough", "disco"}
INCORRECT = {"no", "nope", "false", "f", "nada", "nein", "incorrect", "negative", "negatory"}
UNSURE = {"unsure", "maybe", "idk", "idgaf", "idgaff"}


def _normalize_mark(value: str) -> str:
    value = value.lower()
    if value in CORRECT:
        return "correct"
    elif value in INCORRECT:
        return "incorrect"
    elif value in UNSURE:
        return "unsure"
    else:
        raise ValueError


@blueprint.route("/mark/<int:line>/<value>")
def mark(line: int, value: str):
    """Mark the given line as correct or not."""
    current_app.config["controller"].mark(line, _normalize_mark(value))
    current_app.config["controller"].persist()
    return _go_home()


def _go_home():
    return flask.redirect(
        flask.url_for(
            ".home",
            limit=flask.request.args.get("limit", type=int),
            offset=flask.request.args.get("offset", type=int),
            query=flask.request.args.get("query"),
            source_query=flask.request.args.get("source_query"),
            source_prefix=flask.request.args.get("source_prefix"),
            target_query=flask.request.args.get("target_query"),
            target_prefix=flask.request.args.get("target_prefix"),
            prefix=flask.request.args.get("prefix"),
            same_text=flask.request.args.get("same_text", default="false").lower() in {"true", "t"},
            provenance=flask.request.args.get("provenance"),
            sort=flask.request.args.get("sort"),
            # config
            show_relations=current_app.config["SHOW_RELATIONS"],
            show_lines=current_app.config["SHOW_LINES"],
        )
    )


app = get_app()

if __name__ == "__main__":
    app.run()
