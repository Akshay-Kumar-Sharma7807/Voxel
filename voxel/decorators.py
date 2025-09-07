"""
Decorators for automatic error handling and logging.
"""

import functools
from typing import Callable, Any, Optional, Dict
from .error_handler import ErrorCategory, ErrorSeverity, handle_error, log_system_event
from .exceptions import VoxelError


def handle_errors(category: ErrorCategory, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 component: Optional[str] = None,
                 operation: Optional[str] = None,
                 return_on_error: Any = None,
                 raise_on_critical: bool = True):
    """
    Decorator for automatic error handling.
    
    Args:
        category: Error category for handling strategy
        severity: Error severity level
        component: Component name (defaults to class name)
        operation: Operation name (defaults to method name)
        return_on_error: Value to return if error is handled
        raise_on_critical: Whether to re-raise critical errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Determine component and operation names
                comp_name = component
                op_name = operation or func.__name__
                
                if not comp_name and args and hasattr(args[0], '__class__'):
                    comp_name = args[0].__class__.__name__
                
                # Extract additional data from VoxelError
                additional_data = None
                if isinstance(e, VoxelError):
                    additional_data = e.additional_data
                
                # Handle the error
                can_continue = handle_error(
                    error=e,
                    component=comp_name or "Unknown",
                    operation=op_name,
                    category=category,
                    severity=severity,
                    additional_data=additional_data
                )
                
                # Decide what to do based on handling result
                if not can_continue:
                    if raise_on_critical:
                        raise
                    else:
                        return return_on_error
                
                return return_on_error
        
        return wrapper
    return decorator


def log_operation(level: str = "INFO", 
                 include_args: bool = False,
                 include_result: bool = False):
    """
    Decorator for logging method operations.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        include_args: Whether to log method arguments
        include_result: Whether to log method result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine component name
            component = "Unknown"
            if args and hasattr(args[0], '__class__'):
                component = args[0].__class__.__name__
            
            operation = func.__name__
            
            # Log operation start
            log_data = {"operation": f"{component}.{operation}"}
            if include_args and (args[1:] or kwargs):  # Skip 'self' argument
                log_data["args"] = str(args[1:]) if args[1:] else ""
                log_data["kwargs"] = str(kwargs) if kwargs else ""
            
            log_system_event(f"Starting {operation}", level, **log_data)
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful completion
                success_data = {"operation": f"{component}.{operation}"}
                if include_result and result is not None:
                    success_data["result"] = str(result)[:100]  # Truncate long results
                
                log_system_event(f"Completed {operation}", level, **success_data)
                
                return result
                
            except Exception as e:
                # Log operation failure
                log_system_event(
                    f"Failed {operation}: {str(e)}", 
                    "ERROR", 
                    operation=f"{component}.{operation}"
                )
                raise
        
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, 
                  delay: float = 1.0, 
                  backoff_factor: float = 2.0,
                  exceptions: tuple = (Exception,)):
    """
    Decorator for automatic retry on specific exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Determine component name for logging
                        component = "Unknown"
                        if args and hasattr(args[0], '__class__'):
                            component = args[0].__class__.__name__
                        
                        log_system_event(
                            f"Retry {attempt + 1}/{max_retries} for {component}.{func.__name__}",
                            "WARNING",
                            error=str(e),
                            delay=current_delay
                        )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # Max retries exceeded
                        raise last_exception
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def validate_config(required_attrs: list):
    """
    Decorator to validate that required configuration attributes are set.
    
    Args:
        required_attrs: List of required attribute names
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from .config import SystemConfig
            from .exceptions import ConfigurationError
            
            missing_attrs = []
            for attr in required_attrs:
                if not hasattr(SystemConfig, attr) or getattr(SystemConfig, attr) is None:
                    missing_attrs.append(attr)
            
            if missing_attrs:
                raise ConfigurationError(
                    f"Missing required configuration: {', '.join(missing_attrs)}",
                    component="SystemConfig",
                    additional_data={"missing_attrs": missing_attrs}
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator