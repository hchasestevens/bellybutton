"""Command-line interface."""

from __future__ import print_function

import os
import sys
import argparse
import subprocess
from collections import namedtuple
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


LintingFailure = namedtuple('LintingFailure', 'failure path lineno line rule')


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
        argument_name = argument_name.replace('_', '-')
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
    """Walk the specified directory, yielding paths for python source files."""
    return (
        os.path.join(root, fname)
        for root, _, fnames in os.walk(root_dir)
        for fname in fnames
        if os.path.splitext(fname)[-1] == '.py'
    )


def open_python_files(filepaths):
    """For each specified filepath, yield (path, content) pairs."""
    for filepath in sorted(filepaths):
        with open(filepath, 'r') as f:
            contents = f.read()
        yield filepath, contents


def get_git_modified(project_directory):
    """Get all modified filepaths between current ref and origin/master."""
    subprocess.check_call(
        'git -C "{}" fetch origin'.format(project_directory),
        shell=True
    )
    diff_cmd = 'git -C "{}" diff {{}} --name-only'.format(os.path.abspath(project_directory))
    return frozenset(
        os.path.abspath(path)
        for diff in ('--staged', 'origin/master...')
        for path in subprocess.check_output(
            diff_cmd.format(diff),
            shell=True
        ).decode('utf-8').strip().splitlines()
    )


def linting_failures(filepaths, rules):
    """Given a set of filepaths and a set of rules, yield all rule violations."""
    failures = 0
    files = open_python_files(filepaths)
    for filepath, file_contents in files:
        linting_results = list(lint_file(filepath, file_contents, rules))
        if not linting_results:
            continue
        failure_results = (
            result
            for result in linting_results
            if not result.succeeded
        )
        for failure in failure_results:
            failures += 1
            lines = file_contents.splitlines()
            yield LintingFailure(
                failure=failure,
                path=filepath,
                lineno=failure.lineno,
                line=lines[min(failure.lineno, len(lines)) - 1] if lines else '',
                rule=failure.rule,
            )


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
        message = "ERROR: {}, {}"
        exc_message = getattr(e, 'message', str(e))
        print(error(message.format(config_path, exc_message)))
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

    failures = 0
    filepath_source = get_git_modified if modified_only else walk_python_files
    filepaths = list(filepath_source(os.path.abspath(project_directory)))
    for failure in linting_failures(filepaths, rules):
        failures += 1
        print(failure_message.format(
            path=os.path.relpath(failure.path, project_directory),
            lineno=failure.lineno,
            line=failure.line,
            rule=failure.rule
        ))

    final_message = "Linting {} ({} rule{}, {} file{}, {} violation{}).".format(
        'failed' if failures else 'succeeded',
        len(rules),
        '' if len(rules) == 1 else 's',
        len(filepaths),
        '' if len(filepaths) == 1 else 's',
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
