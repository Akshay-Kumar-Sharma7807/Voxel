"""
Performance tests to validate timing and resource usage benchmarks.
"""

import time
import threading
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from voxel.performance import ResourceManager, PerformanceMonitor, MemoryManager
from voxel.models import AudioChunk, GeneratedImage, ImagePrompt, AnalysisResult
from voxel.config import SystemConfig
from datetime import datetime


class TestResourceManager:
    """Test resource management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.resource_manager = ResourceManager()
        
        # Mock system paths to use temp directory
        with patch.object(SystemConfig, 'IMAGES_DIR', self.temp_dir / 'images'):
            with patch.object(SystemConfig, 'PROJECT_ROOT', self.temp_dir):
                SystemConfig.IMAGES_DIR.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_resource_manager_initialization(self):
        """Test resource manager initializes correctly."""
        assert not self.resource_manager.is_monitoring
        assert self.resource_manager.max_memory_usage_mb == 400
        assert self.resource_manager.max_image_files == 50
        assert self.resource_manager.stats['memory_cleanups'] == 0
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping resource monitoring."""
        self.resource_manager.start_monitoring()
        assert self.resource_manager.is_monitoring
        
        # Give it a moment to start
        time.sleep(0.1)
        
        self.resource_manager.stop_monitoring()
        assert not self.resource_manager.is_monitoring
    
    @patch('voxel.performance.resource_manager.psutil')
    def test_memory_usage_tracking(self, mock_psutil):
        """Test memory usage tracking."""
        # Mock memory info
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_psutil.Process.return_value = mock_process
        
        memory_mb = self.resource_manager._get_memory_usage_mb()
        assert memory_mb == 100.0
    
    def test_cleanup_old_images(self):
        """Test cleanup of old image files."""
        images_dir = self.temp_dir / 'images'
        images_dir.mkdir(exist_ok=True)
        
        # Create test image files
        for i in range(60):  # More than max_image_files (50)
            image_file = images_dir / f"voxel_art_202501{i:02d}_120000.png"
            image_file.write_text("fake image data")
            # Set different modification times
            timestamp = time.time() - (60 - i) * 60  # Older files have earlier timestamps
            image_file.touch(times=(timestamp, timestamp))
        
        with patch.object(SystemConfig, 'IMAGES_DIR', images_dir):
            files_removed, disk_freed = self.resource_manager._cleanup_old_images()
        
        assert files_removed == 10  # Should remove 10 files (60 - 50)
        assert disk_freed > 0
        
        # Check that newest files remain
        remaining_files = list(images_dir.glob("voxel_art_*.png"))
        assert len(remaining_files) == 50
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        # Create temporary files
        temp_files = [
            self.temp_dir / "test.tmp",
            self.temp_dir / "test.temp",
            self.temp_dir / "test~",
            self.temp_dir / ".DS_Store"
        ]
        
        for temp_file in temp_files:
            temp_file.write_text("temp data")
        
        with patch.object(SystemConfig, 'PROJECT_ROOT', self.temp_dir):
            files_removed = self.resource_manager._cleanup_temp_files()
        
        assert files_removed == len(temp_files)
        
        # Check files are removed
        for temp_file in temp_files:
            assert not temp_file.exists()
    
    def test_resource_cleanup_comprehensive(self):
        """Test comprehensive resource cleanup."""
        cleanup_stats = self.resource_manager.cleanup_resources()
        
        assert 'memory_freed_mb' in cleanup_stats
        assert 'files_removed' in cleanup_stats
        assert 'disk_freed_mb' in cleanup_stats
        assert 'cleanup_time' in cleanup_stats
        assert isinstance(cleanup_stats['cleanup_time'], datetime)
    
    def test_optimize_audio_buffers(self):
        """Test audio buffer optimization."""
        # Mock audio capture with large queue
        mock_audio_capture = Mock()
        mock_audio_capture.get_queue_size.return_value = 15  # Above max_audio_buffer_count
        mock_audio_capture._audio_queue.get_nowait.return_value = Mock()
        
        self.resource_manager.optimize_audio_buffers(mock_audio_capture)
        
        # Should have attempted to remove buffers
        assert mock_audio_capture._audio_queue.get_nowait.called
    
    def test_get_resource_stats(self):
        """Test getting resource statistics."""
        stats = self.resource_manager.get_resource_stats()
        
        assert 'memory' in stats
        assert 'disk' in stats
        assert 'files' in stats
        assert 'cleanup_stats' in stats
        assert 'monitoring_active' in stats
        
        # Check memory stats structure
        assert 'current_mb' in stats['memory']
        assert 'peak_mb' in stats['memory']
        assert 'limit_mb' in stats['memory']


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.performance_monitor = PerformanceMonitor()
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initializes correctly."""
        assert not self.performance_monitor.is_monitoring
        assert self.performance_monitor.cpu_warning_threshold == 70.0
        assert self.performance_monitor.cpu_critical_threshold == 85.0
        assert len(self.performance_monitor.cpu_history) == 0
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping performance monitoring."""
        self.performance_monitor.start_monitoring()
        assert self.performance_monitor.is_monitoring
        
        # Give it a moment to start
        time.sleep(0.1)
        
        self.performance_monitor.stop_monitoring()
        assert not self.performance_monitor.is_monitoring
    
    @patch('voxel.performance.performance_monitor.psutil')
    def test_collect_metrics(self, mock_psutil):
        """Test metrics collection."""
        # Mock system metrics
        mock_psutil.cpu_percent.return_value = 45.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.used = 500 * 1024 * 1024  # 500MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.getloadavg.return_value = (1.0, 1.5, 2.0)
        
        metrics = self.performance_monitor._collect_metrics()
        
        assert metrics['cpu_percent'] == 45.0
        assert metrics['memory_percent'] == 60.0
        assert metrics['memory_mb'] == 500.0
        assert metrics['load_average'] == [1.0, 1.5, 2.0]
        assert 'timestamp' in metrics
    
    def test_cpu_temperature_reading(self):
        """Test CPU temperature reading."""
        # Test fallback when thermal zone not available
        temp = self.performance_monitor._get_cpu_temperature()
        assert isinstance(temp, float)
        assert temp >= 0.0
    
    def test_operation_timing(self):
        """Test operation timing measurement."""
        with self.performance_monitor.measure_operation_time("test_operation"):
            time.sleep(0.1)  # Simulate work
        
        # Check that timing was recorded
        assert len(self.performance_monitor.timing_history) == 1
        timing_record = self.performance_monitor.timing_history[0]
        assert timing_record['operation'] == "test_operation"
        assert timing_record['duration'] >= 0.1
    
    def test_optimization_callbacks(self):
        """Test performance optimization callbacks."""
        callback_called = []
        
        def test_callback(optimization_type):
            callback_called.append(optimization_type)
        
        self.performance_monitor.add_optimization_callback(test_callback)
        
        # Simulate high CPU usage
        metrics = {
            'cpu_percent': 90.0,  # Above critical threshold
            'memory_percent': 50.0,
            'temperature': 60.0
        }
        
        self.performance_monitor._check_performance_thresholds(metrics)
        
        # Should have triggered CPU optimization
        assert 'cpu_high' in callback_called or len(callback_called) > 0
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        # Add some fake history data
        self.performance_monitor.cpu_history.append({
            'timestamp': datetime.now(),
            'value': 50.0
        })
        self.performance_monitor.memory_history.append({
            'timestamp': datetime.now(),
            'value': 60.0
        })
        
        stats = self.performance_monitor.get_performance_stats()
        
        assert 'current' in stats
        assert 'averages' in stats
        assert 'peaks' in stats
        assert 'thresholds' in stats
        assert 'events' in stats
        assert 'timing' in stats
        assert 'monitoring' in stats
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations."""
        # Set high usage stats
        self.performance_monitor.stats['cpu_avg'] = 80.0
        self.performance_monitor.stats['memory_avg'] = 85.0
        self.performance_monitor.stats['temperature_avg'] = 70.0
        
        recommendations = self.performance_monitor.get_optimization_recommendations()
        
        assert len(recommendations) > 0
        assert any("CPU usage" in rec for rec in recommendations)
        assert any("memory usage" in rec for rec in recommendations)
        assert any("temperature" in rec for rec in recommendations)


class TestMemoryManager:
    """Test memory management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.memory_manager = MemoryManager()
    
    def test_memory_manager_initialization(self):
        """Test memory manager initializes correctly."""
        assert not self.memory_manager.is_active
        assert self.memory_manager.max_audio_buffer_memory == 50
        assert self.memory_manager.max_image_cache_memory == 100
        assert len(self.memory_manager._buffer_registry) == 0
    
    def test_start_stop_management(self):
        """Test starting and stopping memory management."""
        self.memory_manager.start_management()
        assert self.memory_manager.is_active
        
        self.memory_manager.stop_management()
        assert not self.memory_manager.is_active
    
    def test_register_audio_buffer(self):
        """Test registering audio buffers."""
        # Create mock audio data
        audio_data = b"fake audio data" * 1000
        
        self.memory_manager.register_audio_buffer("test_buffer", audio_data)
        
        assert "audio_test_buffer" in self.memory_manager._buffer_registry
        buffer_info = self.memory_manager._buffer_registry["audio_test_buffer"]
        assert buffer_info['type'] == 'audio'
        assert buffer_info['data'] == audio_data
    
    def test_register_image_cache(self):
        """Test registering image cache."""
        # Create mock image data
        image_data = b"fake image data" * 1000
        
        self.memory_manager.register_image_cache("test_image", image_data)
        
        assert "image_test_image" in self.memory_manager._buffer_registry
        buffer_info = self.memory_manager._buffer_registry["image_test_image"]
        assert buffer_info['type'] == 'image'
        assert buffer_info['data'] == image_data
    
    def test_unregister_buffer(self):
        """Test unregistering buffers."""
        # Register a buffer first
        self.memory_manager.register_audio_buffer("test_buffer", b"data")
        assert "audio_test_buffer" in self.memory_manager._buffer_registry
        
        # Unregister it
        self.memory_manager.unregister_buffer("test_buffer")
        assert "audio_test_buffer" not in self.memory_manager._buffer_registry
    
    def test_cleanup_old_audio_buffers(self):
        """Test cleanup of old audio buffers."""
        # Register more buffers than the limit
        for i in range(15):  # More than max_audio_chunks (10)
            self.memory_manager.register_audio_buffer(f"buffer_{i}", b"data")
        
        # Should automatically clean up old buffers
        audio_buffers = {k: v for k, v in self.memory_manager._buffer_registry.items() 
                        if k.startswith('audio_')}
        assert len(audio_buffers) <= self.memory_manager.max_audio_chunks
    
    def test_cleanup_old_image_cache(self):
        """Test cleanup of old image cache."""
        # Register more images than the limit
        for i in range(8):  # More than max_cached_images (5)
            self.memory_manager.register_image_cache(f"image_{i}", b"data")
        
        # Should automatically clean up old images
        image_cache = {k: v for k, v in self.memory_manager._buffer_registry.items() 
                      if k.startswith('image_')}
        assert len(image_cache) <= self.memory_manager.max_cached_images
    
    @patch('voxel.performance.memory_manager.gc')
    def test_cleanup_memory(self, mock_gc):
        """Test memory cleanup."""
        mock_gc.collect.return_value = 100  # Mock collected objects
        
        cleanup_stats = self.memory_manager.cleanup_memory()
        
        assert 'gc_collected' in cleanup_stats
        assert 'buffers_cleaned' in cleanup_stats
        assert 'memory_freed_mb' in cleanup_stats
        assert 'cleanup_time' in cleanup_stats
        
        # Should have called garbage collection
        assert mock_gc.collect.called
    
    def test_raspberry_pi_optimization(self):
        """Test Raspberry Pi specific optimizations."""
        original_audio_chunks = self.memory_manager.max_audio_chunks
        original_cached_images = self.memory_manager.max_cached_images
        
        self.memory_manager.optimize_for_raspberry_pi()
        
        # Should have reduced limits
        assert self.memory_manager.max_audio_chunks < original_audio_chunks
        assert self.memory_manager.max_cached_images < original_cached_images
    
    def test_memory_pressure_detection(self):
        """Test memory pressure detection."""
        # Mock high memory usage
        with patch.object(self.memory_manager, '_get_process_memory_mb', return_value=350.0):
            pressure = self.memory_manager.check_memory_pressure()
            assert pressure  # Should detect pressure above gc_threshold_mb (300)
        
        # Mock normal memory usage
        with patch.object(self.memory_manager, '_get_process_memory_mb', return_value=100.0):
            pressure = self.memory_manager.check_memory_pressure()
            assert not pressure  # Should not detect pressure
    
    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        # Register some test data
        self.memory_manager.register_audio_buffer("test_audio", b"data")
        self.memory_manager.register_image_cache("test_image", b"data")
        
        stats = self.memory_manager.get_memory_stats()
        
        assert 'process_memory_mb' in stats
        assert 'peak_memory_mb' in stats
        assert 'buffers' in stats
        assert 'limits' in stats
        assert 'statistics' in stats
        assert 'gc_info' in stats
        
        # Check buffer stats
        assert stats['buffers']['audio_count'] == 1
        assert stats['buffers']['image_count'] == 1


class TestPerformanceBenchmarks:
    """Test performance benchmarks and timing requirements."""
    
    def test_audio_processing_latency_benchmark(self):
        """Test that audio processing meets latency requirements."""
        from voxel.audio.capture import AudioCapture
        from voxel.performance import MemoryManager
        
        memory_manager = MemoryManager()
        
        # Mock audio capture without actual hardware
        with patch('sounddevice.query_devices'), \
             patch('sounddevice.InputStream'):
            
            audio_capture = AudioCapture(memory_manager=memory_manager)
            
            # Simulate audio chunk processing
            start_time = time.time()
            
            # Create mock audio chunk
            audio_chunk = AudioChunk(
                data=b"fake audio data" * 1000,
                timestamp=datetime.now(),
                duration=5.0,
                sample_rate=16000
            )
            
            # Process chunk (simulate)
            chunk_id = "benchmark_chunk"
            memory_manager.register_audio_buffer(chunk_id, audio_chunk)
            
            processing_time = time.time() - start_time
            
            # Should process in under 2 seconds (requirement from design)
            assert processing_time < 2.0
    
    def test_memory_usage_benchmark(self):
        """Test that memory usage stays within Raspberry Pi limits."""
        memory_manager = MemoryManager()
        memory_manager.start_management()
        
        try:
            # Simulate registering many audio buffers
            for i in range(20):
                audio_data = b"fake audio data" * 10000  # ~100KB each
                memory_manager.register_audio_buffer(f"buffer_{i}", audio_data)
            
            # Check memory stats
            stats = memory_manager.get_memory_stats()
            
            # Should stay within limits
            assert stats['buffers']['audio_count'] <= memory_manager.max_audio_chunks
            assert stats['buffers']['audio_memory_mb'] <= memory_manager.max_audio_buffer_memory
            
        finally:
            memory_manager.stop_management()
    
    def test_resource_cleanup_timing_benchmark(self):
        """Test that resource cleanup completes within reasonable time."""
        resource_manager = ResourceManager()
        
        start_time = time.time()
        cleanup_stats = resource_manager.cleanup_resources()
        cleanup_time = time.time() - start_time
        
        # Cleanup should complete in under 5 seconds
        assert cleanup_time < 5.0
        assert isinstance(cleanup_stats, dict)
    
    def test_performance_monitoring_overhead_benchmark(self):
        """Test that performance monitoring has minimal overhead."""
        performance_monitor = PerformanceMonitor()
        performance_monitor.start_monitoring()
        
        try:
            # Measure overhead of performance monitoring
            start_time = time.time()
            
            # Simulate some work while monitoring
            for i in range(100):
                with performance_monitor.measure_operation_time(f"test_op_{i}"):
                    time.sleep(0.001)  # 1ms of work
            
            total_time = time.time() - start_time
            
            # Monitoring overhead should be minimal (less than 50% overhead)
            expected_work_time = 0.1  # 100 * 1ms
            assert total_time < expected_work_time * 1.5
            
        finally:
            performance_monitor.stop_monitoring()
    
    @pytest.mark.slow
    def test_long_running_stability_benchmark(self):
        """Test system stability over extended operation."""
        resource_manager = ResourceManager()
        memory_manager = MemoryManager()
        performance_monitor = PerformanceMonitor()
        
        # Start all monitoring
        resource_manager.start_monitoring()
        memory_manager.start_management()
        performance_monitor.start_monitoring()
        
        try:
            # Simulate extended operation (10 seconds)
            start_time = time.time()
            iteration = 0
            
            while time.time() - start_time < 10.0:
                # Simulate processing cycle
                with performance_monitor.measure_operation_time("stability_test"):
                    # Register some data
                    memory_manager.register_audio_buffer(f"stable_{iteration}", b"data" * 1000)
                    
                    # Periodic cleanup
                    if iteration % 10 == 0:
                        memory_manager.cleanup_memory()
                    
                    time.sleep(0.1)  # Simulate processing time
                    iteration += 1
            
            # Check that system is still stable
            memory_stats = memory_manager.get_memory_stats()
            resource_stats = resource_manager.get_resource_stats()
            perf_stats = performance_monitor.get_performance_stats()
            
            # Should have completed multiple iterations
            assert iteration > 50
            
            # Memory should be managed
            assert memory_stats['buffers']['audio_count'] <= memory_manager.max_audio_chunks
            
            # No critical performance issues
            assert perf_stats['events']['critical_events'] == 0
            
        finally:
            # Cleanup
            performance_monitor.stop_monitoring()
            memory_manager.stop_management()
            resource_manager.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])