#!/usr/bin/env python3
"""
Example script demonstrating performance optimization and resource management features.
"""

import time
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxel.performance import ResourceManager, PerformanceMonitor, MemoryManager
from voxel.models import AudioChunk
from voxel.config import SystemConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_resource_management():
    """Demonstrate resource management capabilities."""
    print("\n=== Resource Management Demo ===")
    
    resource_manager = ResourceManager()
    
    # Start monitoring
    resource_manager.start_monitoring()
    print("✓ Resource monitoring started")
    
    # Get initial stats
    stats = resource_manager.get_resource_stats()
    print(f"Initial memory usage: {stats['memory']['current_mb']:.1f}MB")
    print(f"Disk usage: {stats['disk']['usage_percent']:.1f}%")
    
    # Simulate some work
    print("Simulating resource usage...")
    time.sleep(2)
    
    # Force cleanup
    cleanup_stats = resource_manager.force_cleanup()
    print(f"Cleanup completed: {cleanup_stats['files_removed']} files removed, "
          f"{cleanup_stats['memory_freed_mb']:.1f}MB freed")
    
    # Stop monitoring
    resource_manager.stop_monitoring()
    print("✓ Resource monitoring stopped")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("\n=== Performance Monitoring Demo ===")
    
    performance_monitor = PerformanceMonitor()
    
    # Start monitoring
    performance_monitor.start_monitoring()
    print("✓ Performance monitoring started")
    
    # Add optimization callback
    def optimization_callback(optimization_type):
        print(f"🔧 Optimization triggered: {optimization_type}")
    
    performance_monitor.add_optimization_callback(optimization_callback)
    
    # Simulate some operations with timing
    print("Performing timed operations...")
    
    for i in range(5):
        with performance_monitor.measure_operation_time(f"demo_operation_{i}"):
            # Simulate work
            time.sleep(0.5)
            print(f"  Operation {i+1} completed")
    
    # Get performance stats
    stats = performance_monitor.get_performance_stats()
    print(f"Average CPU usage: {stats['averages']['cpu_percent']:.1f}%")
    print(f"Peak memory usage: {stats['peaks']['memory_percent']:.1f}%")
    print(f"Recent operations: {stats['timing']['recent_operations']}")
    
    # Get recommendations
    recommendations = performance_monitor.get_optimization_recommendations()
    print("Performance recommendations:")
    for rec in recommendations[:3]:  # Show first 3
        print(f"  • {rec}")
    
    # Stop monitoring
    performance_monitor.stop_monitoring()
    print("✓ Performance monitoring stopped")


def demonstrate_memory_management():
    """Demonstrate memory management capabilities."""
    print("\n=== Memory Management Demo ===")
    
    memory_manager = MemoryManager()
    
    # Start management
    memory_manager.start_management()
    print("✓ Memory management started")
    
    # Register some audio buffers
    print("Registering audio buffers...")
    for i in range(8):
        audio_data = b"fake audio data" * 10000  # ~100KB each
        audio_chunk = AudioChunk(
            data=audio_data,
            timestamp=datetime.now(),
            duration=5.0,
            sample_rate=16000
        )
        memory_manager.register_audio_buffer(f"demo_buffer_{i}", audio_chunk)
        print(f"  Registered buffer {i+1}")
    
    # Register some image cache
    print("Registering image cache...")
    for i in range(3):
        image_data = b"fake image data" * 50000  # ~500KB each
        memory_manager.register_image_cache(f"demo_image_{i}", image_data)
        print(f"  Registered image {i+1}")
    
    # Get memory stats
    stats = memory_manager.get_memory_stats()
    print(f"Process memory: {stats['process_memory_mb']:.1f}MB")
    print(f"Audio buffers: {stats['buffers']['audio_count']} "
          f"({stats['buffers']['audio_memory_mb']:.1f}MB)")
    print(f"Image cache: {stats['buffers']['image_count']} "
          f"({stats['buffers']['image_memory_mb']:.1f}MB)")
    
    # Check memory pressure
    pressure = memory_manager.check_memory_pressure()
    print(f"Memory pressure detected: {pressure}")
    
    # Force cleanup
    cleanup_stats = memory_manager.force_cleanup()
    print(f"Memory cleanup: {cleanup_stats['gc_collected']} objects collected, "
          f"{cleanup_stats['buffers_cleaned']} buffers cleaned")
    
    # Apply Raspberry Pi optimizations
    print("Applying Raspberry Pi optimizations...")
    memory_manager.optimize_for_raspberry_pi()
    
    # Get updated stats
    stats = memory_manager.get_memory_stats()
    print(f"Optimized limits - Audio chunks: {stats['limits']['max_audio_chunks']}, "
          f"Cached images: {stats['limits']['max_cached_images']}")
    
    # Stop management
    memory_manager.stop_management()
    print("✓ Memory management stopped")


def demonstrate_integrated_performance_system():
    """Demonstrate all performance components working together."""
    print("\n=== Integrated Performance System Demo ===")
    
    # Initialize all components
    resource_manager = ResourceManager()
    performance_monitor = PerformanceMonitor()
    memory_manager = MemoryManager()
    
    # Start all monitoring
    resource_manager.start_monitoring()
    performance_monitor.start_monitoring()
    memory_manager.start_management()
    print("✓ All performance systems started")
    
    # Add performance optimization callback
    def integrated_optimization_callback(optimization_type):
        print(f"🔧 Integrated optimization: {optimization_type}")
        if optimization_type == 'cpu_high':
            # Trigger memory cleanup
            memory_manager.cleanup_memory()
        elif optimization_type == 'memory_high':
            # Trigger resource cleanup
            resource_manager.cleanup_resources()
    
    performance_monitor.add_optimization_callback(integrated_optimization_callback)
    
    # Simulate a processing cycle
    print("Simulating processing cycle...")
    
    with performance_monitor.measure_operation_time("integrated_cycle"):
        # Simulate audio processing
        for i in range(3):
            audio_data = b"audio chunk data" * 5000
            memory_manager.register_audio_buffer(f"cycle_audio_{i}", audio_data)
        
        # Simulate image generation
        image_data = b"generated image data" * 20000
        memory_manager.register_image_cache("cycle_image", image_data)
        
        # Simulate processing delay
        time.sleep(1.0)
        
        # Check memory pressure and cleanup if needed
        if memory_manager.check_memory_pressure():
            print("Memory pressure detected, cleaning up...")
            memory_manager.cleanup_memory()
    
    # Get comprehensive stats
    print("\nFinal System Statistics:")
    
    perf_stats = performance_monitor.get_performance_stats()
    resource_stats = resource_manager.get_resource_stats()
    memory_stats = memory_manager.get_memory_stats()
    
    print(f"  CPU Average: {perf_stats['averages']['cpu_percent']:.1f}%")
    print(f"  Memory Usage: {memory_stats['process_memory_mb']:.1f}MB")
    print(f"  Registered Buffers: {memory_stats['buffers']['total_registered']}")
    print(f"  Cleanup Operations: {resource_stats['cleanup_stats']['memory_cleanups']}")
    
    # Stop all monitoring
    performance_monitor.stop_monitoring()
    memory_manager.stop_management()
    resource_manager.stop_monitoring()
    print("✓ All performance systems stopped")


def main():
    """Run all performance optimization demonstrations."""
    print("Voxel Performance Optimization Demo")
    print("=" * 50)
    
    try:
        # Run individual demos
        demonstrate_resource_management()
        demonstrate_performance_monitoring()
        demonstrate_memory_management()
        demonstrate_integrated_performance_system()
        
        print("\n" + "=" * 50)
        print("✅ All performance optimization demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Resource monitoring and cleanup")
        print("  • CPU and memory performance tracking")
        print("  • Audio buffer and image cache management")
        print("  • Raspberry Pi specific optimizations")
        print("  • Integrated performance optimization callbacks")
        print("  • Automatic memory pressure detection and cleanup")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())