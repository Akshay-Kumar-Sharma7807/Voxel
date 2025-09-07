"""
Resource management for audio buffers, image storage, and system resources.
"""

import os
import gc
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from ..config import SystemConfig, AudioConfig, DisplayConfig
from ..error_handler import ErrorCategory, ErrorSeverity, log_system_event
from ..decorators import handle_errors, log_operation

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages system resources including memory, disk space, and temporary files.
    Optimized for Raspberry Pi constraints with automatic cleanup routines.
    """
    
    def __init__(self):
        """Initialize the resource manager."""
        self.is_monitoring = False
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Resource limits for Raspberry Pi
        self.max_memory_usage_mb = 400  # Conservative limit for Pi
        self.max_disk_usage_mb = 1000   # 1GB for images
        self.max_audio_buffer_count = 10
        self.max_image_files = 50
        
        # Cleanup intervals
        self.cleanup_interval = 300  # 5 minutes
        self.memory_check_interval = 60  # 1 minute
        
        # Statistics
        self.stats = {
            'memory_cleanups': 0,
            'disk_cleanups': 0,
            'files_removed': 0,
            'last_cleanup': None,
            'peak_memory_mb': 0,
            'current_memory_mb': 0
        }
        
        logger.info("ResourceManager initialized")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.MEDIUM
    )
    @log_operation(level="INFO")
    def start_monitoring(self) -> None:
        """Start background resource monitoring and cleanup."""
        if self.is_monitoring:
            logger.warning("Resource monitoring already active")
            return
        
        log_system_event("Starting resource monitoring...")
        
        self.is_monitoring = True
        self._stop_event.clear()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ResourceMonitorThread",
            daemon=True
        )
        self._cleanup_thread.start()
        
        log_system_event("Resource monitoring started successfully")
    
    def stop_monitoring(self) -> None:
        """Stop background resource monitoring."""
        if not self.is_monitoring:
            return
        
        log_system_event("Stopping resource monitoring...")
        
        self.is_monitoring = False
        self._stop_event.set()
        
        # Wait for cleanup thread to finish
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        
        log_system_event("Resource monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in background thread."""
        logger.info("Resource monitoring loop started")
        
        last_memory_check = 0
        last_cleanup = 0
        
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Check memory usage periodically
                if current_time - last_memory_check >= self.memory_check_interval:
                    self._check_memory_usage()
                    last_memory_check = current_time
                
                # Perform cleanup periodically
                if current_time - last_cleanup >= self.cleanup_interval:
                    self.cleanup_resources()
                    last_cleanup = current_time
                
                # Sleep for a short interval
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error
        
        logger.info("Resource monitoring loop stopped")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.LOW
    )
    def cleanup_resources(self) -> Dict[str, Any]:
        """
        Perform comprehensive resource cleanup.
        
        Returns:
            Dictionary with cleanup statistics
        """
        log_system_event("Starting resource cleanup...")
        
        cleanup_stats = {
            'memory_freed_mb': 0,
            'files_removed': 0,
            'disk_freed_mb': 0,
            'cleanup_time': datetime.now()
        }
        
        try:
            # Clean up memory
            memory_before = self._get_memory_usage_mb()
            self._cleanup_memory()
            memory_after = self._get_memory_usage_mb()
            cleanup_stats['memory_freed_mb'] = max(0, memory_before - memory_after)
            
            # Clean up old images
            files_removed, disk_freed = self._cleanup_old_images()
            cleanup_stats['files_removed'] = files_removed
            cleanup_stats['disk_freed_mb'] = disk_freed
            
            # Clean up temporary files
            temp_files_removed = self._cleanup_temp_files()
            cleanup_stats['files_removed'] += temp_files_removed
            
            # Clean up log files
            self._cleanup_log_files()
            
            # Update statistics
            self.stats['memory_cleanups'] += 1
            self.stats['disk_cleanups'] += 1
            self.stats['files_removed'] += cleanup_stats['files_removed']
            self.stats['last_cleanup'] = cleanup_stats['cleanup_time']
            
            log_system_event(
                f"Resource cleanup completed: {cleanup_stats['files_removed']} files removed, "
                f"{cleanup_stats['memory_freed_mb']:.1f}MB memory freed, "
                f"{cleanup_stats['disk_freed_mb']:.1f}MB disk freed"
            )
            
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")
        
        return cleanup_stats
    
    def _cleanup_memory(self) -> None:
        """Force garbage collection and memory cleanup."""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Additional cleanup for specific objects
            gc.collect(0)  # Collect generation 0
            gc.collect(1)  # Collect generation 1
            gc.collect(2)  # Collect generation 2
            
            logger.debug(f"Garbage collection freed {collected} objects")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def _cleanup_old_images(self) -> tuple[int, float]:
        """
        Clean up old generated images to prevent disk space issues.
        
        Returns:
            Tuple of (files_removed, disk_space_freed_mb)
        """
        try:
            images_dir = SystemConfig.IMAGES_DIR
            if not images_dir.exists():
                return 0, 0.0
            
            # Get all image files
            image_files = list(images_dir.glob("voxel_art_*.png"))
            
            files_removed = 0
            disk_freed = 0.0
            
            if len(image_files) > self.max_image_files:
                # Sort by modification time (oldest first)
                image_files.sort(key=lambda x: x.stat().st_mtime)
                files_to_remove = image_files[:-self.max_image_files]
                
                for file_path in files_to_remove:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        files_removed += 1
                        disk_freed += file_size / (1024 * 1024)  # Convert to MB
                        logger.debug(f"Removed old image: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove image {file_path}: {e}")
            
            return files_removed, disk_freed
            
        except Exception as e:
            logger.error(f"Image cleanup failed: {e}")
            return 0, 0.0
    
    def _cleanup_temp_files(self) -> int:
        """
        Clean up temporary files and directories.
        
        Returns:
            Number of files removed
        """
        try:
            files_removed = 0
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*~",
                ".DS_Store",
                "Thumbs.db"
            ]
            
            # Clean up in project root and subdirectories
            for pattern in temp_patterns:
                for temp_file in SystemConfig.PROJECT_ROOT.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            files_removed += 1
                            logger.debug(f"Removed temp file: {temp_file}")
                    except Exception as e:
                        logger.error(f"Failed to remove temp file {temp_file}: {e}")
            
            return files_removed
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            return 0
    
    def _cleanup_log_files(self) -> None:
        """Clean up old log files to prevent disk space issues."""
        try:
            logs_dir = SystemConfig.LOGS_DIR
            if not logs_dir.exists():
                return
            
            # Remove log files older than 7 days
            cutoff_time = datetime.now() - timedelta(days=7)
            
            for log_file in logs_dir.glob("*.log*"):
                try:
                    if log_file.stat().st_mtime < cutoff_time.timestamp():
                        log_file.unlink()
                        logger.debug(f"Removed old log file: {log_file}")
                except Exception as e:
                    logger.error(f"Failed to remove log file {log_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Log file cleanup failed: {e}")
    
    def _check_memory_usage(self) -> None:
        """Check current memory usage and trigger cleanup if needed."""
        try:
            current_memory = self._get_memory_usage_mb()
            self.stats['current_memory_mb'] = current_memory
            
            # Update peak memory usage
            if current_memory > self.stats['peak_memory_mb']:
                self.stats['peak_memory_mb'] = current_memory
            
            # Trigger cleanup if memory usage is high
            if current_memory > self.max_memory_usage_mb:
                logger.warning(f"High memory usage detected: {current_memory:.1f}MB")
                self._cleanup_memory()
                
                # Check again after cleanup
                new_memory = self._get_memory_usage_mb()
                logger.info(f"Memory usage after cleanup: {new_memory:.1f}MB")
                
        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
    
    def _get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except ImportError:
            # Fallback method using /proc/self/status on Linux
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # Extract memory in kB and convert to MB
                            memory_kb = int(line.split()[1])
                            return memory_kb / 1024
                return 0.0
            except Exception:
                return 0.0
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_disk_usage_mb(self, path: Optional[Path] = None) -> Dict[str, float]:
        """
        Get disk usage information for specified path.
        
        Args:
            path: Path to check (defaults to project root)
            
        Returns:
            Dictionary with total, used, and free space in MB
        """
        try:
            if path is None:
                path = SystemConfig.PROJECT_ROOT
            
            stat = os.statvfs(str(path))
            
            # Calculate sizes in MB
            total_mb = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            used_mb = total_mb - free_mb
            
            return {
                'total_mb': total_mb,
                'used_mb': used_mb,
                'free_mb': free_mb,
                'usage_percent': (used_mb / total_mb) * 100 if total_mb > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'total_mb': 0, 'used_mb': 0, 'free_mb': 0, 'usage_percent': 0}
    
    def optimize_audio_buffers(self, audio_capture) -> None:
        """
        Optimize audio buffer usage to prevent memory issues.
        
        Args:
            audio_capture: AudioCapture instance to optimize
        """
        try:
            if not audio_capture:
                return
            
            queue_size = audio_capture.get_queue_size()
            
            # If queue is getting full, remove older chunks
            if queue_size > self.max_audio_buffer_count:
                removed_chunks = 0
                while (audio_capture.get_queue_size() > self.max_audio_buffer_count // 2 and
                       removed_chunks < 5):  # Safety limit
                    try:
                        audio_capture._audio_queue.get_nowait()
                        removed_chunks += 1
                    except:
                        break
                
                if removed_chunks > 0:
                    logger.warning(f"Removed {removed_chunks} old audio chunks to free memory")
                    
        except Exception as e:
            logger.error(f"Audio buffer optimization failed: {e}")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive resource usage statistics.
        
        Returns:
            Dictionary with resource usage information
        """
        try:
            memory_usage = self._get_memory_usage_mb()
            disk_usage = self.get_disk_usage_mb()
            
            # Count current files
            images_count = len(list(SystemConfig.IMAGES_DIR.glob("voxel_art_*.png"))) if SystemConfig.IMAGES_DIR.exists() else 0
            
            return {
                'memory': {
                    'current_mb': memory_usage,
                    'peak_mb': self.stats['peak_memory_mb'],
                    'limit_mb': self.max_memory_usage_mb,
                    'usage_percent': (memory_usage / self.max_memory_usage_mb) * 100
                },
                'disk': disk_usage,
                'files': {
                    'images_count': images_count,
                    'max_images': self.max_image_files
                },
                'cleanup_stats': {
                    'memory_cleanups': self.stats['memory_cleanups'],
                    'disk_cleanups': self.stats['disk_cleanups'],
                    'files_removed': self.stats['files_removed'],
                    'last_cleanup': self.stats['last_cleanup']
                },
                'monitoring_active': self.is_monitoring
            }
            
        except Exception as e:
            logger.error(f"Failed to get resource stats: {e}")
            return {}
    
    def force_cleanup(self) -> Dict[str, Any]:
        """
        Force immediate resource cleanup.
        
        Returns:
            Cleanup statistics
        """
        log_system_event("Forcing immediate resource cleanup...")
        return self.cleanup_resources()