"""
Integration tests for the main Voxel application entry point.
Tests application startup, configuration validation, and command-line interface.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from the main voxel.py file
import importlib.util
spec = importlib.util.spec_from_file_location("voxel_main", project_root / "voxel.py")
voxel_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voxel_main)

VoxelApplication = voxel_main.VoxelApplication
create_argument_parser = voxel_main.create_argument_parser
main = voxel_main.main
from voxel.config import SystemConfig, GenerationConfig


class TestVoxelApplication(unittest.TestCase):
    """Test cases for the VoxelApplication class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = VoxelApplication()
        # Setup a mock logger to avoid None errors
        self.app.logger = Mock()
        
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_logs_dir = Path(self.temp_dir) / "logs"
        self.temp_models_dir = Path(self.temp_dir) / "models"
        self.temp_images_dir = Path(self.temp_dir) / "images"
        
        # Patch SystemConfig paths
        self.original_logs_dir = SystemConfig.LOGS_DIR
        self.original_models_dir = SystemConfig.MODELS_DIR
        self.original_images_dir = SystemConfig.IMAGES_DIR
        
        SystemConfig.LOGS_DIR = self.temp_logs_dir
        SystemConfig.MODELS_DIR = self.temp_models_dir
        SystemConfig.IMAGES_DIR = self.temp_images_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original paths
        SystemConfig.LOGS_DIR = self.original_logs_dir
        SystemConfig.MODELS_DIR = self.original_models_dir
        SystemConfig.IMAGES_DIR = self.original_images_dir
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_setup_logging(self):
        """Test logging setup functionality."""
        # Test that setup_logging can be called without errors
        try:
            self.app.setup_logging(log_level="DEBUG", log_file="test.log")
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"setup_logging raised an exception: {e}")
    
    def test_check_dependencies_success(self):
        """Test successful dependency checking."""
        # Mock all required imports to succeed
        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = Mock()
            
            result = self.app.check_dependencies()
            
            self.assertTrue(result)
            # Test passes if no exception is raised and result is True
    
    def test_check_dependencies_missing(self):
        """Test dependency checking with missing packages."""
        # Mock some imports to fail
        def mock_import_side_effect(name):
            if name == 'sounddevice':
                raise ImportError("No module named 'sounddevice'")
            return Mock()
        
        with patch('builtins.__import__', side_effect=mock_import_side_effect):
            result = self.app.check_dependencies()
            
            self.assertFalse(result)
            # Test passes if result is False when dependencies are missing
    
    def test_check_environment_variables_openai(self):
        """Test environment variable checking for OpenAI provider."""
        # Set provider to OpenAI
        original_provider = GenerationConfig.PROVIDER
        GenerationConfig.PROVIDER = "openai"
        
        try:
            # Test with missing API key
            with patch.object(SystemConfig, 'OPENAI_API_KEY', None):
                result = self.app.check_environment_variables()
                self.assertFalse(result)
            
            # Test with API key present
            with patch.object(SystemConfig, 'OPENAI_API_KEY', 'test-key'):
                result = self.app.check_environment_variables()
                self.assertTrue(result)
        
        finally:
            GenerationConfig.PROVIDER = original_provider
    
    def test_check_environment_variables_freepik(self):
        """Test environment variable checking for Freepik provider."""
        # Set provider to Freepik
        original_provider = GenerationConfig.PROVIDER
        GenerationConfig.PROVIDER = "freepik"
        
        try:
            # Test with missing API key
            with patch.object(GenerationConfig, 'FREEPIK_API_KEY', None):
                result = self.app.check_environment_variables()
                self.assertFalse(result)
            
            # Test with API key present
            with patch.object(GenerationConfig, 'FREEPIK_API_KEY', 'test-key'):
                result = self.app.check_environment_variables()
                self.assertTrue(result)
        
        finally:
            GenerationConfig.PROVIDER = original_provider
    
    def test_check_environment_variables_google_cloud(self):
        """Test environment variable checking for Google Cloud provider."""
        # Set provider to Google Cloud
        original_provider = GenerationConfig.PROVIDER
        GenerationConfig.PROVIDER = "google_cloud"
        
        try:
            # Test with missing credentials
            with patch.object(SystemConfig, 'GOOGLE_APPLICATION_CREDENTIALS', None), \
                 patch.object(GenerationConfig, 'GCP_PROJECT_ID', None):
                result = self.app.check_environment_variables()
                self.assertFalse(result)
            
            # Test with credentials present
            with patch.object(SystemConfig, 'GOOGLE_APPLICATION_CREDENTIALS', '/path/to/creds.json'), \
                 patch.object(GenerationConfig, 'GCP_PROJECT_ID', 'test-project'):
                result = self.app.check_environment_variables()
                self.assertTrue(result)
        
        finally:
            GenerationConfig.PROVIDER = original_provider
    
    @patch('sounddevice.query_devices')
    def test_check_system_requirements_success(self, mock_query_devices):
        """Test successful system requirements checking."""
        # Mock audio devices
        mock_query_devices.return_value = [
            {'name': 'Test Mic', 'max_input_channels': 1, 'max_output_channels': 0}
        ]
        
        result = self.app.check_system_requirements()
        
        self.assertTrue(result)
        # Check that directories were created
        self.assertTrue(self.temp_logs_dir.exists())
        self.assertTrue(self.temp_models_dir.exists())
        self.assertTrue(self.temp_images_dir.exists())
    
    @patch('sounddevice.query_devices')
    def test_check_system_requirements_no_audio(self, mock_query_devices):
        """Test system requirements checking with no audio devices."""
        # Mock no audio input devices
        mock_query_devices.return_value = [
            {'name': 'Test Speaker', 'max_input_channels': 0, 'max_output_channels': 2}
        ]
        
        result = self.app.check_system_requirements()
        
        # Should still return True even with no audio devices
        self.assertTrue(result)
    
    def test_initialize_system_success(self):
        """Test successful system initialization."""
        # Mock all checks to succeed and mock MainController
        with patch.object(self.app, 'check_dependencies', return_value=True), \
             patch.object(self.app, 'check_environment_variables', return_value=True), \
             patch.object(self.app, 'check_system_requirements', return_value=True):
            
            # Mock the MainController class directly in the module
            with patch.object(voxel_main, 'MainController') as mock_controller:
                mock_controller.return_value = Mock()
                
                result = self.app.initialize_system()
                
                self.assertTrue(result)
                self.assertIsNotNone(self.app.controller)
                mock_controller.assert_called_once()
    
    def test_initialize_system_dependency_failure(self):
        """Test system initialization with dependency check failure."""
        with patch.object(self.app, 'check_dependencies', return_value=False):
            result = self.app.initialize_system()
            
            self.assertFalse(result)
            self.assertIsNone(self.app.controller)
    
    def test_run_success(self):
        """Test successful application run."""
        # Mock controller
        mock_controller = Mock()
        mock_controller.is_running = True
        mock_controller.run_continuous_loop = Mock()
        self.app.controller = mock_controller
        
        # Mock the running loop to stop after one iteration
        def stop_running():
            mock_controller.is_running = False
        
        mock_controller.run_continuous_loop.side_effect = stop_running
        
        result = self.app.run()
        
        self.assertEqual(result, 0)
        mock_controller.run_continuous_loop.assert_called_once()
    
    def test_run_keyboard_interrupt(self):
        """Test application run with keyboard interrupt."""
        # Mock controller
        mock_controller = Mock()
        mock_controller.run_continuous_loop.side_effect = KeyboardInterrupt()
        mock_controller.shutdown = Mock()
        self.app.controller = mock_controller
        
        result = self.app.run()
        
        self.assertEqual(result, 0)
        mock_controller.shutdown.assert_called_once()
    
    def test_get_status_not_initialized(self):
        """Test getting status when controller is not initialized."""
        result = self.app.get_status()
        
        self.assertEqual(result, {"status": "not_initialized"})
    
    def test_get_status_initialized(self):
        """Test getting status when controller is initialized."""
        # Mock controller with status
        mock_controller = Mock()
        mock_status = {"is_running": True, "cycles_completed": 5}
        mock_controller.get_status.return_value = mock_status
        self.app.controller = mock_controller
        
        result = self.app.get_status()
        
        self.assertEqual(result, mock_status)


class TestArgumentParser(unittest.TestCase):
    """Test cases for the command-line argument parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = create_argument_parser()
    
    def test_default_arguments(self):
        """Test parsing with default arguments."""
        args = self.parser.parse_args([])
        
        self.assertEqual(args.log_level, "INFO")
        self.assertIsNone(args.log_file)
        self.assertIsNone(args.provider)
        self.assertFalse(args.check_only)
        self.assertFalse(args.status)
    
    def test_log_level_argument(self):
        """Test log level argument parsing."""
        args = self.parser.parse_args(["--log-level", "DEBUG"])
        
        self.assertEqual(args.log_level, "DEBUG")
    
    def test_provider_argument(self):
        """Test provider argument parsing."""
        args = self.parser.parse_args(["--provider", "openai"])
        
        self.assertEqual(args.provider, "openai")
    
    def test_check_only_argument(self):
        """Test check-only argument parsing."""
        args = self.parser.parse_args(["--check-only"])
        
        self.assertTrue(args.check_only)
    
    def test_status_argument(self):
        """Test status argument parsing."""
        args = self.parser.parse_args(["--status"])
        
        self.assertTrue(args.status)
    
    def test_log_file_argument(self):
        """Test log file argument parsing."""
        args = self.parser.parse_args(["--log-file", "/tmp/test.log"])
        
        self.assertEqual(args.log_file, "/tmp/test.log")
    
    def test_invalid_log_level(self):
        """Test invalid log level argument."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--log-level", "INVALID"])
    
    def test_invalid_provider(self):
        """Test invalid provider argument."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--provider", "invalid"])


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""
    
    @patch('sys.argv', ['voxel.py'])
    def test_main_default_execution(self):
        """Test main function with default arguments."""
        # Mock application instance
        with patch.object(voxel_main, 'VoxelApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.initialize_system.return_value = True
            mock_app.run.return_value = 0
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 0)
            mock_app.setup_logging.assert_called_once()
            mock_app.initialize_system.assert_called_once()
            mock_app.run.assert_called_once()
    
    @patch('sys.argv', ['voxel.py', '--provider', 'openai'])
    def test_main_with_provider_override(self):
        """Test main function with provider override."""
        # Mock application instance
        with patch.object(voxel_main, 'VoxelApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.initialize_system.return_value = True
            mock_app.run.return_value = 0
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 0)
            # Check that provider was set in environment
            self.assertEqual(os.environ.get("IMAGE_PROVIDER"), "openai")
    
    @patch('sys.argv', ['voxel.py', '--check-only'])
    def test_main_check_only(self):
        """Test main function with check-only flag."""
        # Mock application instance
        with patch.object(voxel_main, 'VoxelApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.initialize_system.return_value = True
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 0)
            mock_app.initialize_system.assert_called_once()
            mock_app.run.assert_not_called()
    
    @patch('sys.argv', ['voxel.py', '--status'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_status(self, mock_stdout):
        """Test main function with status flag."""
        # Mock application instance
        with patch.object(voxel_main, 'VoxelApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.initialize_system.return_value = True
            mock_app.get_status.return_value = {"is_running": False, "cycles_completed": 0}
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 0)
            mock_app.initialize_system.assert_called_once()
            mock_app.get_status.assert_called_once()
            mock_app.run.assert_not_called()
            
            # Check that status was printed
            output = mock_stdout.getvalue()
            self.assertIn("Voxel System Status", output)
    
    @patch('sys.argv', ['voxel.py'])
    def test_main_initialization_failure(self):
        """Test main function with initialization failure."""
        # Mock application instance
        with patch.object(voxel_main, 'VoxelApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.initialize_system.return_value = False
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 1)
            mock_app.initialize_system.assert_called_once()
            mock_app.run.assert_not_called()


if __name__ == '__main__':
    unittest.main()