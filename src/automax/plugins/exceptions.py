"""
Custom exception hierarchy for plugin error handling.

This module defines standardized exceptions for plugin configuration, execution, and
validation errors.

"""

from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class PluginError(Exception):
    """
    Base exception for all plugin-related errors.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.plugin_name = plugin_name
        self.config = config or {}
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        String representation of the error.
        """
        base_message = f"PluginError: {self.message}"
        if self.plugin_name:
            base_message = f"[{self.plugin_name}] {base_message}"
        return base_message

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for serialization.

        Returns:
            Dictionary containing error details

        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "plugin_name": self.plugin_name,
            "config": {
                k: v
                for k, v in self.config.items()
                if not isinstance(v, (str, int, float, bool)) or len(str(v)) < 100
            },
        }


class PluginConfigurationError(PluginError):
    """
    Raised when plugin configuration is invalid or incomplete.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        missing_keys: Optional[List[str]] = None,
        invalid_keys: Optional[List[str]] = None,
    ):
        super().__init__(message, plugin_name, config, original_error)
        self.missing_keys = missing_keys or []
        self.invalid_keys = invalid_keys or []

    def __str__(self) -> str:
        """
        String representation with configuration details.
        """
        base_message = super().__str__()
        details = []
        if self.missing_keys:
            details.append(f"missing keys: {self.missing_keys}")
        if self.invalid_keys:
            details.append(f"invalid keys: {self.invalid_keys}")
        if details:
            return f"{base_message} ({', '.join(details)})"
        return base_message


class PluginExecutionError(PluginError):
    """
    Raised when plugin execution fails.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        execution_step: Optional[str] = None,
    ):
        super().__init__(message, plugin_name, config, original_error)
        self.execution_step = execution_step

    def __str__(self) -> str:
        """
        String representation with execution context.
        """
        base_message = super().__str__()
        if self.execution_step:
            return f"{base_message} (step: {self.execution_step})"
        return base_message


class PluginValidationError(PluginError):
    """
    Raised when plugin validation fails.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        validation_errors: Optional[List[str]] = None,
    ):
        super().__init__(message, plugin_name, config, original_error)
        self.validation_errors = validation_errors or []

    def __str__(self) -> str:
        """
        String representation with validation details.
        """
        base_message = super().__str__()
        if self.validation_errors:
            errors = "; ".join(self.validation_errors)
            return f"{base_message} (validation errors: {errors})"
        return base_message


class PluginSecurityError(PluginError):
    """
    Raised when security constraints are violated.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        security_context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, plugin_name, config, original_error)
        self.security_context = security_context or {}

    def __str__(self) -> str:
        """
        String representation with security context.
        """
        base_message = super().__str__()
        if self.security_context:
            context_str = ", ".join(
                f"{k}={v}" for k, v in self.security_context.items()
            )
            return f"{base_message} (security context: {context_str})"
        return base_message


def handle_plugin_errors(plugin_name: str) -> Callable[[F], F]:
    """
    Decorator for automatic plugin error handling.

    Args:
        plugin_name: Name of the plugin for error context

    Returns:
        Decorated function with error handling

    """

    def decorator(func: F) -> F:
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except PluginError:
                raise
            except Exception as e:
                raise PluginExecutionError(
                    message=f"Unexpected error: {str(e)}",
                    plugin_name=plugin_name,
                    config=getattr(self, "config", {}),
                    original_error=e,
                ) from e

        return wrapper

    return decorator
