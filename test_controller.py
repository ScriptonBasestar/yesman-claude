#!/usr/bin/env python3
"""Test controller for proxynd session"""

import time
from libs.dashboard.claude_manager import ClaudeManager

def main():
    print("🚀 Starting test controller for proxynd session...")
    
    # Create manager and get controller
    manager = ClaudeManager()
    controller = manager.get_controller("proxynd")
    
    print(f"Controller found: {controller}")
    print(f"Auto-next enabled: {controller.is_auto_next_enabled}")
    print(f"Claude pane: {controller.claude_pane}")
    
    # Start the controller
    print("\n📡 Starting controller...")
    if controller.start():
        print("✅ Controller started successfully!")
        
        try:
            # Let it run for 30 seconds to observe behavior
            print("🔍 Monitoring for 30 seconds... Press Ctrl+C to stop")
            for i in range(30):
                time.sleep(1)
                print(f"Running... {i+1}/30s", end="\r")
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping controller...")
        finally:
            controller.stop()
            print("Controller stopped.")
            
    else:
        print("❌ Failed to start controller")

if __name__ == "__main__":
    main()