"""Tests for bellybutton/yaml.py."""

import pytest

import yaml

import bellybutton.parsing


@pytest.mark.parametrize('expression', (
    '- !xpath //*',
    '- //*',
    '- !regex .*',
))
def test_constructors(expression):
    """Ensure custom constructors successfully parse given expressions."""
    yaml.load(expression)
