"""Tests for bellybutton/parsing.py."""

import re

import pytest

import yaml
from lxml.etree import XPath, XPathSyntaxError

from bellybutton.exceptions import InvalidNode
from bellybutton.parsing import Settings


@pytest.mark.parametrize('expression,expected_type', (
    ('!xpath //*', XPath),
    ('//*', XPath),
    pytest.mark.xfail(('//[]', XPath), raises=XPathSyntaxError),
    ('!regex .*', re._pattern_type),
    pytest.mark.xfail(('!regex "*"', re._pattern_type), raises=re.error),
    ('!settings {included: [], excluded: []}', Settings),
    pytest.mark.xfail(('!settings {}', Settings), raises=InvalidNode)
))
def test_constructors(expression, expected_type):
    """Ensure custom constructors successfully parse given expressions."""
    assert isinstance(yaml.load(expression), expected_type)
