"""Linting engine."""

import re
import fnmatch
import tokenize
from collections import namedtuple


Failure = namedtuple('Failure', 'rule filepath lineno')


def get_ignored_lines(file_contents):
    """Get lines to be ignored for linting."""
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
    ignored_lines = get_ignored_lines(file_contents)
    matching_rules = (
        rule
        for rule in rules
        if rule_settings_match(rule, filepath)
    )
    for rule in matching_rules:
        # see if matches
        # if matches, see if rule is ignorable
        # if ignorable, see if line is ignored
        # otherwise, yield failure
        pass
