#!/usr/bin/env python
"""BluetoothAudio - Bluetooth audio control via AVRCP for UNIAC

This module provides playback control and metadata retrieval for Bluetooth
audio devices connected to the Raspberry Pi via A2DP/AVRCP.

Created for UNIAC Nixie Clock Speaker System
"""

import dbus
import dbus.mainloop.glib
import time
import subprocess

class BluetoothAudio:
    """Class to control Bluetooth audio playback via D-Bus/BlueZ AVRCP"""

    def __init__(self):
        """Initialize Bluetooth audio controller"""
        # D-Bus setup
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
        except Exception as e:
            print("Warning: Could not initialize D-Bus: " + str(e))
            self.bus = None

        # Playback state tracking
        self.playStatusFlag = False
        self.playStatusFull = None
        self.playLastTimeChecked = 0

        # Track time tracking (since Bluetooth may not provide position)
        self.trackStartTime = 0
        self.trackPausedTime = 0
        self.trackDuration = 0
        self.isPaused = True
        self.lastMetadata = {}

        # BlueZ/AVRCP paths
        self.bluez_service = 'org.bluez'
        self.player_iface = 'org.bluez.MediaPlayer1'
        self.device_iface = 'org.bluez.Device1'
        self.properties_iface = 'org.freedesktop.DBus.Properties'

        print("BluetoothAudio controller initialized")

    def _get_managed_objects(self):
        """Get all BlueZ managed objects"""
        if not self.bus:
            return {}
        try:
            manager = dbus.Interface(
                self.bus.get_object(self.bluez_service, '/'),
                'org.freedesktop.DBus.ObjectManager'
            )
            return manager.GetManagedObjects()
        except Exception as e:
            print("Error getting managed objects: " + str(e))
            return {}

    def _find_player(self):
        """Find the first available Bluetooth media player"""
        objects = self._get_managed_objects()
        for path, interfaces in objects.items():
            if self.player_iface in interfaces:
                return path
        return None

    def _get_player_property(self, prop_name):
        """Get a property from the Bluetooth media player"""
        player_path = self._find_player()
        if not player_path or not self.bus:
            return None

        try:
            player = dbus.Interface(
                self.bus.get_object(self.bluez_service, player_path),
                self.properties_iface
            )
            return player.Get(self.player_iface, prop_name)
        except Exception as e:
            print("Error getting player property " + prop_name + ": " + str(e))
            return None

    def _call_player_method(self, method_name):
        """Call a method on the Bluetooth media player"""
        player_path = self._find_player()
        if not player_path or not self.bus:
            return False

        try:
            player = dbus.Interface(
                self.bus.get_object(self.bluez_service, player_path),
                self.player_iface
            )
            method = getattr(player, method_name)
            method()
            return True
        except Exception as e:
            print("Error calling player method " + method_name + ": " + str(e))
            return False

    def playStatus(self):
        """Check if Bluetooth audio is currently playing"""
        status = self._get_player_property('Status')
        if status == 'playing':
            self.playStatusFlag = True
            if self.isPaused:
                # Just started playing, reset timer
                self.trackStartTime = time.time() - self.trackPausedTime
                self.isPaused = False
        else:
            self.playStatusFlag = False
            if not self.isPaused:
                # Just paused, save elapsed time
                self.trackPausedTime = time.time() - self.trackStartTime
                self.isPaused = True

        return self.playStatusFlag

    def canonicalPlayObj(self):
        """Get canonical playback object (metadata)"""
        track = self._get_player_property('Track')
        status = self._get_player_property('Status')

        if track:
            self.lastMetadata = {
                'title': str(track.get('Title', 'Unknown')),
                'artist': str(track.get('Artist', 'Unknown')),
                'album': str(track.get('Album', 'Unknown')),
                'duration': int(track.get('Duration', 0)),
                'status': str(status) if status else 'stopped'
            }

            # Update track duration
            if self.lastMetadata['duration'] > 0:
                self.trackDuration = self.lastMetadata['duration']

            return self.lastMetadata

        return None

    def canonicalPlayStatus(self):
        """Get canonical play status"""
        self.playLastTimeChecked = time.time()
        playStatus = self.playStatus()
        self.playStatusFull = self.canonicalPlayObj()
        return playStatus

    def playPause(self, direction):
        """Toggle play/pause"""
        if direction == -1:
            if self.playStatus():
                return self.pause(-1)
            else:
                return self.play(-1)
        return -1

    def play(self, direction):
        """Start playback"""
        if direction == -1:
            success = self._call_player_method('Play')
            if success:
                self.playStatusFlag = True
                if self.isPaused and self.trackPausedTime > 0:
                    # Resume from paused position
                    self.trackStartTime = time.time() - self.trackPausedTime
                else:
                    # New track
                    self.trackStartTime = time.time()
                    self.trackPausedTime = 0
                self.isPaused = False
            return -1
        return -1

    def pause(self, direction, pauseIfPlaying=False):
        """Pause playback"""
        if direction == -1 or pauseIfPlaying:
            success = self._call_player_method('Pause')
            if success:
                self.playStatusFlag = False
                self.trackPausedTime = time.time() - self.trackStartTime
                self.isPaused = True
        return -1

    def nextTrack(self, direction):
        """Skip to next track"""
        if direction == -1:
            success = self._call_player_method('Next')
            if success:
                # Reset time tracking for new track
                self.trackStartTime = time.time()
                self.trackPausedTime = 0
                self.trackDuration = 0
        return -1

    def previousTrack(self, direction):
        """Go to previous track"""
        if direction == -1:
            success = self._call_player_method('Previous')
            if success:
                # Reset time tracking for new track
                self.trackStartTime = time.time()
                self.trackPausedTime = 0
                self.trackDuration = 0
        return -1

    def clientTime(self):
        """Get current playback time [elapsed_ms, total_ms]"""
        # Update metadata to get current track duration
        self.canonicalPlayObj()

        # Calculate elapsed time
        if self.isPaused:
            elapsed_ms = int(self.trackPausedTime * 1000)
        else:
            elapsed_ms = int((time.time() - self.trackStartTime) * 1000)

        # Get total duration
        total_ms = self.trackDuration

        # Try to get position from AVRCP if available
        position = self._get_player_property('Position')
        if position is not None:
            elapsed_ms = int(position)
            # Update our tracking to match
            if not self.isPaused:
                self.trackStartTime = time.time() - (elapsed_ms / 1000.0)
            else:
                self.trackPausedTime = elapsed_ms / 1000.0

        # Ensure elapsed doesn't exceed total
        if total_ms > 0 and elapsed_ms > total_ms:
            elapsed_ms = total_ms

        return [elapsed_ms, total_ms]

    def getMetadata(self):
        """Get current track metadata"""
        return self.canonicalPlayObj()

    def isConnected(self):
        """Check if a Bluetooth audio device is connected"""
        player_path = self._find_player()
        return player_path is not None


# Compatibility functions for code that uses old interface
class mpdGeneral(BluetoothAudio):
    """Compatibility class that mimics the old mpdGeneral interface"""
    pass


if __name__ == "__main__":
    # Test the Bluetooth audio controller
    print("Testing Bluetooth Audio Controller")
    bt = BluetoothAudio()

    print("\nChecking connection...")
    if bt.isConnected():
        print("Bluetooth device connected!")
    else:
        print("No Bluetooth device connected.")

    print("\nGetting metadata...")
    metadata = bt.getMetadata()
    if metadata:
        print("Title: " + metadata.get('title', 'N/A'))
        print("Artist: " + metadata.get('artist', 'N/A'))
        print("Album: " + metadata.get('album', 'N/A'))
        print("Duration: " + str(metadata.get('duration', 0) / 1000) + " seconds")
        print("Status: " + metadata.get('status', 'N/A'))

    print("\nPlay status: " + str(bt.playStatus()))

    print("\nTrack time:")
    elapsed, total = bt.clientTime()
    print("Elapsed: " + str(elapsed/1000) + "s / Total: " + str(total/1000) + "s")

    print("\nTest complete!")
