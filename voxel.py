#!/usr/bin/env python3
"""
Voxel - Real-time ambient art generator
Main entry point for the application.

This script provides the command-line interface for the Voxel ambient art generator,
handles environment variable configuration, performs system initialization and
dependency checking, and starts the main processing loop.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add the project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass

from voxel.controller import MainController, MainControllerError
from voxel.config import SystemConfig, GenerationConfig, ErrorConfig
from voxel.error_handler import setup_logging


class VoxelApplication:
    """Main application class for Voxel ambient art generator."""
    
    def __init__(self):
        """Initialize the Voxel application."""
        self.controller: Optional[MainController] = None
        self.logger: Optional[logging.Logger] = None
        
    def setup_logging(self, log_level: str = "INFO", log_file: Optional[str] = None) -> None:
        """
        Setup application logging.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional log file path
        """
        # Ensure logs directory exists
        SystemConfig.LOGS_DIR.mkdir(exist_ok=True)
        
        # Use default log file if not specified
        if not log_file:
            log_file = SystemConfig.LOGS_DIR / SystemConfig.LOG_FILE
        
        # Setup logging using the error handler module
        setup_logging(
            log_level=log_level,
            log_file=str(log_file),
            max_size=SystemConfig.MAX_LOG_SIZE,
            backup_count=SystemConfig.LOG_BACKUP_COUNT
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Voxel application logging initialized")
    
    def check_dependencies(self) -> bool:
        """
        Check if all required dependencies are available.
        
        Returns:
            True if all dependencies are available, False otherwise
        """
        self.logger.info("Checking system dependencies...")
        
        missing_deps = []
        
        # Check Python packages
        required_packages = [
            'sounddevice',
            'vosk', 
            'openai',
            'pygame',
            'PIL',  # Pillow
            'numpy',
            'requests',
            'flask'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.logger.debug(f"✓ {package} available")
            except ImportError:
                missing_deps.append(package)
                self.logger.error(f"✗ {package} not available")
        
        # Check optional Google Cloud packages if using GCP provider
        if GenerationConfig.PROVIDER == "google_cloud":
            gcp_packages = ['google.cloud.aiplatform', 'vertexai']
            for package in gcp_packages:
                try:
                    __import__(package)
                    self.logger.debug(f"✓ {package} available")
                except ImportError:
                    missing_deps.append(package)
                    self.logger.error(f"✗ {package} not available (required for Google Cloud provider)")
        
        if missing_deps:
            self.logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            self.logger.error("Please install missing packages using: pip install -r requirements.txt")
            return False
        
        self.logger.info("All dependencies are available")
        return True
    
    def check_environment_variables(self) -> bool:
        """
        Check if required environment variables are set.
        
        Returns:
            True if all required environment variables are set, False otherwise
        """
        self.logger.info("Checking environment variables...")
        
        missing_vars = []
        
        # Check API key based on selected provider
        if GenerationConfig.PROVIDER == "openai":
            if not SystemConfig.OPENAI_API_KEY:
                missing_vars.append("OPENAI_API_KEY")
                self.logger.error("✗ OPENAI_API_KEY not set")
            else:
                self.logger.info("✓ OPENAI_API_KEY configured")
        
        elif GenerationConfig.PROVIDER == "google_cloud":
            if not SystemConfig.GOOGLE_APPLICATION_CREDENTIALS:
                missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
                self.logger.error("✗ GOOGLE_APPLICATION_CREDENTIALS not set")
            else:
                self.logger.info("✓ GOOGLE_APPLICATION_CREDENTIALS configured")
            
            if not GenerationConfig.GCP_PROJECT_ID:
                missing_vars.append("GCP_PROJECT_ID")
                self.logger.error("✗ GCP_PROJECT_ID not set")
            else:
                self.logger.info("✓ GCP_PROJECT_ID configured")
        
        elif GenerationConfig.PROVIDER == "freepik":
            if not GenerationConfig.FREEPIK_API_KEY:
                missing_vars.append("FREEPIK_API_KEY")
                self.logger.error("✗ FREEPIK_API_KEY not set")
            else:
                self.logger.info("✓ FREEPIK_API_KEY configured")
        
        if missing_vars:
            self.logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
            self.logger.error("Please set the required environment variables and try again")
            return False
        
        self.logger.info("All required environment variables are set")
        return True
    
    def check_system_requirements(self) -> bool:
        """
        Check system requirements and hardware availability.
        
        Returns:
            True if system requirements are met, False otherwise
        """
        self.logger.info("Checking system requirements...")
        
        # Check if required directories exist and create them if needed
        required_dirs = [
            SystemConfig.MODELS_DIR,
            SystemConfig.IMAGES_DIR,
            SystemConfig.LOGS_DIR
        ]
        
        for directory in required_dirs:
            try:
                directory.mkdir(exist_ok=True)
                self.logger.debug(f"✓ Directory available: {directory}")
            except Exception as e:
                self.logger.error(f"✗ Cannot create directory {directory}: {e}")
                return False
        
        # Check Vosk model availability
        vosk_model_path = SystemConfig.MODELS_DIR / "vosk-model-small-en-us-0.15"
        if not vosk_model_path.exists():
            self.logger.warning(f"Vosk model not found at {vosk_model_path}")
            self.logger.warning("Please download the Vosk model using the setup instructions")
            # Don't return False here - let the speech processor handle this
        else:
            self.logger.info("✓ Vosk model available")
        
        # Check audio system (basic check)
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                self.logger.warning("No audio input devices found")
                self.logger.warning("Please ensure a microphone is connected")
            else:
                self.logger.info(f"✓ Found {len(input_devices)} audio input device(s)")
        
        except Exception as e:
            self.logger.error(f"Error checking audio devices: {e}")
            return False
        
        self.logger.info("System requirements check completed")
        return True
    
    def initialize_system(self) -> bool:
        """
        Initialize the complete system.
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.logger.info("Initializing Voxel system...")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Check environment variables
        if not self.check_environment_variables():
            return False
        
        # Check system requirements
        if not self.check_system_requirements():
            return False
        
        # Initialize main controller
        try:
            self.controller = MainController()
            self.logger.info("Main controller initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to initialize main controller: {e}")
            return False
    
    def run(self) -> int:
        """
        Run the main application.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            self.logger.info("Starting Voxel ambient art generator...")
            
            # Start the main processing loop
            self.controller.run_continuous_loop()
            
            # Wait for the controller to finish (on shutdown signal)
            while self.controller.is_running:
                time.sleep(1)
            
            self.logger.info("Voxel application finished successfully")
            return 0
        
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, shutting down...")
            if self.controller:
                self.controller.shutdown()
            return 0
        
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            if self.controller:
                self.controller.shutdown()
            return 1
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current application status.
        
        Returns:
            Dictionary containing status information
        """
        if not self.controller:
            return {"status": "not_initialized"}
        
        return self.controller.get_status()


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Voxel - Real-time ambient art generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default settings
  %(prog)s --log-level DEBUG        # Run with debug logging
  %(prog)s --provider openai        # Use OpenAI DALL-E for image generation
  %(prog)s --provider freepik       # Use Freepik AI for image generation
  %(prog)s --check-only             # Only check system requirements
  %(prog)s --status                 # Show current system status

Environment Variables:
  OPENAI_API_KEY                    # Required for OpenAI provider
  FREEPIK_API_KEY                   # Required for Freepik provider
  GCP_PROJECT_ID                    # Required for Google Cloud provider
  GOOGLE_APPLICATION_CREDENTIALS    # Required for Google Cloud provider
  IMAGE_PROVIDER                    # Default image provider (openai/freepik/google_cloud)
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (default: logs/voxel.log)"
    )
    
    parser.add_argument(
        "--provider",
        choices=["openai", "freepik", "google_cloud"],
        help="Image generation provider (overrides IMAGE_PROVIDER env var)"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check system requirements and exit"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current system status and exit"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Voxel 1.0.0"
    )
    
    return parser


def main() -> int:
    """
    Main entry point for the Voxel application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Override provider if specified
    if args.provider:
        os.environ["IMAGE_PROVIDER"] = args.provider
        GenerationConfig.PROVIDER = args.provider
    
    # Create application instance
    app = VoxelApplication()
    
    # Setup logging
    app.setup_logging(log_level=args.log_level, log_file=args.log_file)
    
    # Handle status request
    if args.status:
        print("Voxel System Status:")
        print("=" * 50)
        
        # Basic system info
        print(f"Provider: {GenerationConfig.PROVIDER}")
        print(f"Log Level: {args.log_level}")
        
        # Try to get controller status
        try:
            if app.initialize_system():
                status = app.get_status()
                for key, value in status.items():
                    print(f"{key}: {value}")
            else:
                print("System initialization failed")
        except Exception as e:
            print(f"Error getting status: {e}")
        
        return 0
    
    # Initialize system
    if not app.initialize_system():
        print("System initialization failed. Check logs for details.")
        return 1
    
    # Handle check-only request
    if args.check_only:
        print("System requirements check completed successfully.")
        return 0
    
    # Run the application
    return app.run()


if __name__ == "__main__":
    sys.exit(main())