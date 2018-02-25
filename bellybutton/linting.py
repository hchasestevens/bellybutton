"""Linting engine."""

import re
import fnmatch
import tokenize
from collections import namedtuple
from operator import attrgetter

from astpath import find_in_ast, file_contents_to_xml_ast
from lxml.etree import XPath

LintingResult = namedtuple('LintingResult', 'rule filepath succeeded lineno')


def get_ignored_lines(file_contents):
    """Return set of line numbers to be ignored when linting."""
    it = iter(file_contents.splitlines(True))
    tokens = tokenize.generate_tokens(lambda: next(it))
    return frozenset(
        line
        for token_type, token, (line, _), _, _ in tokens
        if token_type is tokenize.COMMENT
        if re.search(r'bb:\s?ignore', token)
    )


def rule_settings_match(rule, filepath):
    """Return whether rule should be executed on file."""
    should_be_included = any(
        fnmatch.fnmatch(filepath, included_pattern)
        for included_pattern in rule.settings.included
    )
    should_be_excluded = any(
        fnmatch.fnmatch(filepath, excluded_pattern)
        for excluded_pattern in rule.settings.excluded
    )
    return should_be_included and not should_be_excluded


def lint_file(filepath, file_contents, rules):
    """Run rules against file, yielding any failures."""
    matching_rules = [
        rule
        for rule in rules
        if rule_settings_match(rule, filepath)
    ]
    if not matching_rules:
        return

    ignored_lines = get_ignored_lines(file_contents)
    xml_ast = file_contents_to_xml_ast(file_contents)  # todo - use caching module?

    for rule in sorted(matching_rules, key=attrgetter('name')):
        # TODO - hacky - need to find better way to do this (while keeping chain)
        # TODO - possibly having both filepath and contents/input supplied?
        if isinstance(rule.expr, XPath):
            matching_lines = set(find_in_ast(
                xml_ast,
                rule.expr.path,
                return_lines=True
            ))
        elif isinstance(rule.expr, re._pattern_type):
            matching_lines = {
                file_contents[:match.start()].count('\n') + 1  # TODO - slow
                for match in re.finditer(rule.expr)
            }
        elif callable(rule.expr):
            matching_lines = set(rule.expr(file_contents))
        else:
            continue  # todo - maybe throw here?

        if rule.settings.allow_ignore:
            matching_lines -= ignored_lines

        if not matching_lines:
            yield LintingResult(rule, filepath, succeeded=True, lineno=None)

        for line in matching_lines:
            yield LintingResult(rule, filepath, succeeded=False, lineno=line)
