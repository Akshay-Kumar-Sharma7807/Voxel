"""
Centralized error handling and logging system for Voxel.
"""

import logging
import logging.handlers
import traceback
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Type
from dataclasses import dataclass

from .config import SystemConfig, ErrorConfig


class ErrorCategory(Enum):
    """Categories of errors for different handling strategies."""
    AUDIO_CAPTURE = "audio_capture"
    SPEECH_PROCESSING = "speech_processing"
    TEXT_ANALYSIS = "text_analysis"
    IMAGE_GENERATION = "image_generation"
    DISPLAY = "display"
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    component: str
    operation: str
    timestamp: datetime
    error_type: str
    error_message: str
    traceback_info: str
    category: ErrorCategory
    severity: ErrorSeverity
    retry_count: int = 0
    additional_data: Optional[Dict[str, Any]] = None


class VoxelLogger:
    """Centralized logging system with structured output."""
    
    def __init__(self):
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Initialize logging with rotating file handler."""
        # Ensure logs directory exists
        SystemConfig.LOGS_DIR.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('voxel')
        self.logger.setLevel(getattr(logging, SystemConfig.LOG_LEVEL))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        log_file = SystemConfig.LOGS_DIR / SystemConfig.LOG_FILE
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=SystemConfig.MAX_LOG_SIZE,
            backupCount=SystemConfig.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Error file handler for errors only
        error_file = SystemConfig.LOGS_DIR / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=SystemConfig.MAX_LOG_SIZE,
            backupCount=SystemConfig.LOG_BACKUP_COUNT
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
    
    def log_error(self, error_context: ErrorContext):
        """Log error with structured context."""
        error_msg = (
            f"[{error_context.category.value.upper()}] "
            f"{error_context.component}.{error_context.operation} - "
            f"{error_context.error_message}"
        )
        
        if error_context.additional_data:
            error_msg += f" | Data: {error_context.additional_data}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error_msg)
            self.logger.critical(f"Traceback: {error_context.traceback_info}")
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(error_msg)
            self.logger.debug(f"Traceback: {error_context.traceback_info}")
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(error_msg)
        else:
            self.logger.info(error_msg)
    
    def log_recovery(self, component: str, operation: str, retry_count: int):
        """Log successful error recovery."""
        self.logger.info(
            f"[RECOVERY] {component}.{operation} - "
            f"Recovered after {retry_count} retries"
        )
    
    def log_system_event(self, event: str, level: str = "INFO", **kwargs):
        """Log general system events."""
        msg = f"[SYSTEM] {event}"
        if kwargs:
            msg += f" | {kwargs}"
        
        getattr(self.logger, level.lower())(msg)


class ErrorHandler:
    """Centralized error handling with recovery strategies."""
    
    def __init__(self):
        self.logger = VoxelLogger()
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.AUDIO_CAPTURE: self._handle_audio_error,
            ErrorCategory.SPEECH_PROCESSING: self._handle_speech_error,
            ErrorCategory.TEXT_ANALYSIS: self._handle_analysis_error,
            ErrorCategory.IMAGE_GENERATION: self._handle_generation_error,
            ErrorCategory.DISPLAY: self._handle_display_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.AUTHENTICATION: self._handle_auth_error,
            ErrorCategory.CONFIGURATION: self._handle_config_error,
            ErrorCategory.SYSTEM: self._handle_system_error,
        }
    
    def handle_error(self, 
                    error: Exception, 
                    component: str, 
                    operation: str, 
                    category: ErrorCategory,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle an error with appropriate recovery strategy.
        
        Returns:
            bool: True if error was handled and operation can continue, False if critical
        """
        # Create error context
        error_context = ErrorContext(
            component=component,
            operation=operation,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_info=traceback.format_exc(),
            category=category,
            severity=severity,
            additional_data=additional_data
        )
        
        # Log the error
        self.logger.log_error(error_context)
        
        # Track error count for this component
        error_key = f"{component}.{operation}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Check if we've exceeded max consecutive errors
        if self.error_counts[error_key] > ErrorConfig.MAX_CONSECUTIVE_ERRORS:
            self.logger.log_system_event(
                f"Max consecutive errors exceeded for {error_key}",
                level="CRITICAL"
            )
            if ErrorConfig.CRITICAL_ERROR_EXIT:
                return False
        
        # Apply recovery strategy
        recovery_func = self.recovery_strategies.get(category, self._default_recovery)
        can_continue = recovery_func(error_context)
        
        if can_continue:
            # Reset error count on successful recovery
            self.error_counts[error_key] = 0
            self.logger.log_recovery(component, operation, error_context.retry_count)
        
        return can_continue
    
    def _handle_audio_error(self, error_context: ErrorContext) -> bool:
        """Handle audio capture errors."""
        if "permission" in error_context.error_message.lower():
            self.logger.log_system_event(
                "Audio permission denied - check microphone permissions",
                level="ERROR"
            )
            return False
        
        if "device" in error_context.error_message.lower():
            self.logger.log_system_event(
                f"Microphone device error - retrying in {ErrorConfig.ERROR_RECOVERY_DELAY}s",
                level="WARNING"
            )
            time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
            return True
        
        # Default audio recovery
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        return True
    
    def _handle_speech_error(self, error_context: ErrorContext) -> bool:
        """Handle speech processing errors."""
        if "model" in error_context.error_message.lower():
            self.logger.log_system_event(
                "Speech model error - this may be critical",
                level="ERROR"
            )
            return False
        
        # Skip current audio chunk and continue
        return True
    
    def _handle_analysis_error(self, error_context: ErrorContext) -> bool:
        """Handle text analysis errors."""
        # Analysis errors are usually not critical
        self.logger.log_system_event(
            "Text analysis failed - skipping current text",
            level="WARNING"
        )
        return True
    
    def _handle_generation_error(self, error_context: ErrorContext) -> bool:
        """Handle image generation errors."""
        if "rate limit" in error_context.error_message.lower():
            self.logger.log_system_event(
                "API rate limit hit - waiting before retry",
                level="WARNING"
            )
            time.sleep(60)  # Wait 1 minute for rate limit
            return True
        
        if "authentication" in error_context.error_message.lower():
            self.logger.log_system_event(
                "API authentication failed - check API key",
                level="ERROR"
            )
            return False
        
        # Network or temporary API issues
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        return True
    
    def _handle_display_error(self, error_context: ErrorContext) -> bool:
        """Handle display errors."""
        self.logger.log_system_event(
            "Display error - continuing without display update",
            level="WARNING"
        )
        return True
    
    def _handle_network_error(self, error_context: ErrorContext) -> bool:
        """Handle network-related errors."""
        self.logger.log_system_event(
            f"Network error - retrying in {ErrorConfig.ERROR_RECOVERY_DELAY}s",
            level="WARNING"
        )
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        return True
    
    def _handle_auth_error(self, error_context: ErrorContext) -> bool:
        """Handle authentication errors."""
        self.logger.log_system_event(
            "Authentication error - check API credentials",
            level="ERROR"
        )
        return False
    
    def _handle_config_error(self, error_context: ErrorContext) -> bool:
        """Handle configuration errors."""
        self.logger.log_system_event(
            "Configuration error - check system setup",
            level="ERROR"
        )
        return False
    
    def _handle_system_error(self, error_context: ErrorContext) -> bool:
        """Handle general system errors."""
        if error_context.severity == ErrorSeverity.CRITICAL:
            return False
        
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        return True
    
    def _default_recovery(self, error_context: ErrorContext) -> bool:
        """Default recovery strategy."""
        if error_context.severity == ErrorSeverity.CRITICAL:
            return False
        
        time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        return True


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(error: Exception, 
                component: str, 
                operation: str, 
                category: ErrorCategory,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                additional_data: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function for error handling."""
    return error_handler.handle_error(
        error, component, operation, category, severity, additional_data
    )


def log_system_event(event: str, level: str = "INFO", **kwargs):
    """Convenience function for system event logging."""
    error_handler.logger.log_system_event(event, level, **kwargs)

def setup_logging(log_level: str = "INFO", 
                 log_file: str = None, 
                 max_size: int = None, 
                 backup_count: int = None):
    """
    Setup application logging with the specified configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        max_size: Maximum log file size in bytes
        backup_count: Number of backup log files to keep
    """
    # Update SystemConfig if parameters provided
    if log_level:
        SystemConfig.LOG_LEVEL = log_level
    if log_file:
        SystemConfig.LOG_FILE = Path(log_file).name
        SystemConfig.LOGS_DIR = Path(log_file).parent
    if max_size:
        SystemConfig.MAX_LOG_SIZE = max_size
    if backup_count:
        SystemConfig.LOG_BACKUP_COUNT = backup_count
    
    # Initialize the global error handler (which sets up logging)
    global error_handler
    error_handler = ErrorHandler()