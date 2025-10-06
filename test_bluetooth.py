#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test script for Bluetooth audio functionality
Run this to verify your Bluetooth setup is working
"""

import time
import sys
from BluetoothAudio import BluetoothAudio

def test_bluetooth():
    print("=" * 50)
    print("UNIAC Bluetooth Audio Test")
    print("=" * 50)
    print()

    # Initialize
    print("Initializing Bluetooth controller...")
    try:
        bt = BluetoothAudio()
        print("[OK] Bluetooth controller initialized")
    except Exception as e:
        print("[FAIL] Failed to initialize: " + str(e))
        return False

    print()

    # Check connection
    print("Checking for connected Bluetooth device...")
    if bt.isConnected():
        print("[OK] Bluetooth device is connected!")
    else:
        print("[FAIL] No Bluetooth device connected")
        print()
        print("To connect a device:")
        print("1. Make sure Bluetooth is enabled on your phone")
        print("2. Run: sudo bluetoothctl")
        print("3. In bluetoothctl: power on")
        print("4. In bluetoothctl: discoverable on")
        print("5. In bluetoothctl: pairable on")
        print("6. Pair your phone to the Raspberry Pi")
        return False

    print()

    # Get metadata
    print("Getting track metadata...")
    metadata = bt.getMetadata()
    if metadata:
        print("[OK] Metadata retrieved:")
        print("  Title:    " + metadata.get('title', 'N/A'))
        print("  Artist:   " + metadata.get('artist', 'N/A'))
        print("  Album:    " + metadata.get('album', 'N/A'))
        print("  Duration: " + str(metadata.get('duration', 0) / 1000) + " seconds")
        print("  Status:   " + metadata.get('status', 'N/A'))
    else:
        print("[WARN] No metadata available (no track playing?)")

    print()

    # Check playback status
    print("Checking playback status...")
    is_playing = bt.playStatus()
    if is_playing:
        print("[OK] Audio is currently playing")
    else:
        print("[WARN] Audio is not playing")

    print()

    # Get track time
    print("Getting track time...")
    elapsed, total = bt.clientTime()
    elapsed_sec = elapsed / 1000
    total_sec = total / 1000
    print("  Elapsed: " + str(int(elapsed_sec)) + " seconds")
    print("  Total:   " + str(int(total_sec)) + " seconds")
    if total_sec > 0:
        percent = (elapsed_sec / total_sec) * 100
        print("  Progress: " + str(int(percent)) + "%")

    print()
    print("=" * 50)
    print("Testing Playback Controls")
    print("=" * 50)
    print()
    print("This will test play/pause/next/previous controls.")
    print("Make sure you have audio playing on your connected device!")
    print()

    response = raw_input("Test playback controls? (y/n): ")
    if response.lower() == 'y':
        print()
        print("Testing controls (watch your audio device)...")

        # Test pause
        print("  Pausing...")
        bt.pause(-1)
        time.sleep(2)

        # Test play
        print("  Playing...")
        bt.play(-1)
        time.sleep(2)

        # Test next
        print("  Next track...")
        bt.nextTrack(-1)
        time.sleep(2)

        # Test previous
        print("  Previous track...")
        bt.previousTrack(-1)
        time.sleep(2)

        print()
        print("[OK] Control test complete!")
        print("  Did the controls work? If not, your device may not support AVRCP.")

    print()
    print("=" * 50)
    print("Test Complete!")
    print("=" * 50)
    print()
    print("If everything worked, you're ready to run UNIAC_Bluetooth.py")
    print()

    return True


if __name__ == "__main__":
    try:
        test_bluetooth()
    except KeyboardInterrupt:
        print()
        print("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print()
        print("Test failed with error: " + str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
