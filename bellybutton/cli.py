"""Command-line interface."""

from __future__ import print_function

import os
import sys
import argparse

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


PARSER = argparse.ArgumentParser()
SUBPARSERS = PARSER.add_subparsers()


INIT_TEMPLATE = '''
settings:
  all_files: &all_files !settings
    included:
      - "*"
    excluded: []
{test_block}
default_settings: *{default_settings}

rules:
  ExampleRule:
    description: "Empty module."
    expr: /Module/body[not(./*)]
    example: ""
    instead: |
      """This module has a docstring."""
'''

TESTS_SETTINGS_TEMPLATE = """
  tests_only: &tests_only !settings
    included:
      {test_dirs}
    excluded: []

  excluding_tests: &excluding_tests !settings
    included:
      - "*"
    excluded:
      {test_dirs}
"""

TEST_DIR_TEMPLATE = "- tests/*"


def cli_command(fn):
    """Register function as subcommand."""
    command = SUBPARSERS.add_parser(fn.__name__, description=fn.__doc__)
    command.set_defaults(func=fn)

    unspecified = object()
    args = reversed(list(zip_longest(
        reversed(fn.__code__.co_varnames[:fn.__code__.co_argcount]),
        reversed(fn.__defaults__),
        fillvalue=unspecified
    )))
    for argument_name, default_value in args:
        if default_value is unspecified:
            command.add_argument(argument_name)
            continue

        kwargs = dict(
            default=default_value,
            required=False,
        )
        if type(default_value) is bool:
            kwargs['action'] = 'store_{!r}'.format(not default_value).lower()
        else:
            kwargs['type'] = type(default_value)

        command.add_argument(
            '--{}'.format(argument_name),
            **kwargs
        )

    return fn


@cli_command
def init(project_directory='.', force=False):
    """Initialize bellybutton config for project."""
    config_path = os.path.join(project_directory, '.bellybutton.yml')
    if os.path.exists(config_path) and not force:
        print('ERROR: Path `{}` already initialized (use --force to ignore).'.format(config_path))
        return 1

    test_directories = [
        os.path.join(project_directory, d)
        for d in os.listdir(project_directory)
        if os.path.isdir(os.path.join(project_directory, d))
        and d.startswith('test')
    ]
    if test_directories:
        test_settings = TESTS_SETTINGS_TEMPLATE.format(
            test_dirs='\n      '.join(
                test_directories
            )
        )
    else:
        test_settings = ''

    config = INIT_TEMPLATE.format(
        test_block=test_settings,
        default_settings='excluding_tests' if test_directories else 'all_files'
    )
    with open(config_path, 'w') as f:
        f.write(config)
    return 0


@cli_command
def lint(level='all', project_directory='.'):
    """Lint project."""
    return 0


def main():
    """Entrypoint for CLI."""
    args = PARSER.parse_args()
    exit_code = args.func(**{
        arg: getattr(args, arg)
        for arg in args.func.__code__.co_varnames
    })
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
