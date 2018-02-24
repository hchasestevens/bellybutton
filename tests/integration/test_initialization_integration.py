"""Integration tests for bellybutton/initialization.py"""

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

import pytest

from bellybutton import initialization, parsing


@pytest.mark.parametrize('test_dirs', (
    [],
    ['test'],
    ['test', 'tests'],
))
def test_generate_config_parseable(test_dirs):
    """Ensure configuration produced by generate_config is parseable."""
    config = initialization.generate_config(test_dirs)
    stream = BytesIO()
    stream.write(config.encode('utf-8'))
    stream.seek(0)
    assert parsing.load_config(stream)
