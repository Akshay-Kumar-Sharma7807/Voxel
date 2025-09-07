"""
Memory management for audio buffers and system memory optimization.
"""

import gc
import sys
import threading
import weakref
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import logging

from ..config import AudioConfig, SystemConfig
from ..error_handler import ErrorCategory, ErrorSeverity, log_system_event
from ..decorators import handle_errors, log_operation

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages memory usage for audio buffers, image data, and system resources.
    Provides automatic cleanup and optimization for Raspberry Pi constraints.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self.is_active = False
        self._tracked_objects: Set[weakref.ref] = set()
        self._buffer_registry: Dict[str, Any] = {}
        self._cleanup_lock = threading.Lock()
        
        # Memory limits (in MB)
        self.max_audio_buffer_memory = 50  # 50MB for audio buffers
        self.max_image_cache_memory = 100  # 100MB for image cache
        self.gc_threshold_mb = 300  # Trigger GC when total usage exceeds this
        
        # Buffer management
        self.max_audio_chunks = 10
        self.max_cached_images = 5
        
        # Statistics
        self.stats = {
            'gc_collections': 0,
            'buffers_cleaned': 0,
            'memory_freed_mb': 0.0,
            'peak_usage_mb': 0.0,
            'last_cleanup': None
        }
        
        # Configure garbage collection for better performance
        self._configure_gc()
        
        logger.info("MemoryManager initialized")
    
    def _configure_gc(self) -> None:
        """Configure garbage collection for optimal performance."""
        try:
            # Set more aggressive GC thresholds for Raspberry Pi
            gc.set_threshold(500, 10, 10)  # More frequent collection
            
            # Enable automatic garbage collection
            gc.enable()
            
            logger.info("Garbage collection configured for Raspberry Pi")
            
        except Exception as e:
            logger.error(f"Failed to configure garbage collection: {e}")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.MEDIUM
    )
    @log_operation(level="INFO")
    def start_management(self) -> None:
        """Start active memory management."""
        if self.is_active:
            logger.warning("Memory management already active")
            return
        
        log_system_event("Starting memory management...")
        
        self.is_active = True
        
        # Perform initial cleanup
        self.cleanup_memory()
        
        log_system_event("Memory management started successfully")
    
    def stop_management(self) -> None:
        """Stop active memory management."""
        if not self.is_active:
            return
        
        log_system_event("Stopping memory management...")
        
        self.is_active = False
        
        # Final cleanup
        self.cleanup_memory()
        
        log_system_event("Memory management stopped")
    
    def register_audio_buffer(self, buffer_id: str, buffer_data: Any) -> None:
        """
        Register an audio buffer for memory management.
        
        Args:
            buffer_id: Unique identifier for the buffer
            buffer_data: The buffer data to track
        """
        try:
            with self._cleanup_lock:
                self._buffer_registry[f"audio_{buffer_id}"] = {
                    'data': buffer_data,
                    'type': 'audio',
                    'timestamp': datetime.now(),
                    'size_mb': self._estimate_size_mb(buffer_data)
                }
                
                # Check if we need to cleanup old buffers
                self._cleanup_old_audio_buffers()
                
        except Exception as e:
            logger.error(f"Failed to register audio buffer: {e}")
    
    def register_image_cache(self, image_id: str, image_data: Any) -> None:
        """
        Register an image in cache for memory management.
        
        Args:
            image_id: Unique identifier for the image
            image_data: The image data to track
        """
        try:
            with self._cleanup_lock:
                self._buffer_registry[f"image_{image_id}"] = {
                    'data': image_data,
                    'type': 'image',
                    'timestamp': datetime.now(),
                    'size_mb': self._estimate_size_mb(image_data)
                }
                
                # Check if we need to cleanup old images
                self._cleanup_old_image_cache()
                
        except Exception as e:
            logger.error(f"Failed to register image cache: {e}")
    
    def unregister_buffer(self, buffer_id: str) -> None:
        """
        Unregister a buffer from memory management.
        
        Args:
            buffer_id: Identifier of the buffer to unregister
        """
        try:
            with self._cleanup_lock:
                # Try both audio and image prefixes
                for prefix in ['audio_', 'image_']:
                    full_id = f"{prefix}{buffer_id}"
                    if full_id in self._buffer_registry:
                        del self._buffer_registry[full_id]
                        logger.debug(f"Unregistered buffer: {full_id}")
                        break
                        
        except Exception as e:
            logger.error(f"Failed to unregister buffer: {e}")
    
    def _cleanup_old_audio_buffers(self) -> None:
        """Clean up old audio buffers to stay within memory limits."""
        try:
            audio_buffers = {k: v for k, v in self._buffer_registry.items() 
                           if k.startswith('audio_')}
            
            # If we have too many audio buffers, remove oldest
            if len(audio_buffers) > self.max_audio_chunks:
                # Sort by timestamp (oldest first)
                sorted_buffers = sorted(audio_buffers.items(), 
                                      key=lambda x: x[1]['timestamp'])
                
                buffers_to_remove = len(audio_buffers) - self.max_audio_chunks
                
                for i in range(buffers_to_remove):
                    buffer_id, buffer_info = sorted_buffers[i]
                    del self._buffer_registry[buffer_id]
                    self.stats['buffers_cleaned'] += 1
                    logger.debug(f"Removed old audio buffer: {buffer_id}")
            
            # Check total audio memory usage
            total_audio_memory = sum(buf['size_mb'] for buf in audio_buffers.values())
            
            if total_audio_memory > self.max_audio_buffer_memory:
                logger.warning(f"Audio buffer memory usage high: {total_audio_memory:.1f}MB")
                # Remove additional buffers if needed
                self._force_cleanup_audio_buffers()
                
        except Exception as e:
            logger.error(f"Audio buffer cleanup failed: {e}")
    
    def _cleanup_old_image_cache(self) -> None:
        """Clean up old cached images to stay within memory limits."""
        try:
            image_cache = {k: v for k, v in self._buffer_registry.items() 
                          if k.startswith('image_')}
            
            # If we have too many cached images, remove oldest
            if len(image_cache) > self.max_cached_images:
                # Sort by timestamp (oldest first)
                sorted_images = sorted(image_cache.items(), 
                                     key=lambda x: x[1]['timestamp'])
                
                images_to_remove = len(image_cache) - self.max_cached_images
                
                for i in range(images_to_remove):
                    image_id, image_info = sorted_images[i]
                    del self._buffer_registry[image_id]
                    self.stats['buffers_cleaned'] += 1
                    logger.debug(f"Removed old cached image: {image_id}")
            
            # Check total image memory usage
            total_image_memory = sum(img['size_mb'] for img in image_cache.values())
            
            if total_image_memory > self.max_image_cache_memory:
                logger.warning(f"Image cache memory usage high: {total_image_memory:.1f}MB")
                # Remove additional images if needed
                self._force_cleanup_image_cache()
                
        except Exception as e:
            logger.error(f"Image cache cleanup failed: {e}")
    
    def _force_cleanup_audio_buffers(self) -> None:
        """Force cleanup of audio buffers to free memory."""
        try:
            audio_buffers = {k: v for k, v in self._buffer_registry.items() 
                           if k.startswith('audio_')}
            
            # Remove half of the audio buffers (oldest first)
            if audio_buffers:
                sorted_buffers = sorted(audio_buffers.items(), 
                                      key=lambda x: x[1]['timestamp'])
                
                buffers_to_remove = len(sorted_buffers) // 2
                
                for i in range(buffers_to_remove):
                    buffer_id, buffer_info = sorted_buffers[i]
                    del self._buffer_registry[buffer_id]
                    self.stats['buffers_cleaned'] += 1
                
                logger.info(f"Force cleaned {buffers_to_remove} audio buffers")
                
        except Exception as e:
            logger.error(f"Force audio buffer cleanup failed: {e}")
    
    def _force_cleanup_image_cache(self) -> None:
        """Force cleanup of image cache to free memory."""
        try:
            image_cache = {k: v for k, v in self._buffer_registry.items() 
                          if k.startswith('image_')}
            
            # Remove all but the most recent image
            if len(image_cache) > 1:
                sorted_images = sorted(image_cache.items(), 
                                     key=lambda x: x[1]['timestamp'])
                
                # Keep only the newest image
                for i in range(len(sorted_images) - 1):
                    image_id, image_info = sorted_images[i]
                    del self._buffer_registry[image_id]
                    self.stats['buffers_cleaned'] += 1
                
                logger.info(f"Force cleaned {len(sorted_images) - 1} cached images")
                
        except Exception as e:
            logger.error(f"Force image cache cleanup failed: {e}")
    
    def _estimate_size_mb(self, obj: Any) -> float:
        """
        Estimate the memory size of an object in MB.
        
        Args:
            obj: Object to estimate size for
            
        Returns:
            Estimated size in megabytes
        """
        try:
            size_bytes = sys.getsizeof(obj)
            
            # For complex objects, try to get a better estimate
            if hasattr(obj, '__len__'):
                try:
                    # For sequences, estimate based on length and sample element
                    if len(obj) > 0:
                        sample_size = sys.getsizeof(obj[0]) if hasattr(obj, '__getitem__') else 0
                        size_bytes += sample_size * len(obj)
                except (IndexError, TypeError):
                    pass
            
            return size_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 1.0  # Default estimate
    
    @handle_errors(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.LOW
    )
    def cleanup_memory(self) -> Dict[str, Any]:
        """
        Perform comprehensive memory cleanup.
        
        Returns:
            Dictionary with cleanup statistics
        """
        log_system_event("Starting memory cleanup...")
        
        cleanup_stats = {
            'gc_collected': 0,
            'buffers_cleaned': 0,
            'memory_freed_mb': 0.0,
            'cleanup_time': datetime.now()
        }
        
        try:
            with self._cleanup_lock:
                # Get memory usage before cleanup
                memory_before = self._get_process_memory_mb()
                
                # Clean up registered buffers
                initial_buffer_count = len(self._buffer_registry)
                self._cleanup_old_audio_buffers()
                self._cleanup_old_image_cache()
                cleanup_stats['buffers_cleaned'] = initial_buffer_count - len(self._buffer_registry)
                
                # Force garbage collection
                collected = gc.collect()
                cleanup_stats['gc_collected'] = collected
                self.stats['gc_collections'] += 1
                
                # Additional GC passes for thorough cleanup
                for generation in range(3):
                    gc.collect(generation)
                
                # Get memory usage after cleanup
                memory_after = self._get_process_memory_mb()
                cleanup_stats['memory_freed_mb'] = max(0, memory_before - memory_after)
                
                # Update statistics
                self.stats['buffers_cleaned'] += cleanup_stats['buffers_cleaned']
                self.stats['memory_freed_mb'] += cleanup_stats['memory_freed_mb']
                self.stats['last_cleanup'] = cleanup_stats['cleanup_time']
                
                # Update peak usage
                current_memory = self._get_process_memory_mb()
                if current_memory > self.stats['peak_usage_mb']:
                    self.stats['peak_usage_mb'] = current_memory
                
                log_system_event(
                    f"Memory cleanup completed: {cleanup_stats['gc_collected']} objects collected, "
                    f"{cleanup_stats['buffers_cleaned']} buffers cleaned, "
                    f"{cleanup_stats['memory_freed_mb']:.1f}MB freed"
                )
                
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
        
        return cleanup_stats
    
    def _get_process_memory_mb(self) -> float:
        """
        Get current process memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)
        except ImportError:
            # Fallback method
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            memory_kb = int(line.split()[1])
                            return memory_kb / 1024
                return 0.0
            except Exception:
                return 0.0
        except Exception:
            return 0.0
    
    def optimize_for_raspberry_pi(self) -> None:
        """Apply Raspberry Pi specific memory optimizations."""
        try:
            log_system_event("Applying Raspberry Pi memory optimizations...")
            
            # Reduce buffer sizes for Pi constraints
            self.max_audio_chunks = 5  # Reduce from 10
            self.max_cached_images = 2  # Reduce from 5
            self.max_audio_buffer_memory = 25  # Reduce from 50MB
            self.max_image_cache_memory = 50  # Reduce from 100MB
            
            # More aggressive GC settings
            gc.set_threshold(300, 5, 5)  # Even more frequent collection
            
            # Force immediate cleanup
            self.cleanup_memory()
            
            logger.info("Raspberry Pi memory optimizations applied")
            
        except Exception as e:
            logger.error(f"Raspberry Pi optimization failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            current_memory = self._get_process_memory_mb()
            
            # Calculate buffer memory usage
            audio_memory = sum(buf['size_mb'] for buf in self._buffer_registry.values() 
                             if buf['type'] == 'audio')
            image_memory = sum(buf['size_mb'] for buf in self._buffer_registry.values() 
                             if buf['type'] == 'image')
            
            # Count buffers
            audio_count = len([k for k in self._buffer_registry.keys() if k.startswith('audio_')])
            image_count = len([k for k in self._buffer_registry.keys() if k.startswith('image_')])
            
            return {
                'process_memory_mb': current_memory,
                'peak_memory_mb': self.stats['peak_usage_mb'],
                'buffers': {
                    'audio_count': audio_count,
                    'audio_memory_mb': audio_memory,
                    'audio_limit_mb': self.max_audio_buffer_memory,
                    'image_count': image_count,
                    'image_memory_mb': image_memory,
                    'image_limit_mb': self.max_image_cache_memory,
                    'total_registered': len(self._buffer_registry)
                },
                'limits': {
                    'max_audio_chunks': self.max_audio_chunks,
                    'max_cached_images': self.max_cached_images,
                    'gc_threshold_mb': self.gc_threshold_mb
                },
                'statistics': {
                    'gc_collections': self.stats['gc_collections'],
                    'buffers_cleaned': self.stats['buffers_cleaned'],
                    'memory_freed_mb': self.stats['memory_freed_mb'],
                    'last_cleanup': self.stats['last_cleanup']
                },
                'gc_info': {
                    'counts': gc.get_count(),
                    'thresholds': gc.get_threshold(),
                    'enabled': gc.isenabled()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def force_cleanup(self) -> Dict[str, Any]:
        """
        Force immediate memory cleanup.
        
        Returns:
            Cleanup statistics
        """
        log_system_event("Forcing immediate memory cleanup...")
        return self.cleanup_memory()
    
    def check_memory_pressure(self) -> bool:
        """
        Check if system is under memory pressure.
        
        Returns:
            True if memory pressure detected, False otherwise
        """
        try:
            current_memory = self._get_process_memory_mb()
            
            # Check if we're approaching limits
            if current_memory > self.gc_threshold_mb:
                logger.warning(f"Memory pressure detected: {current_memory:.1f}MB")
                return True
            
            # Check buffer memory usage
            total_buffer_memory = sum(buf['size_mb'] for buf in self._buffer_registry.values())
            
            if total_buffer_memory > (self.max_audio_buffer_memory + self.max_image_cache_memory) * 0.8:
                logger.warning(f"Buffer memory pressure: {total_buffer_memory:.1f}MB")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Memory pressure check failed: {e}")
            return False