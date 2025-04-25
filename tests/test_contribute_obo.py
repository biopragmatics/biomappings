"""Tests for contribution workflows."""

import unittest
from textwrap import dedent

from biomappings.contribute.obo import get_curated_mappings, update_obo_lines


class TestContributeOBO(unittest.TestCase):
    """A test case for contributing to OBO flat files."""

    def setUp(self) -> None:
        """Set up the test case with a specific mapping."""
        mappings = get_curated_mappings("uberon")
        sources = {mapping["source identifier"] for mapping in mappings}
        self.assertIn("0000018", sources, msg="Mappings are not loaded properly")

        # cut the mappings down in case additional ones are curated later
        mappings = [
            mappings
            for mappings in mappings
            if mappings["source identifier"] == "0000018" and mappings["target prefix"] == "idomal"
        ]
        self.assertEqual(1, len(mappings))
        self.mappings = mappings

    def test_no_addition(self):
        """Test adding a non-redundant mapping."""
        original = dedent(
            """\
            [Term]
            id: UBERON:0000019
            name: something else
            """
        )
        self.assertEqual(
            original.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

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

        # node that the IDOMAL xref line is added
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
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

    def test_addition_no_xrefs_with_def(self):
        """Test adding a non-redundant mapping."""
        original = dedent(
            """\
            [Term]
            id: UBERON:0000018
            name: compound eye
            def: "A light sensing organ composed of ommatidia." [FB:gg, Wikipedia:Compound_eye]
            """
        )
        expected = dedent(
            """\
            [Term]
            id: UBERON:0000018
            name: compound eye
            def: "A light sensing organ composed of ommatidia." [FB:gg, Wikipedia:Compound_eye]
            xref: IDOMAL:0002421 {dcterms:contributor="https://orcid.org/0000-0003-4423-4370"} ! compound eye
            """
        )
        self.assertEqual(
            expected.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

    def test_addition_no_xrefs(self):
        """Test adding a non-redundant mapping."""
        original = dedent(
            """\
            [Term]
            id: UBERON:0000018
            name: compound eye
            """
        )
        expected = dedent(
            """\
            [Term]
            id: UBERON:0000018
            xref: IDOMAL:0002421 {dcterms:contributor="https://orcid.org/0000-0003-4423-4370"} ! compound eye
            name: compound eye
            """
        )
        self.assertEqual(
            expected.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

    def test_skip_redundant_1(self):
        """Test skipping adding a mapping that doesn't have metadata."""
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
            xref: IDOMAL:0002421
            xref: TGMA:0000024
            intersection_of: UBERON:0000970 ! eye
            relationship: only_in_taxon NCBITaxon:6656 {source="PMID:21062451"} ! Arthropoda
            property_value: seeAlso "https://github.com/obophenotype/uberon/issues/457" xsd:anyURI
            """
        )
        self.assertEqual(
            original.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

    def test_skip_redundant_2(self):
        """Test skipping adding a mapping that doesn't have metadata."""
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
            xref: IDOMAL:0002421 {dcterms:contributor="https://orcid.org/0000-0003-4423-4370"} ! compound eye
            xref: TGMA:0000024
            intersection_of: UBERON:0000970 ! eye
            relationship: only_in_taxon NCBITaxon:6656 {source="PMID:21062451"} ! Arthropoda
            property_value: seeAlso "https://github.com/obophenotype/uberon/issues/457" xsd:anyURI
            """
        )
        self.assertEqual(
            original.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )

    def test_skip_redundant_3(self):
        """Test skipping where the xref just has meta-xrefs."""
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
            xref: IDOMAL:0002421 [https://orcid.org/0000-0003-4423-4370]
            xref: TGMA:0000024
            intersection_of: UBERON:0000970 ! eye
            relationship: only_in_taxon NCBITaxon:6656 {source="PMID:21062451"} ! Arthropoda
            property_value: seeAlso "https://github.com/obophenotype/uberon/issues/457" xsd:anyURI
            """
        )
        self.assertEqual(
            original.splitlines(),
            update_obo_lines(mappings=self.mappings, lines=original.splitlines(), progress=False),
        )
