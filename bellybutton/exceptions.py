"""Custom exceptions."""
from yaml import YAMLError


class InvalidNode(YAMLError):
    """Raised when a custom node fails validation."""
