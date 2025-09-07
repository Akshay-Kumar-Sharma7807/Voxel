"""
Performance monitoring and CPU usage optimization for Raspberry Pi constraints.
"""

import time
import threading
import psutil
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import deque
import logging

from ..config import SystemConfig
from ..error_handler import ErrorCategory, ErrorSeverity, log_system_event
from ..decorators import handle_errors, log_operation

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitors system performance metrics and provides CPU usage optimization
    specifically designed for Raspberry Pi constraints.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Performance thresholds for Raspberry Pi
        self.cpu_warning_threshold = 70.0  # %
        self.cpu_critical_threshold = 85.0  # %
        self.memory_warning_threshold = 80.0  # %
        self.temperature_warning_threshold = 70.0  # °C
        self.temperature_critical_threshold = 80.0  # °C
        
        # Monitoring intervals
        self.monitor_interval = 5.0  # seconds
        self.history_size = 120  # Keep 10 minutes of data (5s intervals)
        
        # Performance history (using deque for efficient operations)
        self.cpu_history: deque = deque(maxlen=self.history_size)
        self.memory_history: deque = deque(maxlen=self.history_size)
        self.temperature_history: deque = deque(maxlen=self.history_size)
        self.timing_history: deque = deque(maxlen=self.history_size)
        
        # Performance statistics
        self.stats = {
            'cpu_avg': 0.0,
            'cpu_peak': 0.0,
            'memory_avg': 0.0,
            'memory_peak': 0.0,
            'temperature_avg': 0.0,
            'temperature_peak': 0.0,
            'warnings_count': 0,
            'critical_events': 0,
            'throttling_events': 0,
            'start_time': None
        }
        
        # Performance optimization callbacks
        self._optimization_callbacks: List[Callable] = []
        
        logger.info("PerformanceMonitor initialized")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.MEDIUM
    )
    @log_operation(level="INFO")
    def start_monitoring(self) -> None:
        """Start background performance monitoring."""
        if self.is_monitoring:
            logger.warning("Performance monitoring already active")
            return
        
        log_system_event("Starting performance monitoring...")
        
        self.is_monitoring = True
        self.stats['start_time'] = datetime.now()
        self._stop_event.clear()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="PerformanceMonitorThread",
            daemon=True
        )
        self._monitor_thread.start()
        
        log_system_event("Performance monitoring started successfully")
    
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring."""
        if not self.is_monitoring:
            return
        
        log_system_event("Stopping performance monitoring...")
        
        self.is_monitoring = False
        self._stop_event.set()
        
        # Wait for monitoring thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        log_system_event("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in background thread."""
        logger.info("Performance monitoring loop started")
        
        while not self._stop_event.is_set():
            try:
                # Collect performance metrics
                metrics = self._collect_metrics()
                
                # Store in history
                self._update_history(metrics)
                
                # Update statistics
                self._update_statistics(metrics)
                
                # Check for performance issues
                self._check_performance_thresholds(metrics)
                
                # Sleep until next monitoring cycle
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                time.sleep(self.monitor_interval * 2)  # Wait longer on error
        
        logger.info("Performance monitoring loop stopped")
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current system performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        metrics = {
            'timestamp': datetime.now(),
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_mb': 0.0,
            'temperature': 0.0,
            'load_average': [0.0, 0.0, 0.0],
            'disk_io': {'read_mb': 0.0, 'write_mb': 0.0},
            'network_io': {'sent_mb': 0.0, 'recv_mb': 0.0}
        }
        
        try:
            # CPU usage
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1.0)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_mb'] = memory.used / (1024 * 1024)
            
            # Load average (Linux/Unix)
            try:
                load_avg = psutil.getloadavg()
                metrics['load_average'] = list(load_avg)
            except AttributeError:
                # Not available on all platforms
                pass
            
            # CPU temperature (Raspberry Pi specific)
            metrics['temperature'] = self._get_cpu_temperature()
            
            # Disk I/O
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    metrics['disk_io'] = {
                        'read_mb': disk_io.read_bytes / (1024 * 1024),
                        'write_mb': disk_io.write_bytes / (1024 * 1024)
                    }
            except Exception:
                pass
            
            # Network I/O
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    metrics['network_io'] = {
                        'sent_mb': net_io.bytes_sent / (1024 * 1024),
                        'recv_mb': net_io.bytes_recv / (1024 * 1024)
                    }
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
        
        return metrics
    
    def _get_cpu_temperature(self) -> float:
        """
        Get CPU temperature (Raspberry Pi specific).
        
        Returns:
            CPU temperature in Celsius, or 0.0 if unavailable
        """
        try:
            # Try Raspberry Pi thermal zone
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_millidegrees = int(f.read().strip())
                return temp_millidegrees / 1000.0
        except (FileNotFoundError, ValueError, PermissionError):
            try:
                # Try psutil sensors (if available)
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
                elif temps:
                    # Return first available temperature sensor
                    return list(temps.values())[0][0].current
            except (AttributeError, IndexError, KeyError):
                pass
        
        return 0.0
    
    def _update_history(self, metrics: Dict[str, Any]) -> None:
        """Update performance history with new metrics."""
        self.cpu_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['cpu_percent']
        })
        
        self.memory_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['memory_percent']
        })
        
        self.temperature_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['temperature']
        })
    
    def _update_statistics(self, metrics: Dict[str, Any]) -> None:
        """Update performance statistics with new metrics."""
        # CPU statistics
        if metrics['cpu_percent'] > self.stats['cpu_peak']:
            self.stats['cpu_peak'] = metrics['cpu_percent']
        
        if self.cpu_history:
            self.stats['cpu_avg'] = sum(h['value'] for h in self.cpu_history) / len(self.cpu_history)
        
        # Memory statistics
        if metrics['memory_percent'] > self.stats['memory_peak']:
            self.stats['memory_peak'] = metrics['memory_percent']
        
        if self.memory_history:
            self.stats['memory_avg'] = sum(h['value'] for h in self.memory_history) / len(self.memory_history)
        
        # Temperature statistics
        if metrics['temperature'] > self.stats['temperature_peak']:
            self.stats['temperature_peak'] = metrics['temperature']
        
        if self.temperature_history:
            self.stats['temperature_avg'] = sum(h['value'] for h in self.temperature_history) / len(self.temperature_history)
    
    def _check_performance_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check performance metrics against thresholds and trigger optimizations."""
        # Check CPU usage
        if metrics['cpu_percent'] > self.cpu_critical_threshold:
            self.stats['critical_events'] += 1
            log_system_event(
                f"CRITICAL: CPU usage at {metrics['cpu_percent']:.1f}%",
                level="ERROR"
            )
            self._trigger_cpu_optimization()
        elif metrics['cpu_percent'] > self.cpu_warning_threshold:
            self.stats['warnings_count'] += 1
            log_system_event(
                f"WARNING: High CPU usage at {metrics['cpu_percent']:.1f}%",
                level="WARNING"
            )
        
        # Check memory usage
        if metrics['memory_percent'] > self.memory_warning_threshold:
            self.stats['warnings_count'] += 1
            log_system_event(
                f"WARNING: High memory usage at {metrics['memory_percent']:.1f}%",
                level="WARNING"
            )
        
        # Check temperature
        if metrics['temperature'] > self.temperature_critical_threshold:
            self.stats['critical_events'] += 1
            self.stats['throttling_events'] += 1
            log_system_event(
                f"CRITICAL: CPU temperature at {metrics['temperature']:.1f}°C - throttling may occur",
                level="ERROR"
            )
            self._trigger_thermal_optimization()
        elif metrics['temperature'] > self.temperature_warning_threshold:
            self.stats['warnings_count'] += 1
            log_system_event(
                f"WARNING: High CPU temperature at {metrics['temperature']:.1f}°C",
                level="WARNING"
            )
    
    def _trigger_cpu_optimization(self) -> None:
        """Trigger CPU optimization measures."""
        try:
            log_system_event("Triggering CPU optimization measures...")
            
            # Reduce processing priority
            import os
            try:
                os.nice(5)  # Lower priority
                logger.info("Reduced process priority")
            except PermissionError:
                logger.warning("Cannot reduce process priority - insufficient permissions")
            
            # Trigger optimization callbacks
            for callback in self._optimization_callbacks:
                try:
                    callback('cpu_high')
                except Exception as e:
                    logger.error(f"Optimization callback failed: {e}")
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
    
    def _trigger_thermal_optimization(self) -> None:
        """Trigger thermal optimization measures."""
        try:
            log_system_event("Triggering thermal optimization measures...")
            
            # Introduce processing delays to reduce heat
            time.sleep(2.0)
            
            # Trigger optimization callbacks
            for callback in self._optimization_callbacks:
                try:
                    callback('thermal_high')
                except Exception as e:
                    logger.error(f"Thermal optimization callback failed: {e}")
            
        except Exception as e:
            logger.error(f"Thermal optimization failed: {e}")
    
    def add_optimization_callback(self, callback: Callable[[str], None]) -> None:
        """
        Add a callback function for performance optimization.
        
        Args:
            callback: Function to call when optimization is needed.
                     Receives optimization type as parameter.
        """
        self._optimization_callbacks.append(callback)
        logger.info(f"Added optimization callback: {callback.__name__}")
    
    def measure_operation_time(self, operation_name: str) -> 'OperationTimer':
        """
        Context manager for measuring operation timing.
        
        Args:
            operation_name: Name of the operation being measured
            
        Returns:
            OperationTimer context manager
        """
        return OperationTimer(self, operation_name)
    
    def record_timing(self, operation_name: str, duration: float) -> None:
        """
        Record timing for a specific operation.
        
        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
        """
        timing_record = {
            'timestamp': datetime.now(),
            'operation': operation_name,
            'duration': duration
        }
        
        self.timing_history.append(timing_record)
        
        # Log slow operations
        if duration > 10.0:  # More than 10 seconds
            log_system_event(
                f"Slow operation detected: {operation_name} took {duration:.2f}s",
                level="WARNING"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dictionary with performance metrics and statistics
        """
        current_metrics = self._collect_metrics()
        
        # Calculate uptime
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        # Get recent timing statistics
        recent_timings = list(self.timing_history)[-20:]  # Last 20 operations
        avg_timing = 0.0
        if recent_timings:
            avg_timing = sum(t['duration'] for t in recent_timings) / len(recent_timings)
        
        return {
            'current': current_metrics,
            'averages': {
                'cpu_percent': self.stats['cpu_avg'],
                'memory_percent': self.stats['memory_avg'],
                'temperature': self.stats['temperature_avg']
            },
            'peaks': {
                'cpu_percent': self.stats['cpu_peak'],
                'memory_percent': self.stats['memory_peak'],
                'temperature': self.stats['temperature_peak']
            },
            'thresholds': {
                'cpu_warning': self.cpu_warning_threshold,
                'cpu_critical': self.cpu_critical_threshold,
                'memory_warning': self.memory_warning_threshold,
                'temperature_warning': self.temperature_warning_threshold,
                'temperature_critical': self.temperature_critical_threshold
            },
            'events': {
                'warnings_count': self.stats['warnings_count'],
                'critical_events': self.stats['critical_events'],
                'throttling_events': self.stats['throttling_events']
            },
            'timing': {
                'recent_operations': len(recent_timings),
                'average_duration': avg_timing
            },
            'monitoring': {
                'active': self.is_monitoring,
                'uptime_seconds': uptime,
                'history_size': len(self.cpu_history)
            }
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations based on current metrics.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        stats = self.get_performance_stats()
        
        # CPU recommendations
        if stats['averages']['cpu_percent'] > 60:
            recommendations.append("Consider reducing processing frequency or adding delays between operations")
        
        if stats['peaks']['cpu_percent'] > 90:
            recommendations.append("CPU usage peaks are very high - consider optimizing algorithms or reducing concurrent operations")
        
        # Memory recommendations
        if stats['averages']['memory_percent'] > 70:
            recommendations.append("Memory usage is high - enable more frequent garbage collection or reduce buffer sizes")
        
        # Temperature recommendations
        if stats['averages']['temperature'] > 65:
            recommendations.append("CPU temperature is elevated - ensure adequate cooling and consider reducing processing intensity")
        
        # Timing recommendations
        if stats['timing']['average_duration'] > 5.0:
            recommendations.append("Operations are taking longer than expected - check for blocking I/O or inefficient algorithms")
        
        # General Raspberry Pi recommendations
        if stats['events']['throttling_events'] > 0:
            recommendations.append("Thermal throttling detected - improve cooling or reduce computational load")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")
        
        return recommendations


class OperationTimer:
    """Context manager for measuring operation timing."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_timing(self.operation_name, duration)