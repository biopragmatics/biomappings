from pyparsing import (
    Word,
    alphanums,
    Optional,
    ParseResults,
    Suppress,
    ZeroOrMore,
    Group,
    nested_expr,
)
from pyparsing.common import dbl_quoted_string, remove_quotes
from curies import Reference
from pydantic import BaseModel, Field


def parse_results_to_reference(r: ParseResults) -> Reference:
    return Reference(prefix=r[0], identifier=r[0])


curie_expr = (Word(alphanums) + Suppress(":") + Word(alphanums)).add_parse_action(
    parse_results_to_reference
)


class Literal(BaseModel):
    value: str
    dtype: Reference | None = None
    # lang: str | None = None


class Annotation(BaseModel):
    predicate: Reference
    object: Reference | Literal


class AnnotationAssertion(BaseModel):
    annotations: list[Annotation] = Field(default_factory=list)
    subject: Reference
    predicate: Reference
    object: Reference | Literal


def _parse(s: ParseResults):
    return Literal(value=s[0], dtype=s[1] if len(s) == 2 else None)


dtype = Suppress("^^") + curie_expr


literal = (
    dbl_quoted_string("literal").set_parse_action(remove_quotes) + Optional(dtype("dtype"))
).set_parse_action(_parse)

identifier = curie_expr
identifier_or_scalar = identifier ^ literal


def parse_annotation(r: ParseResults) -> Annotation:
    return Annotation(predicate=r[0][0], object=r[0][1])


annotation_expr = (
    Suppress("Annotation")
    + nested_expr(
        content=identifier.set_name("predicate") + identifier_or_scalar.set_name("object")
    )
).set_parse_action(parse_annotation)


def parse_annotation_assertion(r: ParseResults) -> AnnotationAssertion:
    if len(r[0]) == 3:
        return AnnotationAssertion(predicate=r[0][0], subject=r[0][1], object=r[0][2])
    print(r[0][0])
    return AnnotationAssertion(
        annotations=r[0][0], predicate=r[0][1], subject=r[0][2], object=r[0][3]
    )


expr = (
    Suppress("AnnotationAssertion")
    + nested_expr(
        content=(
            ZeroOrMore(Group(annotation_expr)).set_name("annotations")
            + identifier.set_name("predicate")
            + identifier.set_name("subject")
            + identifier_or_scalar.set_name("object")
        )
    )
).set_parse_action(parse_annotation_assertion)

if __name__ == "__main__":
    # print(literal.parse_string('"hello"'))
    # print(literal.parse_string('"hello"'))
    # print(literal.parse_string('"hello"^^xsd:string'))
    print(expr.parse_string('AnnotationAssertion(a:b c:d "value")'))
    print(expr.parse_string('AnnotationAssertion(a:b c:d "value"^^xsd:string)'))
    print(expr.parse_string("AnnotationAssertion(Annotation(g:h i:j) a:b c:d e:f)"))
    print(expr.parse_string('AnnotationAssertion(Annotation(g:h "value") a:b c:d e:f)'))
    print(expr.parse_string('AnnotationAssertion(Annotation(g:h "value"^^xsd:string) a:b c:d e:f)'))
