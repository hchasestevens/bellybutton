"""YAML parsing."""
import ast
import re
from collections import namedtuple

import yaml
from lxml.etree import XPath
from astpath.search import find_in_ast, file_contents_to_xml_ast

from bellybutton.exceptions import InvalidNode


def constructor(tag=None, pattern=None):
    """Register custom constructor with pyyaml."""
    def decorator(f):
        if tag is None or f is tag:
            tag_ = '!{}'.format(f.__name__)
        else:
            tag_ = tag
        yaml.add_constructor(tag_, f)
        if pattern is not None:
            yaml.add_implicit_resolver(tag_, re.compile(pattern))
        return f
    if callable(tag):  # little convenience hack to avoid empty arg list
        return decorator(tag)
    return decorator


@constructor(pattern=r'/.+')
def xpath(loader, node):
    """Construct XPath expressions."""
    value = loader.construct_scalar(node)
    return XPath(value)


@constructor
def regex(loader, node):
    """Construct regular expressions."""
    value = loader.construct_scalar(node)
    return re.compile(value)


@constructor
def verbal(loader, node):
    """Construct verbal expressions."""
    values = loader.construct_sequence(node)
    pass  # todo: verbal expressions


@constructor
def chain(loader, node):
    """Construct pipelines of other constructors."""
    values = loader.construct_sequence(node)
    pass  # todo: chain constructors (viz. xpath then regex)


Settings = namedtuple('Settings', 'included excluded allow_ignore')


@constructor
def settings(loader, node):
    values = loader.construct_mapping(node)
    try:
        return Settings(**values)
    except TypeError:
        for field in Settings._fields:
            if field not in values:
                raise InvalidNode(
                    "!settings node missing required field `{}`.".format(field)
                )
        raise


Rule = namedtuple('Rule', 'name description expr example instead settings')


def validate_syntax(rule_example):
    try:
        ast.parse(rule_example)
    except SyntaxError as e:
        raise InvalidNode("Invalid syntax in rule example.")


def parse_rule(rule_name, rule_values, default_settings=None):
    rule_description = rule_values.get('description')
    if rule_description is None:
        raise InvalidNode("No rule description provided.")

    rule_expr = rule_values.get('expr')
    if rule_expr is None:
        raise InvalidNode("No rule expression provided.")
    matches = (
        lambda x: find_in_ast(
            file_contents_to_xml_ast(x),
            rule_expr.path,
            return_lines=False
        )
        if isinstance(rule_expr, XPath)
        else x.match
    )

    rule_example = rule_values.get('example')
    if rule_example is not None:
        validate_syntax(rule_example)
        if not matches(rule_example):
            raise InvalidNode("Rule `example` clause is not matched by rule.")

    rule_instead = rule_values.get('instead')
    if rule_instead is not None:
        validate_syntax(rule_instead)
        if matches(rule_instead):
            raise InvalidNode("Rule `instead` clause is matched by rule.")

    rule_settings = rule_values.get('settings', default_settings)
    if rule_settings is None:
        raise InvalidNode("No rule settings or default settings specified.")

    return Rule(
        name=rule_name,
        description=rule_description,
        expr=rule_expr,
        example=rule_example,
        instead=rule_instead,
        settings=rule_settings,
    )


def load_config(fname):
    """Load bellybutton config file, returning a list of rules."""
    loaded = yaml.load(fname)
    default_settings = loaded.get('default_settings')
    return [
        parse_rule(rule_name, rule_values, default_settings)
        for rule_name, rule_values in
        loaded.get('rules', {}).items()
    ]
