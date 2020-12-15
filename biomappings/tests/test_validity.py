import re
import requests
from biomappings import load_mappings, load_predictions


mappings = load_mappings()
predictions = load_predictions()


class InvalidPrefix(ValueError):
    pass


class InvalidIdentifier(ValueError):
    pass


class MiriamValidator:
    def __init__(self):
        self.entries = self._load_identifiers_entries()

    @staticmethod
    def _load_identifiers_entries():
        url = \
            'https://registry.api.identifiers.org/resolutionApi/getResolverDataset'
        res = requests.get(url)
        regj = res.json()
        patterns = {entry['prefix']:
                        {'pattern': re.compile(entry['pattern']),
                         'namespace_embedded': entry['namespaceEmbeddedInLui']}
                    for entry in sorted(regj['payload']['namespaces'],
                                        key=lambda x: x['prefix'])}
        return patterns

    def check_valid_prefix_id(self, prefix, identifier):
        if prefix not in self.entries:
            raise InvalidPrefix(prefix)
        entry = self.entries[prefix]
        if not re.match(entry['pattern'], identifier):
            raise InvalidIdentifier(identifier)


miriam_validator = MiriamValidator()


def test_valid_mappings():
    for mapping in mappings:
        miriam_validator.check_valid_prefix_id(mapping['source prefix'],
                                               mapping['source identifier'])
        miriam_validator.check_valid_prefix_id(mapping['target prefix'],
                                               mapping['target identifier'])
