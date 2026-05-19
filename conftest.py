import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

import pytest

@pytest.fixture
def minimal_tf_data():
    return {
        'resources': {
            'aws_s3_bucket.my_bucket': {
                'type': 'aws_s3_bucket',
                'name': 'my_bucket',
                'config': {'tags': {'env': 'test'}},
                'file': 'main.tf',
                'module_path': 'root',
                'provider': 'aws',
                'tier': 'Data',
                'account': 'default',
                'region': 'us-east-1',
                'has_tags': True,
                'net_info': [],
            }
        },
        'modules': {},
        'providers': {'aws': {}},
        'data': {},
        'variables': {},
        'outputs': {},
        'locals': {},
        'dependencies': [],
        'accounts': {'default'},
        'regions': {'us-east-1'},
    }
