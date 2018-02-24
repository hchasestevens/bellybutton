"""Command-line interface."""

from __future__ import print_function

import os
import sys
import argparse

from bellybutton.exceptions import InvalidNode
from bellybutton.parsing import load_config

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from bellybutton.initialization import generate_config


PARSER = argparse.ArgumentParser()
SUBPARSERS = PARSER.add_subparsers()


def success(msg):
    return "\033[92m{}\033[0m".format(msg)


def error(msg):
    return "\033[91m{}\033[0m".format(msg)


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

        args = ['--{}'.format(argument_name)]
        kwargs = dict(
            default=default_value,
            required=False,
        )
        if type(default_value) is bool:
            kwargs['action'] = 'store_{!r}'.format(not default_value).lower()
            args.append('-{}'.format(argument_name[0]))
        else:
            kwargs['type'] = type(default_value)

        command.add_argument(
            *args,
            **kwargs
        )

    return fn


@cli_command
def init(project_directory='.', force=False):
    """Initialize bellybutton config for project."""
    config_path = os.path.join(project_directory, '.bellybutton.yml')
    if os.path.exists(config_path) and not force:
        message = 'ERROR: Path `{}` already initialized (use --force to ignore).'
        print(error(message.format(config_path)))
        return 1

    config = generate_config(
        directory
        for directory in os.listdir(project_directory)
        if os.path.isdir(os.path.join(project_directory, directory))
        and directory.startswith('test')
    )
    with open(config_path, 'w') as f:
        f.write(config)
    return 0


@cli_command
def lint(level='all', project_directory='.', verbose=False):
    """Lint project."""
    config_path = os.path.join(project_directory, '.bellybutton.yml')
    try:
        with open(config_path, 'r') as f:
            rules = load_config(f)
    except IOError:
        message = "ERROR: Configuration file path `{}` does not exist."
        print(error(message.format(config_path)))
        return 1
    except InvalidNode as e:
        message = "ERROR: When parsing {}: {!r}"
        print(error(message.format(config_path, e)))
        return 1
    print(success("Linting succeeded ({} rule{}).".format(
        len(rules),
        '' if len(rules) == 1 else 's'
    )))
    return 0


def main():
    """Entrypoint for CLI."""
    args = PARSER.parse_args()
    exit_code = args.func(**{
        arg: getattr(args, arg)
        for arg in args.func.__code__.co_varnames[:args.func.__code__.co_argcount]
    })
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
