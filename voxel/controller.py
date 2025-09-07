"""
Main control loop and timing system for the Voxel ambient art generator.
"""

import logging
import signal
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .audio.capture import AudioCapture
from .exceptions import AudioCaptureError
from .speech.processor import SpeechProcessor
from .exceptions import SpeechProcessingError
from .analysis.analyzer import TextAnalyzer
from .generation.crafter import PromptCrafter
from .generation.generator import ImageGenerator
from .exceptions import ImageGenerationError
from .display.controller import DisplayController
from .exceptions import DisplayError
from .config import SystemConfig, ErrorConfig
from .models import AudioChunk, TranscriptionResult, AnalysisResult, ImagePrompt, GeneratedImage
from .performance import ResourceManager, PerformanceMonitor, MemoryManager


logger = logging.getLogger(__name__)


class MainController:
    """
    Orchestrates the complete Voxel workflow with continuous operation loop,
    30-second cooldown timer, and graceful shutdown handling.
    """
    
    def __init__(self):
        """Initialize the main controller and all components."""
        self.is_running = False
        self.shutdown_requested = False
        self.last_cycle_time = datetime.now()
        self.cycle_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        
        # Component initialization
        self.audio_capture: Optional[AudioCapture] = None
        self.speech_processor: Optional[SpeechProcessor] = None
        self.text_analyzer: Optional[TextAnalyzer] = None
        self.prompt_crafter: Optional[PromptCrafter] = None
        self.image_generator: Optional[ImageGenerator] = None
        self.display_controller: Optional[DisplayController] = None
        
        # Performance management components
        self.resource_manager = ResourceManager()
        self.performance_monitor = PerformanceMonitor()
        self.memory_manager = MemoryManager()
        
        # Threading
        self._main_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Statistics tracking
        self.stats = {
            'cycles_completed': 0,
            'images_generated': 0,
            'errors_encountered': 0,
            'start_time': None,
            'last_successful_cycle': None
        }
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Setup performance optimization callbacks
        self._setup_performance_callbacks()
        
        logger.info("MainController initialized")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _setup_performance_callbacks(self) -> None:
        """Setup performance optimization callbacks."""
        def performance_optimization_callback(optimization_type: str) -> None:
            """Handle performance optimization requests."""
            try:
                if optimization_type == 'cpu_high':
                    logger.info("Applying CPU optimization measures...")
                    # Reduce processing frequency
                    time.sleep(1.0)
                    # Optimize audio buffers
                    if self.audio_capture:
                        self.resource_manager.optimize_audio_buffers(self.audio_capture)
                    # Force memory cleanup
                    self.memory_manager.cleanup_memory()
                    
                elif optimization_type == 'thermal_high':
                    logger.info("Applying thermal optimization measures...")
                    # Introduce longer delays to reduce heat
                    time.sleep(2.0)
                    # Force resource cleanup
                    self.resource_manager.cleanup_resources()
                    
                elif optimization_type == 'memory_high':
                    logger.info("Applying memory optimization measures...")
                    # Force aggressive memory cleanup
                    self.memory_manager.force_cleanup()
                    # Clean up old images
                    if self.image_generator:
                        self.image_generator.cleanup_old_images(max_images=20)
                        
            except Exception as e:
                logger.error(f"Performance optimization callback failed: {e}")
        
        # Register the callback with performance monitor
        self.performance_monitor.add_optimization_callback(performance_optimization_callback)
    
    def initialize_components(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            True if all components initialized successfully, False otherwise
        """
        logger.info("Initializing system components...")
        
        try:
            # Initialize audio capture
            logger.info("Initializing audio capture...")
            self.audio_capture = AudioCapture(memory_manager=self.memory_manager)
            
            # Initialize speech processor
            logger.info("Initializing speech processor...")
            self.speech_processor = SpeechProcessor()
            if not self.speech_processor.initialize_model():
                logger.error("Failed to initialize speech processor")
                return False
            
            # Initialize text analyzer
            logger.info("Initializing text analyzer...")
            self.text_analyzer = TextAnalyzer()
            
            # Initialize prompt crafter
            logger.info("Initializing prompt crafter...")
            self.prompt_crafter = PromptCrafter()
            
            # Initialize image generator
            logger.info("Initializing image generator...")
            self.image_generator = ImageGenerator()
            
            # Initialize display controller
            logger.info("Initializing display controller...")
            self.display_controller = DisplayController()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return False
    
    def run_continuous_loop(self) -> None:
        """
        Start the main continuous operation loop.
        
        This method runs the complete workflow continuously until shutdown is requested.
        """
        if self.is_running:
            logger.warning("Main loop is already running")
            return
        
        logger.info("Starting Voxel continuous operation loop...")
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components, cannot start main loop")
            return
        
        # Start audio capture
        try:
            self.audio_capture.start_recording()
        except AudioCaptureError as e:
            logger.error(f"Failed to start audio capture: {e}")
            return
        
        # Set running state
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        self.resource_manager.start_monitoring()
        self.memory_manager.start_management()
        
        # Optimize for Raspberry Pi if detected
        self._optimize_for_raspberry_pi()
        
        # Start main loop in separate thread
        self._main_thread = threading.Thread(
            target=self._main_loop,
            name="VoxelMainLoop",
            daemon=False
        )
        self._main_thread.start()
        
        logger.info("Voxel main loop started successfully")
    
    def _main_loop(self) -> None:
        """Main processing loop that runs in a separate thread."""
        logger.info("Main processing loop started")
        
        while not self._shutdown_event.is_set() and not self.shutdown_requested:
            try:
                # Execute one processing cycle with performance monitoring
                cycle_start_time = datetime.now()
                
                with self.performance_monitor.measure_operation_time("processing_cycle"):
                    success = self._execute_processing_cycle()
                
                if success:
                    self.stats['cycles_completed'] += 1
                    self.stats['last_successful_cycle'] = cycle_start_time
                    self.consecutive_errors = 0
                    logger.info(f"Processing cycle {self.stats['cycles_completed']} completed successfully")
                else:
                    self._handle_cycle_error()
                
                # Check for memory pressure and cleanup if needed
                if self.memory_manager.check_memory_pressure():
                    self.memory_manager.cleanup_memory()
                
                # Wait for cooldown period before next cycle
                self._wait_for_cooldown(cycle_start_time)
                
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                self._handle_cycle_error()
                time.sleep(ErrorConfig.ERROR_RECOVERY_DELAY)
        
        logger.info("Main processing loop stopped")
    
    def _execute_processing_cycle(self) -> bool:
        """
        Execute one complete processing cycle.
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        try:
            # Step 1: Get audio chunk
            logger.debug("Waiting for audio chunk...")
            audio_chunk = self._get_audio_chunk()
            if not audio_chunk:
                logger.debug("No audio chunk available, skipping cycle")
                return True  # Not an error, just no audio
            
            # Step 2: Transcribe speech
            logger.debug("Transcribing audio...")
            transcription = self._transcribe_audio(audio_chunk)
            if not transcription or not transcription.is_valid:
                logger.debug("No valid speech detected, skipping cycle")
                return True  # Not an error, just no speech
            
            # Step 3: Analyze text
            logger.debug("Analyzing transcribed text...")
            analysis = self._analyze_text(transcription)
            if not analysis or analysis.confidence < 0.3:
                logger.debug("Low confidence analysis, skipping cycle")
                return True  # Not an error, just low quality
            
            # Step 4: Craft image prompt
            logger.debug("Crafting image prompt...")
            prompt = self._craft_prompt(analysis)
            if not prompt:
                logger.warning("Failed to craft image prompt")
                return False
            
            # Step 5: Generate image
            logger.debug("Generating image...")
            generated_image = self._generate_image(prompt)
            if not generated_image:
                logger.warning("Failed to generate image")
                return False
            
            # Step 6: Display image
            logger.debug("Displaying image...")
            display_success = self._display_image(generated_image)
            if not display_success:
                logger.warning("Failed to display image")
                # Don't return False here - image was generated successfully
            
            self.stats['images_generated'] += 1
            logger.info(f"Cycle completed: '{transcription.text[:50]}...' -> Image generated and displayed")
            return True
            
        except Exception as e:
            logger.error(f"Processing cycle failed: {e}")
            return False
    
    def _get_audio_chunk(self) -> Optional[AudioChunk]:
        """Get the next audio chunk from the capture system."""
        try:
            if not self.audio_capture or not self.audio_capture.is_recording():
                logger.warning("Audio capture not active")
                return None
            
            # Wait for audio chunk with timeout
            audio_chunk = self.audio_capture.get_audio_chunk(timeout=2.0)
            return audio_chunk
            
        except Exception as e:
            logger.error(f"Failed to get audio chunk: {e}")
            return None
    
    def _transcribe_audio(self, audio_chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """Transcribe audio chunk to text."""
        try:
            if not self.speech_processor:
                logger.error("Speech processor not initialized")
                return None
            
            transcription = self.speech_processor.transcribe_audio(audio_chunk)
            
            if transcription.is_valid:
                logger.debug(f"Transcribed: '{transcription.text}' (confidence: {transcription.confidence:.2f})")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            return None
    
    def _analyze_text(self, transcription: TranscriptionResult) -> Optional[AnalysisResult]:
        """Analyze transcribed text for keywords and sentiment."""
        try:
            if not self.text_analyzer:
                logger.error("Text analyzer not initialized")
                return None
            
            analysis = self.text_analyzer.analyze_text(transcription)
            
            logger.debug(f"Analysis: keywords={analysis.keywords}, sentiment={analysis.sentiment}, themes={analysis.themes}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return None
    
    def _craft_prompt(self, analysis: AnalysisResult) -> Optional[ImagePrompt]:
        """Craft an artistic image prompt from the analysis."""
        try:
            if not self.prompt_crafter:
                logger.error("Prompt crafter not initialized")
                return None
            
            prompt = self.prompt_crafter.craft_prompt(analysis)
            
            logger.debug(f"Crafted prompt: '{prompt.prompt_text[:100]}...'")
            
            return prompt
            
        except Exception as e:
            logger.error(f"Prompt crafting failed: {e}")
            return None
    
    def _generate_image(self, prompt: ImagePrompt) -> Optional[GeneratedImage]:
        """Generate an image from the crafted prompt."""
        try:
            if not self.image_generator:
                logger.error("Image generator not initialized")
                return None
            
            generated_image = self.image_generator.generate_image(prompt)
            
            logger.info(f"Image generated successfully: {generated_image.local_path}")
            
            return generated_image
            
        except ImageGenerationError as e:
            logger.error(f"Image generation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during image generation: {e}")
            return None
    
    def _display_image(self, generated_image: GeneratedImage) -> bool:
        """Display the generated image."""
        try:
            if not self.display_controller:
                logger.error("Display controller not initialized")
                return False
            
            success = self.display_controller.display_image(generated_image)
            
            if success:
                logger.info("Image displayed successfully")
            else:
                logger.warning("Image display failed")
            
            return success
            
        except DisplayError as e:
            logger.error(f"Display error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during image display: {e}")
            return False
    
    def _wait_for_cooldown(self, cycle_start_time: datetime) -> None:
        """
        Wait for the cooldown period between processing cycles.
        
        Args:
            cycle_start_time: When the current cycle started
        """
        cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
        cooldown_remaining = SystemConfig.CYCLE_COOLDOWN - cycle_duration
        
        if cooldown_remaining > 0:
            logger.debug(f"Waiting {cooldown_remaining:.1f} seconds for cooldown...")
            
            # Wait in small increments to allow for responsive shutdown
            while cooldown_remaining > 0 and not self._shutdown_event.is_set():
                sleep_time = min(1.0, cooldown_remaining)
                time.sleep(sleep_time)
                cooldown_remaining -= sleep_time
        else:
            logger.debug("No cooldown needed, cycle took longer than cooldown period")
    
    def _handle_cycle_error(self) -> None:
        """Handle errors that occur during processing cycles."""
        self.error_count += 1
        self.consecutive_errors += 1
        self.stats['errors_encountered'] += 1
        
        logger.warning(f"Processing cycle error (consecutive: {self.consecutive_errors}, total: {self.error_count})")
        
        # If too many consecutive errors, attempt recovery
        if self.consecutive_errors >= ErrorConfig.MAX_CONSECUTIVE_ERRORS:
            logger.error("Too many consecutive errors, attempting system recovery...")
            self._attempt_recovery()
    
    def _attempt_recovery(self) -> None:
        """Attempt to recover from consecutive errors."""
        try:
            logger.info("Starting system recovery...")
            
            # Stop and restart audio capture
            if self.audio_capture:
                try:
                    self.audio_capture.stop_recording()
                    time.sleep(2)
                    self.audio_capture.start_recording()
                    logger.info("Audio capture restarted")
                except Exception as e:
                    logger.error(f"Failed to restart audio capture: {e}")
            
            # Clear display
            if self.display_controller:
                try:
                    self.display_controller.clear_display()
                    logger.info("Display cleared")
                except Exception as e:
                    logger.error(f"Failed to clear display: {e}")
            
            # Reset error counter if recovery seems successful
            self.consecutive_errors = 0
            logger.info("System recovery completed")
            
        except Exception as e:
            logger.error(f"System recovery failed: {e}")
    
    def shutdown(self) -> None:
        """Initiate graceful shutdown of the system."""
        if self.shutdown_requested:
            logger.info("Shutdown already in progress")
            return
        
        logger.info("Initiating graceful shutdown...")
        self.shutdown_requested = True
        self._shutdown_event.set()
        
        # Wait for main thread to finish
        if self._main_thread and self._main_thread.is_alive():
            logger.info("Waiting for main thread to finish...")
            self._main_thread.join(timeout=10.0)
            
            if self._main_thread.is_alive():
                logger.warning("Main thread did not finish within timeout")
        
        # Stop performance monitoring
        self.performance_monitor.stop_monitoring()
        self.resource_manager.stop_monitoring()
        self.memory_manager.stop_management()
        
        # Cleanup components
        self._cleanup_components()
        
        self.is_running = False
        logger.info("Graceful shutdown completed")
    
    def _cleanup_components(self) -> None:
        """Clean up all system components."""
        logger.info("Cleaning up system components...")
        
        # Stop audio capture
        if self.audio_capture:
            try:
                self.audio_capture.stop_recording()
                logger.info("Audio capture stopped")
            except Exception as e:
                logger.error(f"Error stopping audio capture: {e}")
        
        # Cleanup speech processor
        if self.speech_processor:
            try:
                self.speech_processor.cleanup()
                logger.info("Speech processor cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up speech processor: {e}")
        
        # Cleanup display controller
        if self.display_controller:
            try:
                self.display_controller.cleanup()
                logger.info("Display controller cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up display controller: {e}")
        
        # Cleanup image generator (remove old images)
        if self.image_generator:
            try:
                self.image_generator.cleanup_old_images()
                logger.info("Image generator cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up image generator: {e}")
        
        # Final resource cleanup
        try:
            self.resource_manager.force_cleanup()
            self.memory_manager.force_cleanup()
            logger.info("Final resource cleanup completed")
        except Exception as e:
            logger.error(f"Error during final resource cleanup: {e}")
        
        logger.info("Component cleanup completed")
    
    def _optimize_for_raspberry_pi(self) -> None:
        """Apply Raspberry Pi specific optimizations."""
        try:
            import platform
            
            # Check if running on Raspberry Pi
            if 'arm' in platform.machine().lower() or 'raspberry' in platform.node().lower():
                logger.info("Raspberry Pi detected, applying optimizations...")
                
                # Apply memory optimizations
                self.memory_manager.optimize_for_raspberry_pi()
                
                # Reduce image cache size
                if self.image_generator:
                    self.image_generator.cleanup_old_images(max_images=20)
                
                logger.info("Raspberry Pi optimizations applied")
            else:
                logger.info("Not running on Raspberry Pi, using standard settings")
                
        except Exception as e:
            logger.error(f"Raspberry Pi optimization failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status and statistics.
        
        Returns:
            Dictionary containing system status information
        """
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        # Get performance statistics
        performance_stats = self.performance_monitor.get_performance_stats()
        resource_stats = self.resource_manager.get_resource_stats()
        memory_stats = self.memory_manager.get_memory_stats()
        
        return {
            'is_running': self.is_running,
            'shutdown_requested': self.shutdown_requested,
            'uptime_seconds': uptime,
            'cycles_completed': self.stats['cycles_completed'],
            'images_generated': self.stats['images_generated'],
            'errors_encountered': self.stats['errors_encountered'],
            'consecutive_errors': self.consecutive_errors,
            'last_successful_cycle': self.stats['last_successful_cycle'],
            'audio_capture_active': self.audio_capture.is_recording() if self.audio_capture else False,
            'audio_queue_size': self.audio_capture.get_queue_size() if self.audio_capture else 0,
            'speech_processor_ready': self.speech_processor.is_initialized if self.speech_processor else False,
            'performance': performance_stats,
            'resources': resource_stats,
            'memory': memory_stats
        }
    
    def handle_shutdown(self, signum: int = None, frame = None) -> None:
        """
        Handle shutdown signals (Ctrl+C interruption).
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received shutdown signal: {signum}")
        self.shutdown()


class MainControllerError(Exception):
    """Custom exception for main controller errors."""
    pass


class ComponentInitializationError(MainControllerError):
    """Exception raised when component initialization fails."""
    pass


class ProcessingCycleError(MainControllerError):
    """Exception raised during processing cycle execution."""
    pass