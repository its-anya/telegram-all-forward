#!/usr/bin/env python3
"""
Script to help determine when you can run the forwarder again after a FloodWaitError.
"""

import time
import datetime

def main():
    # The flood wait time from your error (in seconds)
    flood_wait_seconds = 2891  # Change this to your actual wait time
    
    # Calculate when you can run the script again
    now = datetime.datetime.now()
    wait_until = now + datetime.timedelta(seconds=flood_wait_seconds)
    
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"You need to wait {flood_wait_seconds} seconds ({flood_wait_seconds // 60:.1f} minutes)")
    print(f"You can run the forwarder again after: {wait_until.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # If you want to wait and then automatically run the forwarder
    choice = input("\nDo you want to wait and then automatically run the forwarder? (y/N): ")
    if choice.lower() == 'y':
        print(f"Waiting {flood_wait_seconds} seconds...")
        time.sleep(flood_wait_seconds)
        print("Wait complete! You can now run the forwarder.")
        
        # Optionally run the forwarder automatically
        run_now = input("Do you want to run the forwarder now? (y/N): ")
        if run_now.lower() == 'y':
            import subprocess
            subprocess.run(["python", "forwarder.py"])

if __name__ == "__main__":
    main()