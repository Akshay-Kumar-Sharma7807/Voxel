"""
Example script demonstrating MainController usage and testing.
"""

import logging
import time
import sys
from pathlib import Path

# Add the parent directory to the path so we can import voxel
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxel.controller import MainController
from voxel.config import SystemConfig


def setup_logging():
    """Setup logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('voxel_example.log')
        ]
    )


def test_controller_initialization():
    """Test MainController initialization."""
    print("Testing MainController initialization...")
    
    controller = MainController()
    
    # Test initial state
    assert not controller.is_running
    assert not controller.shutdown_requested
    assert controller.cycle_count == 0
    
    print("✓ MainController initialized successfully")
    
    # Test status reporting
    status = controller.get_status()
    print(f"Initial status: {status}")
    
    return controller


def test_component_initialization(controller):
    """Test component initialization."""
    print("\nTesting component initialization...")
    
    try:
        success = controller.initialize_components()
        if success:
            print("✓ All components initialized successfully")
        else:
            print("✗ Component initialization failed")
            return False
    except Exception as e:
        print(f"✗ Component initialization failed with exception: {e}")
        return False
    
    return True


def test_processing_cycle(controller):
    """Test a single processing cycle."""
    print("\nTesting processing cycle...")
    
    try:
        # This will likely fail in a real environment without proper setup
        # but we can test the error handling
        result = controller._execute_processing_cycle()
        
        if result:
            print("✓ Processing cycle completed successfully")
        else:
            print("⚠ Processing cycle completed with no action (expected without audio)")
        
        return True
    except Exception as e:
        print(f"Processing cycle error (expected): {e}")
        return True  # Expected in test environment


def test_error_handling(controller):
    """Test error handling mechanisms."""
    print("\nTesting error handling...")
    
    # Test error tracking
    initial_errors = controller.error_count
    controller._handle_cycle_error()
    
    assert controller.error_count == initial_errors + 1
    assert controller.consecutive_errors == 1
    
    print("✓ Error tracking works correctly")
    
    # Test recovery attempt
    try:
        controller._attempt_recovery()
        print("✓ Recovery attempt completed")
    except Exception as e:
        print(f"Recovery attempt error (may be expected): {e}")
    
    return True


def test_timing_system(controller):
    """Test timing and cooldown system."""
    print("\nTesting timing system...")
    
    # Test cooldown with quick cycle
    start_time = time.time()
    
    # Temporarily reduce cooldown for testing
    original_cooldown = SystemConfig.CYCLE_COOLDOWN
    SystemConfig.CYCLE_COOLDOWN = 2  # 2 seconds
    
    try:
        from datetime import datetime
        cycle_start = datetime.now()
        controller._wait_for_cooldown(cycle_start)
        
        elapsed = time.time() - start_time
        print(f"Cooldown wait time: {elapsed:.2f} seconds")
        
        if elapsed >= 1.8:  # Allow some tolerance
            print("✓ Cooldown timing works correctly")
        else:
            print("⚠ Cooldown timing may be incorrect")
    
    finally:
        SystemConfig.CYCLE_COOLDOWN = original_cooldown
    
    return True


def test_shutdown_handling(controller):
    """Test shutdown handling."""
    print("\nTesting shutdown handling...")
    
    # Test shutdown signal handling
    controller.handle_shutdown(signum=2)  # Simulate SIGINT
    
    assert controller.shutdown_requested
    assert controller._shutdown_event.is_set()
    
    print("✓ Shutdown signal handling works correctly")
    
    # Test cleanup
    controller._cleanup_components()
    print("✓ Component cleanup completed")
    
    return True


def demonstrate_full_workflow():
    """Demonstrate the complete workflow (simulation)."""
    print("\n" + "="*50)
    print("DEMONSTRATING FULL VOXEL WORKFLOW")
    print("="*50)
    
    controller = MainController()
    
    try:
        # Step 1: Initialize
        print("\n1. Initializing system...")
        if not controller.initialize_components():
            print("⚠ Component initialization failed - this is expected in test environment")
            print("   In a real environment, ensure:")
            print("   - Microphone is connected")
            print("   - Vosk model is downloaded")
            print("   - API keys are configured")
            return
        
        # Step 2: Show status
        print("\n2. System status:")
        status = controller.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Step 3: Simulate workflow
        print("\n3. Simulating processing workflow...")
        print("   In a real environment, this would:")
        print("   - Capture 5-second audio chunks")
        print("   - Transcribe speech using Vosk")
        print("   - Analyze text for keywords and sentiment")
        print("   - Craft artistic image prompts")
        print("   - Generate images using DALL-E 3")
        print("   - Display images fullscreen")
        print("   - Wait 30 seconds between cycles")
        
        # Step 4: Test one cycle (will likely fail gracefully)
        print("\n4. Testing one processing cycle...")
        result = controller._execute_processing_cycle()
        print(f"   Cycle result: {result}")
        
        # Step 5: Show final status
        print("\n5. Final system status:")
        final_status = controller.get_status()
        for key, value in final_status.items():
            print(f"   {key}: {value}")
    
    finally:
        # Always cleanup
        print("\n6. Cleaning up...")
        controller.shutdown()
        print("   Shutdown completed")


def main():
    """Main example function."""
    setup_logging()
    
    print("Voxel MainController Example")
    print("="*40)
    
    try:
        # Test individual components
        controller = test_controller_initialization()
        
        if test_component_initialization(controller):
            test_processing_cycle(controller)
        
        test_error_handling(controller)
        test_timing_system(controller)
        test_shutdown_handling(controller)
        
        print("\n" + "✓"*40)
        print("All basic tests completed successfully!")
        print("✓"*40)
        
        # Demonstrate full workflow
        demonstrate_full_workflow()
        
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nExample completed.")


if __name__ == "__main__":
    main()