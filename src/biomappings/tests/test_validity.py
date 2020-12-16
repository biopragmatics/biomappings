"""Validation tests for :mod:`biomappings`."""

import itertools as itt
import re
from collections import Counter

import requests

from biomappings import load_false_mappings, load_mappings, load_predictions
from biomappings.utils import get_canonical_tuple

mappings = load_mappings()
predictions = load_predictions()
incorrect = load_false_mappings()


class InvalidPrefix(ValueError):
    """Raised for an invalid prefix."""


class InvalidIdentifier(ValueError):
    """Raised for an invalid identifier."""


class MiriamValidator:
    """Validate prefix/identifier pairs based on the MIRIAM database."""

    def __init__(self):  # noqa: D107
        self.entries = self._load_identifiers_entries()

    @staticmethod
    def _load_identifiers_entries():
        url = 'https://registry.api.identifiers.org/resolutionApi/getResolverDataset'
        res = requests.get(url)
        regj = res.json()
        patterns = {
            entry['prefix']: {
                'pattern': re.compile(entry['pattern']),
                'namespace_embedded': entry['namespaceEmbeddedInLui'],
            }
            for entry in sorted(regj['payload']['namespaces'], key=lambda x: x['prefix'])
        }
        return patterns

    def check_valid_prefix_id(self, prefix, identifier):
        """Check the prefix/identifier pair is valid."""
        if prefix not in self.entries:
            raise InvalidPrefix(prefix)
        entry = self.entries[prefix]
        if not re.match(entry['pattern'], identifier):
            raise InvalidIdentifier(identifier)


miriam_validator = MiriamValidator()


def test_valid_mappings():
    """Test the validity of the prefixes and identifiers in the mappings."""
    for mapping in itt.chain(mappings, incorrect, predictions):
        miriam_validator.check_valid_prefix_id(
            mapping['source prefix'],
            mapping['source identifier'],
        )
        miriam_validator.check_valid_prefix_id(
            mapping['target prefix'],
            mapping['target identifier'],
        )


def test_redundancy():
    """Test the redundancy of manually curated mappings and predicted mappings."""
    counter = Counter(
        get_canonical_tuple(m)
        for m in itt.chain(mappings, incorrect, predictions)
    )
    redundant = [k for k, v in counter.items() if v > 1]
    if redundant:
        raise ValueError(f'Redundant: {redundant}')
