"""Command-line interface."""

from __future__ import print_function

import os
import sys
import argparse
from textwrap import dedent

from bellybutton.exceptions import InvalidNode
from bellybutton.linting import lint_file
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


def walk_python_files(root_dir):
    """
    Walk the specified directory, yielding (path, content) pairs for python
    source files.
    """
    filepaths = (
        os.path.join(root, fname)
        for root, _, fnames in os.walk(root_dir)
        for fname in fnames
        if os.path.splitext(fname)[-1] == '.py'
    )
    for filepath in sorted(filepaths):
        with open(filepath, 'r') as f:
            contents = f.read()
        yield filepath, contents


@cli_command
def lint(modified_only=False, project_directory='.', verbose=False):
    """Lint project."""
    config_path = os.path.abspath(
        os.path.join(project_directory, '.bellybutton.yml')
    )
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

    if verbose:
        failure_message = dedent("""
        \033[95m{path}:{lineno}\033[0m\t\033[1;95;4m{rule.name}\033[0m
        \033[1mDescription\033[0m: {rule.description}
        \033[1mLine\033[0m:
        {line}
        \033[1mExample\033[0m:
        {rule.example}
        \033[1mInstead\033[0m:
        {rule.instead}
        """).lstrip()
    else:
        failure_message = "{path}:{lineno}\t{rule.name}: {rule.description}"

    num_files = 0
    failures = 0
    files = walk_python_files(os.path.abspath(project_directory))
    for filepath, file_contents in files:
        relpath = os.path.relpath(filepath, project_directory)
        linting_results = list(lint_file(filepath, file_contents, rules))
        if not linting_results:
            continue
        num_files += 1
        failure_results = (
            result
            for result in linting_results
            if not result.succeeded
        )
        for failure in failure_results:
            failures += 1
            print(failure_message.format(
                path=relpath,
                lineno=failure.lineno,
                line=file_contents.splitlines()[failure.lineno - 1],
                rule=failure.rule,
            ))

    final_message = "Linting {} ({} rule{}, {} file{}, {} violation{}).".format(
        'failed' if failures else 'succeeded',
        len(rules),
        '' if len(rules) == 1 else 's',
        num_files,
        '' if num_files == 1 else 's',
        failures,
        '' if failures == 1 else 's',
    )
    print((error if failures else success)(final_message))
    return 1 if failures else 0


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
