"""YAML parsing."""
import re
import ast
import functools
from collections import namedtuple

import os
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


def _reraise_with_line_no(fn):
    @functools.wraps(fn)
    def wrapper(loader, node):
        try:
            return fn(loader, node)
        except Exception as e:
            msg = getattr(e, 'message', str(e))
            raise InvalidNode(
                "line {}: {}.".format(node.start_mark.line + 1, msg)
            )
    return wrapper


@constructor(pattern=r'\~\+[/\\].+')
@_reraise_with_line_no
def glob(loader, node):
    """Construct glob expressions."""
    value = loader.construct_scalar(node)[len('~+/'):]
    return os.path.join(
        os.path.dirname(loader.name),
        value
    )


# todo - all exprs return (parsed_expr, contents -> {lines})?

@constructor(pattern=r'/.+')
@_reraise_with_line_no
def xpath(loader, node):
    """Construct XPath expressions."""
    value = loader.construct_scalar(node)
    return XPath(value)


@constructor
@_reraise_with_line_no
def regex(loader, node):
    """Construct regular expressions."""
    value = loader.construct_scalar(node)
    return re.compile(value, re.MULTILINE)


@constructor
@_reraise_with_line_no
def verbal(loader, node):
    """Construct verbal expressions."""
    values = loader.construct_sequence(node)
    pass  # todo: verbal expressions


@constructor
@_reraise_with_line_no
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


def validate_syntax(rule_clause, clause_type):
    try:
        ast.parse(rule_clause)
    except SyntaxError as e:
        raise InvalidNode("Invalid syntax in `{}` clause.".format(clause_type))


def _reraise_with_rule_name(fn):
    @functools.wraps(fn)
    def wrapper(rule_name, *args, **kwargs):
        try:
            return fn(rule_name, *args, **kwargs)
        except Exception as e:
            msg = getattr(e, 'message', str(e))
            raise InvalidNode("rule `{}`: {}".format(rule_name, msg))
    return wrapper


@_reraise_with_rule_name
def parse_rule(rule_name, rule_values, default_settings=None):
    rule_description = rule_values.get('description')
    if rule_description is None:
        raise InvalidNode("No description provided.")

    rule_expr = rule_values.get('expr')
    if rule_expr is None:
        raise InvalidNode("No expression provided.".format(rule_name))
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
        validate_syntax(rule_example, clause_type='example')
        if not matches(rule_example):
            raise InvalidNode("`example` clause is not matched by expression.")

    rule_instead = rule_values.get('instead')
    if rule_instead is not None:
        validate_syntax(rule_instead, clause_type='instead')
        if matches(rule_instead):
            raise InvalidNode("`instead` clause is matched by expression.")

    rule_settings = rule_values.get('settings', default_settings)
    if rule_settings is None:
        raise InvalidNode("No settings or default settings specified.")
    if not isinstance(rule_settings, Settings):
        raise InvalidNode("Settings must be a !settings node.")

    return Rule(
        name=rule_name,
        description=rule_description,
        expr=rule_expr,
        example=rule_example,
        instead=rule_instead,
        settings=rule_settings,
    )


def load_config(fileobj):
    """Load bellybutton config file, returning a list of rules."""
    loaded = yaml.load(fileobj)
    default_settings = loaded.get('default_settings')
    rules = [
        parse_rule(rule_name, rule_values, default_settings)
        for rule_name, rule_values in
        loaded.get('rules', {}).items()
    ]
    return rules
