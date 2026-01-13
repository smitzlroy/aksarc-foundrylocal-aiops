"""Custom exception classes for the application."""


class AIOperatorException(Exception):
    """Base exception for all application errors."""

    pass


class KubernetesError(AIOperatorException):
    """Raised when Kubernetes operations fail."""

    pass


class KubernetesConnectionError(KubernetesError):
    """Raised when unable to connect to Kubernetes cluster."""

    pass


class KubernetesPermissionError(KubernetesError):
    """Raised when lacking permissions for Kubernetes operation."""

    pass


class FoundryError(AIOperatorException):
    """Raised when Foundry Local operations fail."""

    pass


class FoundryConnectionError(FoundryError):
    """Raised when unable to connect to Foundry Local."""

    pass


class FoundryTimeoutError(FoundryError):
    """Raised when Foundry query times out."""

    pass


class ContextBufferError(AIOperatorException):
    """Raised when context buffer operations fail."""

    pass


class ContextBufferFullError(ContextBufferError):
    """Raised when context buffer is full."""

    pass
