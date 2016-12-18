from collections import defaultdict
import json

import pytest

from anotamela.cache import Cache, AVAILABLE_CACHES


class MockCache(Cache):
    def __init__(self):
        self.name = 'Mock Cache'
        self.storage = defaultdict(dict)

    def _client_set(self, info_dict, namespace, save_as_json):
        table = self.storage[namespace]
        if save_as_json:
            info_dict = {k: json.dumps(v) for k, v in info_dict.items()}
        table.update(info_dict)

    def _client_get(self, keys, namespace, load_as_json):
        table = self.storage[namespace]
        info_dict = {k: table[k] for k in keys if k in table}
        if load_as_json:
            info_dict = {k: json.loads(v) for k, v in info_dict.items()}
        return info_dict


AVAILABLE_CACHES['mock_cache'] = MockCache


@pytest.fixture(scope='module')
def mock_cache():
    return MockCache()

