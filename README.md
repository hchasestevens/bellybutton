# bellybutton

[![Build Status](https://travis-ci.org/hchasestevens/bellybutton.svg?branch=master)](https://travis-ci.org/hchasestevens/bellybutton) [![PyPI version](https://badge.fury.io/py/bellybutton.svg)](https://badge.fury.io/py/bellybutton)

<img src="demo.gif" width="642">

`bellybutton` is a customizable, easy-to-configure linting engine for Python. 

## What is this good for?

Tools like [pylint](https://www.pylint.org/) and [flake8](http://flake8.pycqa.org/en/latest/#) provide, 
out-of-the-box, a wide variety of rules for enforcing Python best practices, ensuring PEP-8 compliance, 
and avoiding frequent sources of bugs. However, many projects have project-specific candidates for 
static analysis, such as internal style guides, areas of deprecated functionality, or common sources 
of error. This is especially true of those projects with many contributors or with large or legacy 
codebases.

`bellybutton` allows custom linting rules to be specified on a per-project basis and detected as part of
your normal build, test and deployment process and, further, makes specifying these rules highly 
accessible, greatly lowering the cost of adoption.

Give `bellybutton` a try if:
* You find yourself often making the same PR comments
* You need a means of gradually deprecating legacy functionality
* You're looking to build a self-enforcing style guide
* Your project needs to onboard new or junior developers more quickly and effectively
* You have Python nitpicks that go beyond what standard linting tools enforce

## Installation & getting started 

`bellybutton` can be installed via:
```bash
pip install bellybutton
```

Once installed, running
```bash
bellybutton init
```
in your project's root directory will create a `.bellybutton.yml` configuration file with an example 
rule for you to begin adapting. `bellybutton` will also try to provide additional rule settings based
on the directory structure of your project.

Once you have configured `bellybutton` for your project, running 
```bash
bellybutton lint
```
will lint the project against the rules specified in your `.bellybutton.yml`. Additionally, running
```bash
bellybutton lint --modified-only
```
will, if using git, only lint those files that differ from `origin/master`.

For adding `bellybutton` to your CI pipeline, take a look at this repository's [tox configuration](tox.ini)
and [.travis.yml](.travis.yml) as an example.

## Concepts

### Rules

Rules in `bellybutton` supply patterns that should be caught and cause linting to fail. Rules as specified
in your `.bellybutton.yml` configuration must consist of:
* A description `description`, expressing the meaning of the rule
* An expression `expr`, specifying the pattern to be caught - either as an 
[astpath](https://github.com/hchasestevens/astpath) expression or as a regular expression.

Additionally, the key used for the rule within the `rules` mapping serves as its name.

Rules may also consist of:
* Settings `settings` that specify on which files the rule is to be enforced, as well as whether it can be
ignored via a `# bb: ignore` comment
* An example `example` of Python code that would be matched by the rule
* A counter-example `instead` of an alternative piece of code, for guiding the developer in fixing their
linting error.

These `example` and `instead` clauses are checked at run-time to ensure that they respectively are and are
matched by the rule's `expr`.

### Settings

`!settings` nodes specify:
* `included` paths on which rules are to be run, using [glob notation](https://docs.python.org/3.6/library/glob.html)
* `excluded` paths on which rules are not to be run (even when matching the `included` paths)
* A boolean `allow_ignore` which determines whether rules can be ignored, providing the line matching the
rule has a `# bb: ignore` comment.

Additionally, at the root level of `.bellybutton.yml`, a `default_settings` setting may be specified which
will be used by rules without explicit settings. Each rule must either have a `settings` parameter or be
able to fall back on the `default_settings`.

## Example usage

Check out this repository's [`.bellybutton.yml`](.bellybutton.yml) as an example `bellybutton` configuration file, 
and [`astpath`'s README](https://github.com/hchasestevens/astpath/blob/master/README.md) for examples of the types 
of patterns you can lint for using `bellybutton`.

## Development status

`bellybutton` is in an alpha release and, as such, is missing some key features, documentation, 
and full test coverage. Further, `bellybutton` is not optimized for performance on extremely large 
codebases and may contain breaking bugs. Please report any bugs encountered.

### Known issues:
* The `--modified-only` flag of `bellybutton lint` is not yet implemented
* The `!chain` and `!verbal` expression nodes are not yet implemented
* Errors in `expr` syntax are not yet caught
* Errors in rule specification are not yet localized to the relevant `.bellybutton.yml` line


## Contacts

* Name: [H. Chase Stevens](http://www.chasestevens.com)
* Twitter: [@hchasestevens](https://twitter.com/hchasestevens)
