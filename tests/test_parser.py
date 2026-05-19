import os, tempfile, pytest


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def test_dot_terraform_dir_excluded():
    """Resources inside .terraform/ must never appear in output."""
    from lib.parser import parse_project

    with tempfile.TemporaryDirectory() as tmp:
        _write(os.path.join(tmp, '.terraform', 'main.tf'),
               'resource "aws_s3_bucket" "excluded" {}')
        _write(os.path.join(tmp, 'main.tf'),
               'resource "aws_s3_bucket" "included" {}')

        result = parse_project(tmp)

    assert 'aws_s3_bucket.excluded' not in result['resources'], (
        ".terraform/ resource leaked into diagram"
    )
    assert 'aws_s3_bucket.included' in result['resources']
