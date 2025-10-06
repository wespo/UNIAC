#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
UNIAC Bluetooth Edition - No Button Mode
This version skips GPIO/button initialization for testing Bluetooth audio
and Nixie display without requiring the MCP23008 GPIO expander.

The display will cycle through modes automatically.
"""

import nixieDisplay
import time
import re
import pickle
import sys
import os
import setproctitle

# Import Bluetooth audio controller instead of Spotify
from BluetoothAudio import BluetoothAudio

setproctitle.setproctitle("UNIAC")

configPath = '/home/pi/UNIAC/UNIAC.conf'

print('Starting UNIAC: The Ultimate Nixie Internet Alarm Clock')
print('Model: UNIAC-S1000-Portable')
print('Version: 4.0 - Bluetooth Edition (No Buttons Test Mode)')

if len(sys.argv) > 1:
    if(sys.argv[1] == "autostart"):
        print("Auto-starting in Bluetooth mode")
        time.sleep(5)

nixie = nixieDisplay.Nixie()
nixie.dimTubes(75)
nixie.stopAllBlinking()
nixie.setAllFade(True)

def announce(message, block = False):
    if block:
        blockString = '\"'
    else:
        blockString = '\" &'
    print(message)
    newMessage = 'sudo espeak -ven+f3 -k5 -a150 -p20 -s120 \"' + message + blockString
    os.system(newMessage)

# Configuration class
class UNIACConfig:
    def __init__(self, path=configPath):
        self.path = path
        if os.path.isfile(self.path):
            confFileStream = open(self.path, 'r')
            self.conf = pickle.load(confFileStream)
            confFileStream.close()
        else:
            self.conf = {}
    def readParam(self, param):
        if param in self.conf:
            return self.conf[param]
        else:
            return None
    def writeParam(self, param, value):
        self.conf[param] = value
        self.storeConfig()
    def storeConfig(self):
        confFileStream = open(self.path, 'w')
        pickle.dump(self.conf, confFileStream)

Config = UNIACConfig()

class alarmInfo:
    def __init__(self):
        self.settings = Config.readParam('alarm')
        if self.settings == None:
            self.settings = {'hours':0,'minutes':0,'seconds':0,'alarmEnabled':False,'snoozeTime':10,'playing':False}

alarm = alarmInfo()

# Bluetooth audio general class
class btAudioGeneral:
    """General purpose class for Bluetooth audio interfaces"""
    def __init__(self):
        self.bt = BluetoothAudio()
        self.playStatusFlag = False
        self.playStatusFull = None
        self.playLastTimeChecked = 0

    def playStatus(self):
        """Check if audio is playing"""
        self.playStatusFlag = self.bt.playStatus()
        return self.playStatusFlag

    def canonicalPlayObj(self):
        """Get current playback object"""
        return self.bt.canonicalPlayObj()

    def canonicalPlayStatus(self):
        """Get canonical play status"""
        playStatusRecv = self.canonicalPlayObj()
        self.playLastTimeChecked = time.time()
        if playStatusRecv != None:
            playStatus = playStatusRecv['status'] == 'playing'
            self.playStatusFull = playStatusRecv
        else:
            playStatus = False
        self.playStatusFlag = playStatus
        return playStatus

    def clientTime(self):
        """Get current playback time [elapsed_ms, total_ms]"""
        return self.bt.clientTime()


class nixieClock(btAudioGeneral):
    """Regular clock display"""
    def __init__(self):
        super(nixieClock, self).__init__()
        self.twelveHour = Config.readParam('twelveHour')
        if self.twelveHour == None:
            self.twelveHour = True
            Config.writeParam('twelveHour',self.twelveHour)

    def displayHandler(self):
        if self.twelveHour:
            timeNum = int(time.strftime('%I%M%S'))
            if time.strftime('%p') == 'PM':
                nixie.setSpare(0,True)
            else:
                nixie.setSpare(0,False)
        else:
            timeNum = int(time.strftime('%H%M%S'))
        if(timeNum < 10000):
            timeNum = timeNum + 1000000
        nixie.printTubes(timeNum, 2)
        nixie.colons(True)

    def stopHandler(self):
        nixie.setSpare(0,False)


class btAudioStatus(btAudioGeneral):
    """Display Bluetooth audio track status (elapsed/remaining time)"""
    def __init__(self):
        super(btAudioStatus, self).__init__()
        self.displayMode = 'elapsed'

    def displayHandler(self):
        [elapsedMillis, totalMillis] = self.clientTime()
        elapsedSeconds = int(round(elapsedMillis/1000))
        totalSeconds = int(round(totalMillis/1000))

        if self.displayMode == 'remaining':
            remainingSeconds = totalSeconds - elapsedSeconds
            displaySeconds = max(remainingSeconds, 0)
        else:
            displaySeconds = elapsedSeconds

        if displaySeconds < 0:
            displaySeconds = 0

        displayMinutes = int(displaySeconds/60)
        modSeconds = displaySeconds%60
        displayTime = displayMinutes*100 + modSeconds
        nixie.printTubes(displayTime, 2)
        nixie.colons(True)


class nixieCalendar(btAudioGeneral):
    """Calendar display mode"""
    def __init__(self):
        super(nixieCalendar, self).__init__()

    def displayHandler(self):
        calNum = int(time.strftime('%m%d%y'))
        nixie.printTubes(calNum, 2)
        nixie.colons(False)


# Simple mode manager without buttons
class SimpleModeManager:
    def __init__(self):
        self.modes = []
        self.currentMode = 0
        self.lastModeSwitch = time.time()
        self.modeSwitchInterval = 10  # Switch modes every 10 seconds

    def attachMode(self, mode):
        self.modes.append(mode)

    def displayUpdate(self):
        # Auto-switch modes every interval
        if time.time() - self.lastModeSwitch > self.modeSwitchInterval:
            self.currentMode = (self.currentMode + 1) % len(self.modes)
            self.lastModeSwitch = time.time()
            print("Switching to mode " + str(self.currentMode))

        # Update current mode display
        if len(self.modes) > 0:
            self.modes[self.currentMode].displayHandler()


# Create mode manager
modeManager = SimpleModeManager()

# Attach display modes
print("Attaching display modes...")
modeManager.attachMode(nixieClock())           # Clock
modeManager.attachMode(btAudioStatus())        # Bluetooth audio status
modeManager.attachMode(nixieCalendar())        # Calendar

print("Display modes attached:")
print("  Mode 0: Clock (HH:MM:SS)")
print("  Mode 1: Track Time (MM:SS)")
print("  Mode 2: Calendar (MM/DD/YY)")
print()
print("Modes will auto-rotate every 10 seconds")
print()

# Check Bluetooth status
bt_test = BluetoothAudio()
if bt_test.isConnected():
    print("[OK] Bluetooth device connected")
    metadata = bt_test.getMetadata()
    if metadata:
        print("Currently playing:")
        print("  Title:  " + str(metadata.get('title', 'Unknown')))
        print("  Artist: " + str(metadata.get('artist', 'Unknown')))
else:
    print("[WARN] No Bluetooth device connected")
    print("Connect your phone via Bluetooth to see track info")

print()
print("Starting main loop...")
print("Press Ctrl+C to exit")
print()

# Main loop
cycleCount = 0
cycleTime = 0.1  # seconds

try:
    while True:
        time.sleep(cycleTime)
        modeManager.displayUpdate()
        cycleCount += 1

        # Print status every 30 seconds
        if cycleCount % 300 == 0:
            if bt_test.playStatus():
                elapsed, total = bt_test.clientTime()
                print("Status: Playing - " + str(elapsed/1000) + "s / " + str(total/1000) + "s")
            else:
                print("Status: Not playing")

except KeyboardInterrupt:
    print()
    print("Shutting down...")
    nixie.printTubes('', True)
    nixie.colons(False)
    print("Goodbye!")
