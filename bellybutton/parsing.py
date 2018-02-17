"""YAML parsing."""
import re

import yaml
from lxml.etree import XPath


def constructor(tag=None, pattern=None):
    """Register custom constructor with pyyaml."""
    def decorator(f):
        if tag is None or f is tag:
            tag_ = '!{}'.format(f.__name__)
        else:
            tag_ = tag
        yaml.add_constructor(tag_, f)
        if pattern is not None:
            yaml.add_implicit_resolver(tag_, re.compile(pattern))
        return f
    if callable(tag):  # little convenience hack to avoid empty arg list
        return decorator(tag)
    return decorator


@constructor(pattern=r'/.+')
def xpath(loader, node):
    """Construct XPath expressions."""
    value = loader.construct_scalar(node)
    return XPath(value)


@constructor
def regex(loader, node):
    """Construct regular expressions."""
    value = loader.construct_scalar(node)
    return re.compile(value)


@constructor
def verbal(loader, node):
    """Construct verbal expressions."""
    values = loader.construct_sequence(node)
    pass  # todo: verbal expressions


@constructor
def chain(loader, node):
    """Construct pipelines of other constructors."""
    values = loader.construct_sequence(node)
    pass  # todo: chain constructors (viz. xpath then regex)
