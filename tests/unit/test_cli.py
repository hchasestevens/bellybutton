"""Unit tests for bellybutton/cli.py"""

import pytest

from bellybutton import cli


@pytest.mark.parametrize('fn', (
    cli.init,
    cli.lint,
))
@pytest.mark.parametrize('options', (
    ' --project_directory .',
    ' --project_directory=.',
    '',
))
def test_interface_exposes_subcommands(fn, options):
    """Ensure argparse interface exposes expected subcommands."""
    assert cli.PARSER.parse_args(
        '{.__name__}{}'.format(fn, options).split()
    ).func is fn
