"""Tests for contribution workflows."""

import unittest
from textwrap import dedent

from biomappings.contribute.obo import update_obo_lines


class TestContributeOBO(unittest.TestCase):
    """A test case for contributing to OBO flat files."""

    def test_addition(self):
        """Test adding a non-redundant mapping."""
        original = dedent(
            """\
            [Term]
            id: UBERON:0000018
            name: compound eye
            def: "A light sensing organ composed of ommatidia." [FB:gg, Wikipedia:Compound_eye]
            subset: organ_slim
            synonym: "adult compound eye" RELATED []
            xref: BTO:0001921
            xref: HAO:0000217
            xref: TGMA:0000024
            intersection_of: UBERON:0000970 ! eye
            relationship: only_in_taxon NCBITaxon:6656 {source="PMID:21062451"} ! Arthropoda
            property_value: seeAlso "https://github.com/obophenotype/uberon/issues/457" xsd:anyURI
            """
        )
        expected = dedent(
            """\
            [Term]
            id: UBERON:0000018
            name: compound eye
            def: "A light sensing organ composed of ommatidia." [FB:gg, Wikipedia:Compound_eye]
            subset: organ_slim
            synonym: "adult compound eye" RELATED []
            xref: BTO:0001921
            xref: HAO:0000217
            xref: IDOMAL:0002421 {dcterms:contributor="https://orcid.org/0000-0003-4423-4370"} ! compound eye
            xref: TGMA:0000024
            intersection_of: UBERON:0000970 ! eye
            relationship: only_in_taxon NCBITaxon:6656 {source="PMID:21062451"} ! Arthropoda
            property_value: seeAlso "https://github.com/obophenotype/uberon/issues/457" xsd:anyURI
        """
        )
        self.assertEqual(
            expected.splitlines(),
            update_obo_lines(prefix="uberon", lines=original.splitlines()),
        )
