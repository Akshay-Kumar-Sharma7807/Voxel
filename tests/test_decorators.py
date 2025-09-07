"""
Unit tests for error handling decorators.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, Mock

from voxel.decorators import (
    handle_errors, log_operation, retry_on_error, validate_config
)
from voxel.error_handler import ErrorCategory, ErrorSeverity
from voxel.exceptions import (
    VoxelError, AudioCaptureError, ConfigurationError
)


class TestHandleErrorsDecorator:
    """Test cases for handle_errors decorator."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig
        self.config_patcher = patch('voxel.error_handler.SystemConfig')
        mock_config = self.config_patcher.start()
        mock_config.LOGS_DIR = self.logs_dir
        mock_config.LOG_FILE = "test_decorators.log"
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.MAX_LOG_SIZE = 1024 * 1024
        mock_config.LOG_BACKUP_COUNT = 3
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
    
    def test_successful_operation(self):
        """Test decorator with successful operation."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM
        )
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_error_handling_with_return_value(self):
        """Test error handling with custom return value."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="error_occurred",
            raise_on_critical=False
        )
        def failing_function():
            raise AudioCaptureError("Test error")
        
        result = failing_function()
        assert result == "error_occurred"
    
    def test_critical_error_re_raising(self):
        """Test that critical errors are re-raised when configured."""
        
        @handle_errors(
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            raise_on_critical=True
        )
        def critical_failing_function():
            raise Exception("Critical error")
        
        with pytest.raises(Exception, match="Critical error"):
            critical_failing_function()
    
    def test_component_name_detection(self):
        """Test automatic component name detection from class."""
        
        class TestComponent:
            @handle_errors(
                category=ErrorCategory.AUDIO_CAPTURE,
                severity=ErrorSeverity.MEDIUM,
                return_on_error=None,
                raise_on_critical=False
            )
            def test_method(self):
                raise AudioCaptureError("Method error")
        
        component = TestComponent()
        result = component.test_method()
        assert result is None
    
    def test_voxel_error_additional_data(self):
        """Test handling of VoxelError with additional data."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="handled",
            raise_on_critical=False
        )
        def function_with_voxel_error():
            raise AudioCaptureError(
                "Error with data",
                component="TestComponent",
                additional_data={"key": "value"}
            )
        
        result = function_with_voxel_error()
        assert result == "handled"


class TestLogOperationDecorator:
    """Test cases for log_operation decorator."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig
        self.config_patcher = patch('voxel.error_handler.SystemConfig')
        mock_config = self.config_patcher.start()
        mock_config.LOGS_DIR = self.logs_dir
        mock_config.LOG_FILE = "test_decorators.log"
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.MAX_LOG_SIZE = 1024 * 1024
        mock_config.LOG_BACKUP_COUNT = 3
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
    
    def test_basic_logging(self):
        """Test basic operation logging."""
        
        @log_operation(level="INFO")
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
    
    def test_logging_with_arguments(self):
        """Test logging with argument inclusion."""
        
        @log_operation(level="INFO", include_args=True)
        def test_function_with_args(arg1, arg2="default"):
            return f"{arg1}_{arg2}"
        
        result = test_function_with_args("value1", arg2="value2")
        assert result == "value1_value2"
    
    def test_logging_with_result(self):
        """Test logging with result inclusion."""
        
        @log_operation(level="INFO", include_result=True)
        def test_function_with_result():
            return "test_result"
        
        result = test_function_with_result()
        assert result == "test_result"
    
    def test_logging_with_exception(self):
        """Test logging when function raises exception."""
        
        @log_operation(level="INFO")
        def failing_function():
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError, match="Test exception"):
            failing_function()
    
    def test_class_method_logging(self):
        """Test logging for class methods."""
        
        class TestClass:
            @log_operation(level="INFO", include_args=True)
            def test_method(self, value):
                return f"processed_{value}"
        
        obj = TestClass()
        result = obj.test_method("input")
        assert result == "processed_input"


class TestRetryOnErrorDecorator:
    """Test cases for retry_on_error decorator."""
    
    def test_successful_retry(self):
        """Test successful operation after retries."""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def function_with_retries():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = function_with_retries()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        
        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        def always_failing_function():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError, match="Persistent error"):
            always_failing_function()
    
    def test_non_retryable_exception(self):
        """Test that non-specified exceptions are not retried."""
        
        @retry_on_error(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def function_with_different_error():
            raise TypeError("Different error type")
        
        with pytest.raises(TypeError, match="Different error type"):
            function_with_different_error()
    
    def test_backoff_factor(self):
        """Test exponential backoff behavior."""
        call_times = []
        
        @retry_on_error(
            max_retries=3, 
            delay=0.1, 
            backoff_factor=2.0, 
            exceptions=(ValueError,)
        )
        def function_with_backoff():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Retry error")
            return "success"
        
        start_time = time.time()
        result = function_with_backoff()
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Check that delays increased (approximately)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 > delay1  # Second delay should be longer
    
    def test_zero_retries(self):
        """Test behavior with zero retries."""
        
        @retry_on_error(max_retries=0, delay=0.01, exceptions=(ValueError,))
        def function_no_retries():
            raise ValueError("Immediate failure")
        
        with pytest.raises(ValueError, match="Immediate failure"):
            function_no_retries()


class TestValidateConfigDecorator:
    """Test cases for validate_config decorator."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock SystemConfig in the config module
        self.config_patcher = patch('voxel.config.SystemConfig')
        self.mock_config = self.config_patcher.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
    
    def test_valid_configuration(self):
        """Test decorator with valid configuration."""
        self.mock_config.REQUIRED_ATTR = "valid_value"
        
        @validate_config(["REQUIRED_ATTR"])
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_missing_configuration(self):
        """Test decorator with missing configuration."""
        # Create a new mock that doesn't have the required attribute
        with patch('voxel.config.SystemConfig') as missing_config_mock:
            # Configure the mock to not have MISSING_ATTR
            del missing_config_mock.MISSING_ATTR  # This will make hasattr return False
            
            @validate_config(["MISSING_ATTR"])
            def test_function():
                return "success"
            
            with pytest.raises(ConfigurationError) as exc_info:
                test_function()
            
            assert "Missing required configuration" in str(exc_info.value)
            assert "MISSING_ATTR" in str(exc_info.value)
    
    def test_none_configuration(self):
        """Test decorator with None configuration value."""
        self.mock_config.NULL_ATTR = None
        
        @validate_config(["NULL_ATTR"])
        def test_function():
            return "success"
        
        with pytest.raises(ConfigurationError) as exc_info:
            test_function()
        
        assert "Missing required configuration" in str(exc_info.value)
        assert "NULL_ATTR" in str(exc_info.value)
    
    def test_multiple_missing_attributes(self):
        """Test decorator with multiple missing attributes."""
        with patch('voxel.config.SystemConfig') as missing_config_mock:
            missing_config_mock.VALID_ATTR = "valid"
            # Configure the mock to not have MISSING_ATTR1 and MISSING_ATTR2
            del missing_config_mock.MISSING_ATTR1
            del missing_config_mock.MISSING_ATTR2
            
            @validate_config(["VALID_ATTR", "MISSING_ATTR1", "MISSING_ATTR2"])
            def test_function():
                return "success"
            
            with pytest.raises(ConfigurationError) as exc_info:
                test_function()
            
            error_message = str(exc_info.value)
            assert "Missing required configuration" in error_message
            assert "MISSING_ATTR1" in error_message
            assert "MISSING_ATTR2" in error_message
            assert "VALID_ATTR" not in error_message  # Should not include valid attrs


class TestDecoratorCombination:
    """Test cases for combining multiple decorators."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Mock SystemConfig
        self.config_patcher = patch('voxel.error_handler.SystemConfig')
        mock_config = self.config_patcher.start()
        mock_config.LOGS_DIR = self.logs_dir
        mock_config.LOG_FILE = "test_decorators.log"
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.MAX_LOG_SIZE = 1024 * 1024
        mock_config.LOG_BACKUP_COUNT = 3
        mock_config.REQUIRED_ATTR = "valid_value"
        
        # Also patch the config module for the validate_config decorator
        self.validate_config_patcher = patch('voxel.config.SystemConfig')
        validate_mock_config = self.validate_config_patcher.start()
        validate_mock_config.REQUIRED_ATTR = "valid_value"
    
    def teardown_method(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        if hasattr(self, 'validate_config_patcher'):
            self.validate_config_patcher.stop()
    
    def test_combined_decorators_success(self):
        """Test successful operation with multiple decorators."""
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM
        )
        @log_operation(level="INFO")
        @validate_config(["REQUIRED_ATTR"])
        def combined_function():
            return "success"
        
        result = combined_function()
        assert result == "success"
    
    def test_combined_decorators_with_retry(self):
        """Test combined decorators with retry logic."""
        call_count = 0
        
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="handled",
            raise_on_critical=False
        )
        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        @log_operation(level="INFO")
        def combined_retry_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = combined_retry_function()
        assert result == "success"
        assert call_count == 2
    
    def test_decorator_order_matters(self):
        """Test that decorator order affects behavior."""
        
        # Error handler outside retry - should handle the final error
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="handled",
            raise_on_critical=False
        )
        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        def function_error_outside():
            raise ValueError("Always fails")
        
        result = function_error_outside()
        assert result == "handled"
        
        # Retry outside error handler - should retry the error handling
        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        @handle_errors(
            category=ErrorCategory.AUDIO_CAPTURE,
            severity=ErrorSeverity.MEDIUM,
            return_on_error="handled",
            raise_on_critical=False
        )
        def function_retry_outside():
            raise ValueError("Always fails")
        
        result = function_retry_outside()
        assert result == "handled"


if __name__ == "__main__":
    pytest.main([__file__])