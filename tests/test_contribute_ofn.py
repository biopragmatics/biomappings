"""

"""
import unittest
from textwrap import dedent

from biomappings.contribute.utils import get_curated_mappings
from biomappings.contribute.ofn import update_ofn_lines


class TestContributeOBO(unittest.TestCase):
    """A test case for contributing to OWL files encoded in Functional OWL."""

    def setUp(self) -> None:
        """Set up the test case with a specific mapping."""
        mappings = get_curated_mappings("efo")
        mappings = [
            mappings
            for mappings in mappings
            if (
                mappings["source prefix"] == "efo"
                and mappings["source identifier"] == "1000567"
                and mappings["target prefix"] == "doid"
            )
        ]
        self.assertEqual(1, len(mappings))
        self.mappings = mappings

    def test_no_addition(self):
        """Test adding a non-redundant mapping."""
        original = dedent(
            """\
            # Class: efo:EFO_1000567 (Testicular Granulosa Cell Tumor)

            AnnotationAssertion(obo:IAO_0000115 efo:EFO_1000567 "A rare sex cord-stromal tumor that arises from the testis. It is characterized by the presence of granulosa-like cells and Call-Exner bodies. There are two variants described, the adult and the juvenile.")
            AnnotationAssertion(oboInOwl:hasDbXref efo:EFO_1000567 "NCIt:C6357")
            AnnotationAssertion(rdfs:label efo:EFO_1000567 "Testicular Granulosa Cell Tumor")
            SubClassOf(efo:EFO_1000567 efo:EFO_0004281)
            SubClassOf(efo:EFO_1000567 ObjectSomeValuesFrom(efo:EFO_0000784 ObjectUnionOf(obo:UBERON_0000473 ObjectSomeValuesFrom(obo:BFO_0000050 obo:UBERON_0000473))))
            """
        )
        expected = dedent(
            """\
            # Class: efo:EFO_1000567 (Testicular Granulosa Cell Tumor)
        
            AnnotationAssertion(obo:IAO_0000115 efo:EFO_1000567 "A rare sex cord-stromal tumor that arises from the testis. It is characterized by the presence of granulosa-like cells and Call-Exner bodies. There are two variants described, the adult and the juvenile.")
            AnnotationAssertion(oboInOwl:hasDbXref efo:EFO_1000567 "NCIt:C6357")
            AnnotationAssertion(Annotation(dcterms:contributor <https://orcid.org/0000-0003-4423-4370>) oboInOwl:hasDbXref efo:EFO_1000567 "DOID:5331")
            AnnotationAssertion(rdfs:label efo:EFO_1000567 "Testicular Granulosa Cell Tumor")
            SubClassOf(efo:EFO_1000567 efo:EFO_0004281)
            SubClassOf(efo:EFO_1000567 ObjectSomeValuesFrom(efo:EFO_0000784 ObjectUnionOf(obo:UBERON_0000473 ObjectSomeValuesFrom(obo:BFO_0000050 obo:UBERON_0000473))))
            """
        )
        self.assertEqual(
            original.splitlines(),
            update_ofn_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )