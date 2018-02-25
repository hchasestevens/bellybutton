"""Initialization of new bellybutton configuration files."""

import os


INIT_TEMPLATE = '''settings:
  all_files: &all_files !settings
    included:
      - ~+/*
    excluded:
      - ~+/.tox/*
    allow_ignore: yes
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
    excluded: 
      - ~+/.tox/*
    allow_ignore: yes

  excluding_tests: &excluding_tests !settings
    included:
      - ~+/*
    excluded:
      {test_dirs}
      - ~+/.tox/*
    allow_ignore: yes
"""


def generate_config(test_directories):
    """Generate configuration, given test directories."""
    test_dirs_block = '\n      '.join(
        "- ~+/{}".format(os.path.join(test_dir, '*'))
        for test_dir in test_directories
    )
    if test_dirs_block:
        test_settings = TESTS_SETTINGS_TEMPLATE.format(
            test_dirs=test_dirs_block
        )
    else:
        test_settings = ''
    config = INIT_TEMPLATE.format(
        test_block=test_settings,
        default_settings='excluding_tests' if test_settings else 'all_files'
    )
    return config
