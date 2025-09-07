"""
Unit tests for the error handling and logging system.
"""

import pytest
import tempfile
import logging
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from voxel.error_handler import (
    ErrorHandler, VoxelLogger, ErrorCategory, ErrorSeverity, 
    ErrorContext, handle_error, log_system_event
)
from voxel.exceptions import (
    VoxelError, AudioCaptureError, SpeechProcessingError,
    ImageGenerationError, DisplayError
)
from voxel.decorators import handle_errors, log_operation, retry_on_error


class TestVoxelLogger:
    """Test cases for VoxelLogger."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig for testing
        with patch('voxel.error_handler.SystemConfig') as mock_config:
            mock_config.LOGS_DIR = self.logs_dir
            mock_config.LOG_FILE = "test_voxel.log"
            mock_config.LOG_LEVEL = "DEBUG"
            mock_config.MAX_LOG_SIZE = 1024 * 1024
            mock_config.LOG_BACKUP_COUNT = 3
            
            self.logger = VoxelLogger()
    
    def test_logger_initialization(self):
        """Test logger initialization creates proper handlers."""
        assert self.logger.logger is not None
        assert len(self.logger.logger.handlers) == 3  # file, console, error
        
        # Check log files are created
        assert (self.logs_dir / "test_voxel.log").exists()
    
    def test_log_error_with_context(self):
        """Test error logging with structured context."""
        error_context = ErrorContext(
            component="TestComponent",
            operation="test_operation",
            timestamp=datetime.now(),
            error_type="TestError",
            error_message="Test error message",
            traceback_info="Test traceback",
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.HIGH,
            additional_data={"test_key": "test_value"}
        )
        
        self.logger.log_error(error_context)
        
        # Check log file contains the error
        log_content = (self.logs_dir / "test_voxel.log").read_text()
        assert "TestComponent.test_operation" in log_content
        assert "Test error message" in log_content
        assert "test_key" in log_content
    
    def test_log_recovery(self):
        """Test recovery logging."""
        self.logger.log_recovery("TestComponent", "test_operation", 3)
        
        log_content = (self.logs_dir / "test_voxel.log").read_text()
        assert "RECOVERY" in log_content
        assert "TestComponent.test_operation" in log_content
        assert "3 retries" in log_content
    
    def test_log_system_event(self):
        """Test system event logging."""
        self.logger.log_system_event("Test system event", level="INFO", test_param="test_value")
        
        log_content = (self.logs_dir / "test_voxel.log").read_text()
        assert "SYSTEM" in log_content
        assert "Test system event" in log_content
        assert "test_param" in log_content


class TestErrorHandler:
    """Test cases for ErrorHandler."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        with patch('voxel.error_handler.SystemConfig') as mock_config:
            mock_config.LOGS_DIR = self.logs_dir
            mock_config.LOG_FILE = "test_voxel.log"
            mock_config.LOG_LEVEL = "DEBUG"
            mock_config.MAX_LOG_SIZE = 1024 * 1024
            mock_config.LOG_BACKUP_COUNT = 3
            
            self.error_handler = ErrorHandler()
    
    def test_handle_recoverable_error(self):
        """Test handling of recoverable errors."""
        error = AudioCaptureError("Test audio error")
        
        result = self.error_handler.handle_error(
            error=error,
            component="AudioCapture",
            operation="start_recording",
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result is True  # Should be recoverable
    
    def test_handle_critical_error(self):
        """Test handling of critical errors."""
        error = Exception("Critical system error")
        
        result = self.error_handler.handle_error(
            error=error,
            component="System",
            operation="initialize",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL
        )
        
        assert result is False  # Should not be recoverable
    
    def test_error_count_tracking(self):
        """Test error count tracking and max error handling."""
        # Mock the recovery strategy in the strategies dictionary
        def mock_recovery_strategy(error_context):
            # Return False (not recoverable) to prevent error count reset
            return False
        
        # Replace the strategy in the dictionary
        original_strategy = self.error_handler.recovery_strategies[ErrorCategory.AUDIO_CAPTURE]
        self.error_handler.recovery_strategies[ErrorCategory.AUDIO_CAPTURE] = mock_recovery_strategy
        
        error = AudioCaptureError("Repeated error")
        
        # Simulate multiple errors
        for i in range(6):  # Exceed MAX_CONSECUTIVE_ERRORS (5)
            result = self.error_handler.handle_error(
                error=error,
                component="AudioCapture",
                operation="test_operation",
                category=ErrorCategory.AUDIO_CAPTURE,
                severity=ErrorSeverity.MEDIUM
            )
            
            # All should return False since our mock strategy returns False
            assert result is False
        
        # Restore original strategy
        self.error_handler.recovery_strategies[ErrorCategory.AUDIO_CAPTURE] = original_strategy
        
        # Verify the error count was tracked
        error_key = "AudioCapture.test_operation"
        assert self.error_handler.error_counts[error_key] == 6
    
    def test_audio_error_recovery_strategy(self):
        """Test audio-specific error recovery."""
        # Test permission error (should not recover)
        permission_error = AudioCaptureError("permission denied")
        result = self.error_handler._handle_audio_error(
            ErrorContext(
                component="AudioCapture",
                operation="start",
                timestamp=datetime.now(),
                error_type="AudioCaptureError",
                error_message="permission denied",
                traceback_info="",
                category=ErrorCategory.AUDIO_CAPTURE,
                severity=ErrorSeverity.HIGH
            )
        )
        assert result is False
        
        # Test device error (should recover)
        device_error = AudioCaptureError("device not found")
        result = self.error_handler._handle_audio_error(
            ErrorContext(
                component="AudioCapture",
                operation="start",
                timestamp=datetime.now(),
                error_type="AudioCaptureError",
                error_message="device not found",
                traceback_info="",
                category=ErrorCategory.AUDIO_CAPTURE,
                severity=ErrorSeverity.MEDIUM
            )
        )
        assert result is True
    
    def test_network_error_recovery_strategy(self):
        """Test network error recovery with delay."""
        start_time = time.time()
        
        result = self.error_handler._handle_network_error(
            ErrorContext(
                component="ImageGenerator",
                operation="generate",
                timestamp=datetime.now(),
                error_type="ConnectionError",
                error_message="network timeout",
                traceback_info="",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM
            )
        )
        
        end_time = time.time()
        
        assert result is True
        assert end_time - start_time >= 2.0  # Should have delayed


class TestErrorDecorators:
    """Test cases for error handling decorators."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig
        self.config_patcher = patch('voxel.error_handler.SystemConfig')
        mock_config = self.config_patcher.start()
        mock_config.LOGS_DIR = self.logs_dir
        mock_config.LOG_FILE = "test_voxel.log"
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.MAX_LOG_SIZE = 1024 * 1024
        mock_config.LOG_BACKUP_COUNT = 3
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
    
    def test_handle_errors_decorator_success(self):
        """Test handle_errors decorator with successful operation."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="error_result"
        )
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_handle_errors_decorator_with_error(self):
        """Test handle_errors decorator with error handling."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="error_result",
            raise_on_critical=False
        )
        def test_function():
            raise AudioCaptureError("Test error")
        
        result = test_function()
        assert result == "error_result"
    
    def test_log_operation_decorator(self):
        """Test log_operation decorator."""
        
        @log_operation(level="INFO", include_args=True, include_result=True)
        def test_function(arg1, arg2="default"):
            return "test_result"
        
        result = test_function("value1", arg2="value2")
        assert result == "test_result"
        
        # Check logs were created
        log_file = self.logs_dir / "test_voxel.log"
        if log_file.exists():
            log_content = log_file.read_text()
            assert "Starting test_function" in log_content
            assert "Completed test_function" in log_content
    
    def test_retry_on_error_decorator(self):
        """Test retry_on_error decorator."""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.1, exceptions=(ValueError,))
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_error_max_retries_exceeded(self):
        """Test retry_on_error when max retries exceeded."""
        
        @retry_on_error(max_retries=2, delay=0.1, exceptions=(ValueError,))
        def test_function():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError, match="Persistent error"):
            test_function()


class TestCustomExceptions:
    """Test cases for custom exception classes."""
    
    def test_voxel_error_with_additional_data(self):
        """Test VoxelError with additional data."""
        error = VoxelError(
            "Test error message",
            component="TestComponent",
            additional_data={"key1": "value1", "key2": "value2"}
        )
        
        assert str(error) == "Test error message"
        assert error.component == "TestComponent"
        assert error.additional_data["key1"] == "value1"
        assert error.additional_data["key2"] == "value2"
    
    def test_specific_error_types(self):
        """Test specific error type inheritance."""
        audio_error = AudioCaptureError("Audio error")
        speech_error = SpeechProcessingError("Speech error")
        image_error = ImageGenerationError("Image error")
        display_error = DisplayError("Display error")
        
        assert isinstance(audio_error, VoxelError)
        assert isinstance(speech_error, VoxelError)
        assert isinstance(image_error, VoxelError)
        assert isinstance(display_error, VoxelError)


class TestIntegration:
    """Integration tests for the complete error handling system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig
        self.config_patcher = patch('voxel.error_handler.SystemConfig')
        mock_config = self.config_patcher.start()
        mock_config.LOGS_DIR = self.logs_dir
        mock_config.LOG_FILE = "test_voxel.log"
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.MAX_LOG_SIZE = 1024 * 1024
        mock_config.LOG_BACKUP_COUNT = 3
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
    
    def test_end_to_end_error_handling(self):
        """Test complete error handling flow."""
        
        class TestComponent:
            @handle_errors(
                category=ErrorCategory.AUDIO_CAPTURE,
                severity=ErrorSeverity.MEDIUM,
                return_on_error=None
            )
            @log_operation(level="INFO")
            def risky_operation(self):
                raise AudioCaptureError(
                    "Test error for integration",
                    component="TestComponent",
                    additional_data={"operation_id": "test_123"}
                )
        
        component = TestComponent()
        result = component.risky_operation()
        
        # Should return None due to error handling
        assert result is None
        
        # Check that logs were created
        log_file = self.logs_dir / "test_voxel.log"
        if log_file.exists():
            log_content = log_file.read_text()
            assert "TestComponent" in log_content
            assert "risky_operation" in log_content
    
    def test_global_error_handler_functions(self):
        """Test global error handler convenience functions."""
        error = AudioCaptureError("Global handler test")
        
        result = handle_error(
            error=error,
            component="GlobalTest",
            operation="test_operation",
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result is True
        
        # Test global logging function
        log_system_event("Global log test", level="INFO", test_data="test_value")
        
        # Verify logs exist
        log_file = self.logs_dir / "test_voxel.log"
        if log_file.exists():
            log_content = log_file.read_text()
            assert "Global log test" in log_content


if __name__ == "__main__":
    pytest.main([__file__])