"""Error handling utilities and decorators."""

import functools
import asyncio
from typing import Callable, Any, Optional, Type, Union, Dict
import time
import logging

from .exceptions import (
    BaseOrchestratorError,
    ErrorHandler,
    get_error_handler,
    AgentTimeoutError,
    WorkflowTimeoutError
)


logger = logging.getLogger(__name__)


def handle_errors(
    default_return: Any = None,
    propagate: bool = True,
    log_errors: bool = True,
    recovery: bool = True
):
    """Decorator for handling errors in functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseOrchestratorError as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e.to_dict()}")
                
                if recovery:
                    error_handler = get_error_handler()
                    recovery_options = error_handler.handle_error(e)
                    if recovery_options:
                        logger.info(f"Recovery options available: {recovery_options}")
                
                if propagate:
                    raise
                return default_return
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if propagate:
                    raise
                return default_return
        
        return wrapper
    return decorator


def handle_errors_async(
    default_return: Any = None,
    propagate: bool = True,
    log_errors: bool = True,
    recovery: bool = True
):
    """Async decorator for handling errors in async functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseOrchestratorError as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e.to_dict()}")
                
                if recovery:
                    error_handler = get_error_handler()
                    recovery_options = error_handler.handle_error(e)
                    if recovery_options:
                        logger.info(f"Recovery options available: {recovery_options}")
                
                if propagate:
                    raise
                return default_return
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if propagate:
                    raise
                return default_return
        
        return wrapper
    return decorator


def with_timeout(
    timeout_seconds: int,
    error_class: Type[BaseOrchestratorError] = AgentTimeoutError,
    error_args: tuple = ()
):
    """Decorator to add timeout to functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise error_class(*error_args, timeout_seconds=timeout_seconds)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll use a different approach
            import signal
            
            def timeout_handler(signum, frame):
                raise error_class(*error_args, timeout_seconds=timeout_seconds)
            
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_error(
    max_attempts: int = 3,
    backoff_seconds: int = 1,
    exponential_backoff: bool = True,
    error_types: tuple = (BaseOrchestratorError,)
):
    """Decorator to retry function on specific errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except error_types as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_seconds * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            if last_error:
                raise last_error
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_seconds * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            if last_error:
                raise last_error
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_input(**validators: Dict[str, Callable]):
    """Decorator to validate function inputs."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        from .exceptions import ValidationError
                        raise ValidationError(
                            f"Validation failed for parameter '{param_name}' with value: {value}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_message: str = None,
    **kwargs
) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except BaseOrchestratorError as e:
        logger.error(f"{error_message or 'Error during execution'}: {e.to_dict()}")
        return default_return
    except Exception as e:
        logger.error(f"{error_message or 'Unexpected error'}: {str(e)}")
        return default_return


async def safe_execute_async(
    func: Callable,
    *args,
    default_return: Any = None,
    error_message: str = None,
    **kwargs
) -> Any:
    """Safely execute an async function with error handling."""
    try:
        return await func(*args, **kwargs)
    except BaseOrchestratorError as e:
        logger.error(f"{error_message or 'Error during execution'}: {e.to_dict()}")
        return default_return
    except Exception as e:
        logger.error(f"{error_message or 'Unexpected error'}: {str(e)}")
        return default_return


class ErrorContext:
    """Context manager for error handling."""
    
    def __init__(
        self,
        operation: str,
        propagate: bool = True,
        log_errors: bool = True,
        recovery: bool = True
    ):
        """Initialize error context."""
        self.operation = operation
        self.propagate = propagate
        self.log_errors = log_errors
        self.recovery = recovery
        self.error_handler = get_error_handler()
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with error handling."""
        if exc_val is None:
            return False
        
        if isinstance(exc_val, BaseOrchestratorError):
            if self.log_errors:
                logger.error(f"Error in {self.operation}: {exc_val.to_dict()}")
            
            if self.recovery:
                recovery_options = self.error_handler.handle_error(exc_val)
                if recovery_options:
                    logger.info(f"Recovery options for {self.operation}: {recovery_options}")
            
            return not self.propagate
        
        if self.log_errors:
            logger.error(f"Unexpected error in {self.operation}: {str(exc_val)}")
        
        return not self.propagate