"""Command-line interface."""

import sys
import argparse

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


PARSER = argparse.ArgumentParser()
SUBPARSERS = PARSER.add_subparsers()


def cli_command(fn):
    """Register function as subcommand."""
    command = SUBPARSERS.add_parser(fn.__name__, description=fn.__doc__)
    unspecified = object()
    args = reversed(list(zip_longest(
        reversed(fn.__code__.co_varnames),
        reversed(fn.__defaults__),
        fillvalue=unspecified
    )))
    for argument_name, default_value in args:
        if default_value is unspecified:
            command.add_argument(argument_name, required=True)
            continue
        command.add_argument(
            '--{}'.format(argument_name),
            default=default_value,
            required=False
        )
    command.set_defaults(func=fn)
    return fn


@cli_command
def init(project_directory='.'):
    """Intiialize bellybutton config for project."""


@cli_command
def lint(level='all', project_directory='.'):
    """Lint project."""
    sys.exit(0)


if __name__ == '__main__':
    ARGS = PARSER.parse_args()
    ARGS.func(**{
        arg: getattr(ARGS, arg)
        for arg in ARGS.func.__code__.co_varnames
    })
