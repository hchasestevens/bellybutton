"""Integration tests for bellybutton/parsing.py."""

import os

import pytest

from bellybutton.parsing import load_config


@pytest.mark.parametrize('file', [
    os.path.join(os.path.dirname(__file__), 'examples', fname)
    for fname in os.listdir(
        os.path.join(os.path.dirname(__file__), 'examples')
    )
    if fname.endswith('.yml')
])
def test_loadable(file):
    """Ensure that bellybutton is able to parse configuration."""
    with open(file, 'r') as f:
        assert isinstance(load_config(f), list)
