"""Base provider interface for the podcast generator."""

from abc import ABC, abstractmethod


class Provider(ABC):
    """Abstract base class for all providers."""

    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize the provider with optional configuration."""
        pass
