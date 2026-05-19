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


def test_region_inferred_from_terragrunt_path():
    """Terragrunt path <root>/prod/us-east-1/module/main.tf -> region us-east-1."""
    from lib.parser import parse_project

    with tempfile.TemporaryDirectory() as tmp:
        module_dir = os.path.join(tmp, 'prod', 'us-east-1', 'mymodule')
        os.makedirs(module_dir)
        # Intentionally malformed HCL to exercise regex fallback
        _write(os.path.join(module_dir, 'main.tf'),
               'resource "aws_s3_bucket" "regional" { invalid; syntax }')

        result = parse_project(tmp)

    assert 'aws_s3_bucket.regional' in result['resources'], (
        "Resource not found — regex fallback may have failed entirely"
    )
    rd = result['resources']['aws_s3_bucket.regional']
    assert rd['region'] == 'us-east-1', (
        f"Expected region 'us-east-1', got '{rd['region']}'"
    )
