#!/usr/bin/python
# -*- coding: utf-8 -*-
import nixieDisplay
import time
import re
import pickle
import Menu as MenuClass
from socket import error as SocketError
import sys
import os
import setproctitle

# Import Bluetooth audio controller instead of Spotify
from BluetoothAudio import BluetoothAudio

setproctitle.setproctitle("UNIAC")

configPath = '/home/pi/UNIAC/UNIAC.conf'

print('Starting UNIAC: The Ultimate Nixie Internet Alarm Clock')
print('Model: UNIAC-S1000-Portable')
print('Version: 4.0 - Bluetooth Edition')

if len(sys.argv) > 1:
    if(sys.argv[1] == "autostart"):
        print("Auto-starting in Bluetooth mode")
        time.sleep(5)

nixie = nixieDisplay.Nixie()
nixie.dimTubes(75)
nixie.stopAllBlinking()
nixie.setAllFade(True)

# Set system volume to 50%
print("Setting volume to 50%...")
try:
    os.system('amixer set Master 50%')
    print("Volume set successfully")
except Exception as e:
    print("Warning: Could not set volume: " + str(e))

# Setup menu system
Menu = MenuClass.menu()

# Add buttons - the physical buttons on the board
buttons = {'plus':5, 'minus':6, 'mode':4, 'playpause':3, 'select':2,'snooze':1,'alarmenable':0}
Menu.addButtons(buttons)

def announce(message, block = False):
    # Just print the message instead of using espeak to avoid audio errors
    print("[Announce] " + message)
    # Uncomment below to re-enable espeak voice announcements
    # if block:
    #     blockString = '\"'
    # else:
    #     blockString = '\" &'
    # newMessage = 'sudo espeak -ven+f3 -k5 -a150 -p20 -s120 \"' + message + blockString
    # os.system(newMessage)

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

    def playPause(self, direction):
        """Toggle play/pause"""
        if direction == -1:
            self.bt.playPause(-1)
            return -1
        return -1

    def play(self, direction):
        """Start playback"""
        if direction == -1:
            self.bt.play(-1)
            self.playStatusFlag = True
            return -1
        return -1

    def pause(self, direction, pauseIfPlaying=False):
        """Pause playback"""
        if direction == -1 or pauseIfPlaying:
            self.bt.pause(-1, pauseIfPlaying)
            self.playStatusFlag = False
        return -1

    def nextTrack(self, direction):
        """Skip to next track"""
        if direction == -1:
            self.bt.nextTrack(-1)
        return -1

    def previousTrack(self, direction):
        """Go to previous track"""
        if direction == -1:
            self.bt.previousTrack(-1)
        return -1

    def clientTime(self):
        """Get current playback time [elapsed_ms, total_ms]"""
        return self.bt.clientTime()


class alarmGeneral(btAudioGeneral):
    """Alarm functionality with Bluetooth audio"""
    def toggleAlarm(self, direction):
        if direction == -1:
            if alarm.settings['playing']:
                self.pause(-1, True)
                alarm.settings['playing'] = False
            if alarm.settings['alarmEnabled']:
                alarm.settings['alarmEnabled'] = False
                alarm.settings['playing'] = False
                print("Alarm Disabled")
                nixie.setDecimal(0,False)
            else:
                alarm.settings['alarmEnabled'] = True
                print("Alarm Enabled")
                nixie.setDecimal(0,True)

    def snooze(self, direction):
        if direction == -1 and alarm.settings['playing']:
            alarm.settings['minutes'] = alarm.settings['minutes'] + alarm.settings['snoozeTime']
            if alarm.settings['minutes'] >= 60:
                alarm.settings['hours'] = alarm.settings['hours'] + 1
                if alarm.settings['hours'] >= 24:
                    alarm.settings['hours'] = alarm.settings['hours'] - 24
            alarm.settings['playing'] = False
            self.pause(-1, True)

    def setAlarmTime(self, hours, minutes, seconds):
        alarm.settings['hours'] = hours%24
        alarm.settings['minutes'] = minutes%60
        alarm.settings['seconds'] = seconds%60
        Config.writeParam('alarm', alarm.settings)

    def getAlarmTime(self):
        return alarm.settings

    def alarmEvent(self, twelveHour, Trigger=False):
        """Handle alarm triggering"""
        if Trigger:
            print("Alarm Announce")
            if twelveHour:
                hour = int(time.strftime('%H'))
                minute = int(time.strftime('%M'))
                styleString = ' in the morning.'
                if hour >= 12 and hour < 17:
                    styleString = ' in the afternoon.'
                elif hour >= 17 and hour < 21:
                    styleString = ' in the evening.'
                elif hour >= 21:
                    styleString = ' at night.'
                if minute == 0:
                    timeStr = time.strftime('%I o\'clock')
                elif minute < 10:
                    minuteStr = time.strftime('%M')
                    minuteStr = minuteStr[1:]
                    hourStr = time.strftime('%I')
                    timeStr  = hourStr + ', oh ' + minuteStr + '.'
                else:
                    timeStr = time.strftime('%I, %M.')
                if timeStr[0] == '0':
                    timeStr = timeStr[1:]
                announce("It is " +  timeStr + styleString, True)
            else:
                announce("It is " +  time.strftime('%H, %M.'), True)
            self.play(-1)
            return False

        if alarm.settings['playing']:
            return False
        elif time.localtime().tm_hour == alarm.settings['hours'] and time.localtime().tm_min == alarm.settings['minutes'] and time.localtime().tm_sec <= 2 and alarm.settings['playing'] == False and alarm.settings['alarmEnabled']:
            alarm.settings['playing'] = True
            print("Alarm Trigger")
            return True
        return False

    def changeAlarmHours(self,direction):
        if direction == -1 or direction == 1:
            self.setAlarmTime(alarm.settings['hours'] + direction, alarm.settings['minutes'], alarm.settings['seconds'])

    def changeAlarmMinutes(self,direction):
        if direction == -1 or direction == 1 or direction == -10 or direction == 10:
            self.setAlarmTime(alarm.settings['hours'], alarm.settings['minutes'] + direction, alarm.settings['seconds'])


class alarmClock(alarmGeneral):
    """Alarm clock display mode"""
    def __init__(self):
        alarmGeneral.__init__(self)
        self.buttonHandlers = {'select':self.nextOption, 'minus':self.decValue,'plus':self.incValue, 'playpause':self.playPause,'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.selected = 1
        self.alarmTwelveHour = Config.readParam('twelveHour')
        if self.alarmTwelveHour == None:
            self.alarmTwelveHour = True
            Config.writeParam('alarmTwelveHour', True)

    def eventFunction(self, Trigger=False):
        return self.alarmEvent(self.alarmTwelveHour, Trigger)

    def displayHandler(self):
        alarmTime = self.getAlarmTime()
        localHours = alarmTime['hours']
        if self.alarmTwelveHour:
            if localHours > 11:
                nixie.setSpare(0, True)
                if localHours > 12:
                    localHours = localHours - 12
            else:
                if localHours == 0:
                    localHours = 12
                nixie.setSpare(0, False)
            nixie.printTubes(localHours*10000 + alarmTime['minutes']*100,2)
            nixie.colons(True)
        else:
            nixie.printTubes(localHours*10000 + alarmTime['minutes']*100)
            nixie.colons(True)

    def nextOption(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected + 1)%4
            if self.selected == 0:
                self.selected = 1
            nixie.startBlinking(self.selected)

    def incValue(self,direction):
        if direction == -1:
            if self.selected == 1:
                self.changeAlarmHours(1)
            elif self.selected == 2:
                self.changeAlarmMinutes(10)
            elif self.selected == 3:
                self.changeAlarmMinutes(1)

    def decValue(self,direction):
        if direction == -1:
            if self.selected == 1:
                self.changeAlarmHours(-1)
            elif self.selected == 2:
                self.changeAlarmMinutes(-10)
            elif self.selected == 3:
                self.changeAlarmMinutes(-1)

    def startHandler(self):
        nixie.startBlinking(self.selected)

    def stopHandler(self):
        nixie.stopAllBlinking()
        nixie.setSpare(0, False)

    def twelveHourMode(self, onOff):
        if onOff == True or onOff == False:
            self.alarmTwelveHour = onOff
            Config.writeParam('twelveHour', self.alarmTwelveHour)
        return self.alarmTwelveHour


class nixieClock(alarmGeneral):
    """Regular clock display"""
    def __init__(self):
        alarmGeneral.__init__(self)
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.defaultMenu = 'default'
        self.canonicalMenu = 'canonical'
        self.twelveHour = Config.readParam('twelveHour')
        if self.twelveHour == None:
            self.twelveHour = True
            Config.writeParam('twelveHour',self.twelveHour)
        self.antiCathodePoisoning = Config.readParam('antiCathodePoisoning')
        if self.antiCathodePoisoning == None:
            Config.writeParam('antiCathodePoisoning', True)
        self.acp = 0
        self.acpFlag = False

    def displayHandler(self):
        if self.antiCathodePoisoning:
            if (time.localtime().tm_min == 30) and (time.localtime().tm_sec < 1) and (self.acpFlag == False):
                self.acp = 0
                self.acpFlag = True
        if self.acpFlag == True:
            if self.acp < 100:
                self.acp += 1
            else:
                self.acp = 0
                self.acpFlag = False
            digits = range(0,6)
            timeNum = int(''.join(str(offsDig) for offsDig in [(digit+int(round(time.time()%9)))%10 for digit in digits]))
            if(timeNum < 100000):
                timeNum = timeNum + 1000000
        else:
            if self.twelveHour:
                self.acp = 0
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

    def twelveHourMode(self, onOff=None):
        if onOff == True or onOff == False:
            self.twelveHour = onOff
            Config.writeParam('twelveHour', self.twelveHour)
        return self.twelveHour

    def antiCathodePoisoning(self, onOff):
        if onOff == True or onOff == False:
            self.antiCathodePoisoning = onOff
            Config.writeParam('antiCathodePoisoning', self.antiCathodePoisoning)
        return self.antiCathodePoisoning


class nixieCalendar(nixieClock):
    """Calendar display mode"""
    def __init__(self):
        nixieClock.__init__(self)
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}

    def displayHandler(self):
        calNum = int(time.strftime('%m%d%y'))
        nixie.printTubes(calNum, 2)
        nixie.colons(False)


class btAudioStatus(alarmGeneral):
    """Display Bluetooth audio track status (elapsed/remaining time)"""
    def __init__(self):
        alarmGeneral.__init__(self)
        self.buttonHandlers = {'playpause':self.statusPlayPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'select':self.changeDisplayMode, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.defaultMenu = 'default'
        self.displayMode = 'elapsed'

    def setDefaultMenu(self):
        if self.playStatus() == True:
            self.defaultMenu = 'default'
        else:
            if hasattr(self, 'defaultMenu'):
                del self.defaultMenu

    def startHandler(self):
        self.setDefaultMenu()

    def statusPlayPause(self, direction):
        self.playPause(direction)
        self.setDefaultMenu()

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

    def changeDisplayMode(self, direction):
        if direction == -1:
            if self.displayMode == 'elapsed':
                self.displayMode = 'remaining'
                announce("Remaining time", False)
            else:
                self.displayMode = 'elapsed'
                announce("Elapsed time", False)


class ipAddress(btAudioGeneral):
    """Display IP address"""
    def __init__(self):
        btAudioGeneral.__init__(self)
        self.ticks = 0
        self.tickTime = 0
        self.defaultMenu = 'default'
        self.ip = '0.0.0.0.'.split('.')

    def startHandler(self):
        import socket
        import fcntl
        import struct
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ipVal = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', 'wlan0'[:15])
            )[20:24])
            self.ip = (ipVal+'.').split('.')
        except:
            self.ip = '0.0.0.0.'.split('.')
        print("IP Address: " + '.'.join(self.ip))
        self.ticks = 0
        self.tickTime = round(time.time())
        nixie.printTubes('', True)

    def stopHandler(self):
        nixie.printTubes('', True)

    def displayHandler(self):
        if self.tickTime+1.5 < round(time.time()):
            self.tickTime = round(time.time())
            self.ticks += 1
            if self.ticks > 3:
                self.ticks = 0
        ipNum = self.ip[self.ticks]
        nixie.printTubes(ipNum, 2)
        nixie.colons(False)


def callAntiCathodePoisoning(value=None):
    retVal = value
    for menuItem in Menu.modes:
        if hasattr(menuItem, 'antiCathodePoisoning'):
            retVal = menuItem.antiCathodePoisoning(value)
    return retVal


def callTwelveHour(value=None):
    retVal = value
    for menuItem in Menu.modes:
        if hasattr(menuItem, 'twelveHourMode'):
            retVal = menuItem.twelveHourMode(value)
    return retVal


# Attach menu modes
Menu.attachMode(nixieClock())           # Clock with playback controls
Menu.attachMode(btAudioStatus())        # Bluetooth audio status display
Menu.attachMode(nixieCalendar())        # Calendar
Menu.attachMode(alarmClock())           # Alarm clock
Menu.attachMode(ipAddress())            # IP address display

# Options menu (simplified - no shuffle/repeat for Bluetooth)
class option:
    """Option parameter descriptor"""
    def __init__(self, name='null', minimum=0, maximum=0, value=0, onget=None, onset=None):
        self.name = name
        self.min = minimum
        self.max = maximum
        self.value = value
        if onget is None:
            onget = self.dummy
        self.getter = onget
        if onset is None:
            onset = self.dummy
        self.setter = onset

    def playStatus(self):
        return True

    def dummy(self, value=0):
        return 0


class optionMenu(alarmGeneral):
    """Options configuration menu"""
    def __init__(self, options=[]):
        alarmGeneral.__init__(self)
        self.buttonHandlers = {'select':self.nextOption, 'minus':self.decValue,'plus':self.incValue, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.options = options
        self.playState = 0
        while len(options) < 6:
            options.append(option())
        self.selected = 0

    def playStatus(self):
        return True

    def appendOption(self, option):
        self.options.append(option)

    def refreshOptions(self):
        for option in self.options:
            option.value = option.getter()

    def startHandler(self):
        self.playState = self.canonicalPlayStatus()
        if self.playState:
            self.pause(-1)
        self.refreshOptions()
        nixie.startBlinking(self.selected)
        announce(self.options[self.selected].name, True)

    def stopHandler(self):
        if self.playState:
            self.play(-1)
        nixie.stopAllBlinking()

    def displayHandler(self):
        disp = ''
        for option in self.options:
            disp = disp + str(max(int(option.value),0))
        nixie.printTubes(disp)
        nixie.colons(False)

    def nextOption(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected + 1)%len(self.options)
            nixie.startBlinking(self.selected)
            announce(self.options[self.selected].name, True)

    def incValue(self,direction):
        if direction == -1:
            tempValue = self.options[self.selected].value + 1
            if tempValue > self.options[self.selected].max:
                tempValue = self.options[self.selected].min
            self.options[self.selected].value = tempValue
            self.options[self.selected].setter(tempValue)

    def decValue(self,direction):
        if direction == -1:
            tempValue = self.options[self.selected].value - 1
            if tempValue < self.options[self.selected].min:
                tempValue = self.options[self.selected].max
            self.options[self.selected].value = tempValue
            self.options[self.selected].setter(tempValue)


options = [option('twelve hour mode', 0, 1, 1, callTwelveHour, callTwelveHour),
           option('cathode protection', 0, 1, 1, callAntiCathodePoisoning, callAntiCathodePoisoning)]

Menu.attachMode(optionMenu(options))

# Main loop
print("Entering main loop...")
cycleCount = 0
cycleTime = 0.1  # seconds

while True:
    time.sleep(cycleTime)
    Menu.displayUpdate()
    cycleCount += 1
