"""Unit tests for bellybutton/parsing.py."""

import re

import pytest

import yaml
from lxml.etree import XPath, XPathSyntaxError

from bellybutton.exceptions import InvalidNode
from bellybutton.parsing import Settings, parse_rule, Rule

try:
    from re import Pattern as pattern_type
except ImportError:
    from re import _pattern_type as pattern_type

@pytest.mark.parametrize('expression,expected_type', (
    ('!xpath //*', XPath),
    ('//*', XPath),
    pytest.mark.xfail(('//[]', XPath), raises=InvalidNode),
    ('!regex .*', pattern_type),
    pytest.mark.xfail(('!regex "*"', pattern_type), raises=InvalidNode),
    ('!settings {included: [], excluded: [], allow_ignore: yes}', Settings),
    pytest.mark.xfail(('!settings {}', Settings), raises=InvalidNode)
))
def test_constructors(expression, expected_type):
    """Ensure custom constructors successfully parse given expressions."""
    assert isinstance(yaml.load(expression), expected_type)


def test_parse_rule():
    """Ensure parse_rule returns expected output."""
    expr = XPath("//Num")
    assert parse_rule(
        rule_name='',
        rule_values=dict(
            description='',
            expr=expr,
            example="a = 1",
            instead="a = int('1')",
            settings=Settings(included=[], excluded=[], allow_ignore=True),
        )
    ) == Rule(
        name='',
        description='',
        expr=expr,
        example="a = 1",
        instead="a = int('1')",
        settings=Settings(included=[], excluded=[], allow_ignore=True)
    )


def test_parse_rule_requires_settings():
    """Ensure parse_rule raises an exception if settings are not provided."""
    with pytest.raises(InvalidNode):
        parse_rule(
            rule_name='',
            rule_values=dict(
                description='',
                expr=XPath("//Num"),
                example="a = 1",
                instead="a = int('1')",
            )
        )


@pytest.mark.parametrize('kwargs', (
    dict(example="a = "),
    dict(instead="a = int('1'"),
))
def test_parse_rule_validates_code_examples(kwargs):
    """
    Ensure parse_rule raises an exception if code examples are syntactically
    invalid.
    """
    with pytest.raises(InvalidNode):
        parse_rule(
            rule_name='',
            rule_values=dict(
                description='',
                expr=XPath("//Num"),
                **kwargs
            )
        )
