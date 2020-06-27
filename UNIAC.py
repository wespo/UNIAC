#!/usr/bin/python
import nixieDisplay
import time
import re
import pickle
import Menu as MenuClass
from socket import error as SocketError
import sys
import os
import spotipyLogin
import setproctitle
import socket
import fcntl
import struct

##import sys
##logfilename = 'UNIAC.log'
##sys.stdout = open(logfilename, 'w')
##print logfilename

setproctitle.setproctitle("UNIAC")

configPath = '/home/pi/UNIAC/UNIAC.conf'

print 'Starting UNIAC: The Ultimate Nixie Internet Alarm Clock'
print 'Model: UNIAC-S1000-Portable'
print 'Version: 3.0'

if len(sys.argv) > 1:
    if(sys.argv[1] == "autostart"):
        print("starting mopidy and waiting 30 seconds")
        os.popen('mopidy &')
        time.sleep(30)

def UNIACPS():
    pythonProcesses = os.popen('ps -e | grep python').readlines()
    pythonProcesses.pop()
    for process in pythonProcesses:
        psNum = str.split(process)[0]
        print "killing: " + psNum
        os.system('sudo kill ' + psNum)

#UNIACPS()

nixie = nixieDisplay.Nixie()
nixie.dimTubes(75)
nixie.stopAllBlinking()
nixie.setAllFade(True)

#setup menu system
Menu = MenuClass.menu()

#add buttons so menu system knows the hardware.
#the 'name' addribute will be used as a lookup on child classes.
buttons = {'plus':5, 'minus':6, 'mode':4, 'playpause':3, 'select':2,'snooze':1,'alarmenable':0} #list the physical buttons on the board
#add buttons to the menu system
Menu.addButtons(buttons)

def announce(message, block = False):
    if block:
        blockString = '\"'
    else:
        blockString = '\" &'
    print message
    newMessage = 'sudo espeak -ven+f3 -k5 -a150 -p20 -s120 \"' + message + blockString
    os.system(newMessage)

def announcePlaylist(message, block = False): #cleans up playlist name string
    message = message.encode('ascii','ignore')
    re.sub("\s\s+"," ", message)
    print message
    parenIndex = message.find('(')
    if parenIndex > 0:
        message = message[0:parenIndex]
    message = ' '.join(str.split(message)[0:4])
    announce(message, block)

#start connections to Mopidy

class mpdGeneral: #general purpose class for MPD interfaces
    playStatusFlag = False
    playStatusFull = None
    playLastTimeChecked = 0
    def playStatus(self):
        if time.time() > (self.playLastTimeChecked + (5 * 60)):
            #print("Timeout, checking canonical play status.")
            return self.canonicalPlayStatus()
        else:
            return self.playStatusFlag
    def canonicalPlayStatus(self):
        playStatusRecv = spotipyLogin.sp.current_playback()
        self.playLastTimeChecked = time.time()
        if playStatusRecv != None:
            playStatus = playStatusRecv['is_playing']
            self.playStatusFull = playStatusRecv
        else:
            #print("Warning: Canonical Playstatus = None")
            playStatus = False
        playStatusFlag = playStatus
        return playStatus
    def playPause(self, direction):
        if direction == -1:
            if self.playStatus():
                return self.pause(-1)
            else:
                return self.play(-1)
        else:
            return -1
    def play(self, direction):
        print("Attempting to start playback")
        if direction == -1:
            retryCount = 0
            currentPlayback = spotipyLogin.sp.current_playback()
            print(currentPlayback)
            if currentPlayback != None:
                try:
                    startPlayback = spotipyLogin.sp.start_playback()
                    self.playStatusFlag = True
                    print("playback start succeeded")
                except:
                    while retryCount < 10:
                        print(spotipyLogin.sp.devices())
                        print("Generic playback start failed. Attempting to specifically start UNIAC")
                        try:
                            startPlayback = spotipyLogin.sp.start_playback(device_id=spotipyLogin.sp.uniac_id)
                            print("succeeded -- no error.")
                            self.playStatusFlag = True
                            return startPlayback
                        except:
                            print("warning: connection failed. Retrying " + str(10-retryCount) + " more times.")
                            time.sleep(1)
                        retryCount = retryCount+1
            else:
                #spotipyLogin.sp.start_playback(device_id=spotipyLogin.sp.uniac_id, context_uri=playlist['uri'], uris=[['item']['uri']])
                if self.playStatusFull != None and self.playStatusFull['context'] != None:
                    print("No play status found. Loading playlist with context: {}".format(self.playStatusFull['context']))
                    self.loadPlaylist(self.playStatusFull['context'])
                else:
                    print("No play status yet available. Please manually load (or initial startup). No playback started.")
            return -1
        else:
            return -1
    def pause(self, direction, pauseIfPlaying=False):
        self.playStatusFlag = False
        self.canonicalPlayStatus()
        currentPlayback = spotipyLogin.sp.current_playback()
        print(currentPlayback)
        if (currentPlayback != None) and (direction == -1):
            spotipyLogin.sp.pause_playback()
        else:
            print("Attempted to pause but playback status returned none. Playback is already paused.")
        return -1
    def nextTrack(self, direction):
        currentPlayback = spotipyLogin.sp.current_playback()
        print(currentPlayback)
        if (currentPlayback != None) and (direction == -1):
            spotipyLogin.sp.next_track()
        else:
            print("Attempted to select next track but playback status returned none. No track to advance to.")
        return -1
    def previousTrack(self, direction):
        currentPlayback = spotipyLogin.sp.current_playback()
        print(currentPlayback)
        if (currentPlayback != None) and (direction == -1):
            spotipyLogin.sp.previous_track()
        else:
            print("Attempted to select previous track but playback status returned none. No track to return to.")
        return -1
    def getPlaylists(self):
        lists = spotipyLogin.sp.user_playlists(spotipyLogin.sp.username)
        print "# Playlists found:" + str(lists['total'])
        return lists
    def loadPlaylist(self, playlist):
        retryCount = 0
        while retryCount < 10:
            try:
                spotipyLogin.sp.volume(0, device_id=spotipyLogin.sp.uniac_id)
                time.sleep(0.25)
                spotipyLogin.sp.start_playback(device_id=spotipyLogin.sp.uniac_id, context_uri=playlist['uri'])
                spotipyLogin.sp.pause_playback(device_id=spotipyLogin.sp.uniac_id)
                time.sleep(0.25)
                spotipyLogin.sp.volume(100, device_id=spotipyLogin.sp.uniac_id)
                print("Loaded playlist successfully")
                return
            except:
                print("warning: load failed. Retrying " + str(10-retryCount) + " more times.")
                time.sleep(3)
            retryCount = retryCount+1
    def clientTime(self):
        current = spotipyLogin.sp.currently_playing()
        # print("Client time = ")
        # print(type(current))
        if current != None:
            return [current['progress_ms'], current['item']['duration_ms']]
        else:
            return [0, 0]
    def setRandom(self, value): #-1 to toggle
        sh_state = spotipyLogin.sp.current_playback()['shuffle_state']
        if value == -1:
            spotipyLogin.sp.shuffle(not sh_state)
        else:
            spotipyLogin.sp.shuffle(value)
        return int(spotipyLogin.sp.current_playback()['shuffle_state'])
    def getRandom(self):
        return int(spotipyLogin.sp.current_playback()['shuffle_state'])
    def setRepeat(self, value): #-1 to toggle
        sh_state = spotipyLogin.sp.current_playback()['repeat_state']
        repeatLookup = {False:'off',True:'context'}
        if value == -1:
            spotipyLogin.sp.repeat(not repeatLookup[sh_state])
            return int(not repeatLookup[sh_state])
        else:
            spotipyLogin.sp.repeat(repeatLookup[value])
            return int(value)
    def getRepeat(self):
        repeatLookup = {'off':False,'context':True,'track':True}
        return int(repeatLookup[spotipyLogin.sp.current_playback()['repeat_state']])

class UNIACConfig:
    def __init__(self, path=configPath):
        self.path = path
        if os.path.isfile(self.path):
            confFileStream = open(self.path, 'r')
            self.conf = pickle.load(confFileStream)
            confFileStream.close()
        else:
            self.conf = {}
    def readParam(self, param, update = False, value = None):
        if param in self.conf:
            return self.conf[param]
        elif update:
            self.writeParam(param, value)
            return value
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
        self.hours = Config.readParam('hours', True, 0)
        self.minutes = Config.readParam('minutes', True, 0)
        self.seconds = Config.readParam('seconds', True, 0)
        self.alarmEnabled = Config.readParam('alarmEnabled', True, False)
        self.snoozeTime = Config.readParam('snoozeTime', True, 10)
        self.playing = Config.readParam('playing', True, False)
alarm = alarmInfo()
#special instance, fuck me. There has to be a better way to do this.
#alarm must be consistent and the same from all menu page classes,
#meaning they must all inherit from AlarmGeneral

class alarmGeneral (mpdGeneral): #stuff that all classes will need access to
    def toggleAlarm(self, direction):
        if direction == -1:
            if alarm.playing:
                self.pause(-1, True)
                alarm.playing = False
            if alarm.alarmEnabled:
                alarm.alarmEnabled = False
                alarm.playing = False
                print "Alarm Disabled"
                nixie.setDecimal(0,False)
            else:
                alarm.alarmEnabled = True
                print "Alarm Enabled"
                nixie.setDecimal(0,True)
    def snooze(self, direction):
        if direction == -1 and alarm.playing:
            alarm.minutes = alarm.minutes + alarm.snoozeTime
            if alarm.minutes >= 60:
                alarm.hours = alarm.hours + 1
                if alarm.minutes >= 24:
                    alarm.hours = alarm.hours - 24
            alarm.playing = False
            self.pause(-1, True)
    def setAlarmTime(self, hours, minutes, seconds):
        alarm.hours = hours%24
        alarm.minutes = minutes%60
        alarm.seconds = seconds%60
        Config.writeParam('hours', alarm.hours)
        Config.writeParam('minutes', alarm.minutes)
        Config.writeParam('seconds', alarm.seconds)
    def getAlarmTime(self):
        return {'hours':alarm.hours,'minutes':alarm.minutes,'seconds':alarm.seconds}
    def alarmEvent(self, twelveHour, Trigger=False):
        #play alarm
        if Trigger:
            print "Alarm Announce"
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
        #print str(time.localtime().tm_hour) + " " + str(time.localtime().tm_min) + " " + str(time.localtime().tm_sec) + " : " + str(alarm.hours) + " " + str(alarm.minutes) + " " + str(alarm.seconds) + " : " + str(alarm.playing) + " " + str(alarm.alarmEnabled)
        if alarm.playing:
            return False
        elif time.localtime().tm_hour == alarm.hours and time.localtime().tm_min == alarm.minutes and time.localtime().tm_sec <= 2 and alarm.playing == False and alarm.alarmEnabled:
            alarm.playing = True
            print "Alarm Trigger"
            return True
        return False
    def changeAlarmHours(self,direction):
        if direction == -1 or direction == 1:
            self.setAlarmTime(alarm.hours + direction, alarm.minutes, alarm.seconds)
    def changeAlarmMinutes(self,direction):
        if direction == -1 or direction == 1 or direction == -10 or direction == 10:
            self.setAlarmTime(alarm.hours, alarm.minutes + direction, alarm.seconds)

#handl
class alarmClock (alarmGeneral, mpdGeneral):
    def __init__(self):
        self.buttonHandlers = {'select':self.nextOption, 'minus':self.decValue,'plus':self.incValue, 'playpause':self.playPause,'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.selected = 1
        self.alarmTwelveHour = Config.readParam('twelveHour', True, True)
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

class nixieClock(mpdGeneral, alarmGeneral): #regular ol' clock
    def __init__(self):
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.defaultMenu = 'default'
        self.canonicalMenu = 'canonical'
        self.twelveHour = Config.readParam('twelveHour', True, True)
        self.antiCathodePoisoning = Config.readParam('antiCathodePoisoning', True, True)
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
                timeNum = timeNum + 1000000 #add leading zeros for midnight so it shows 00 for hours (the 1 is offscreen)
        else:
            if self.twelveHour:
                self.acp = 0
                timeNum = int(time.strftime('%I%M%S')) #%I for 12-hour mode
                if time.strftime('%p') == 'PM':
                    nixie.setSpare(0,True)
                else:
                    nixie.setSpare(0,False)
            else:
                timeNum = int(time.strftime('%H%M%S')) #%H for 24-hour mode
        if(timeNum < 10000):
            timeNum = timeNum + 1000000 #add leading zeros for midnight so it shows 00 for hours (the 1 is offscreen)
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

class ipAddress(mpdGeneral):
    def __init__(self):
        self.ticks = 0
        self.tickTime = 0
        self.defaultMenu = 'default'
        self.ip = '0.0.0.0.'.split('.')
    def startHandler(self):
        self.ip = (self.get_ip_address('wlan0')+'.').split('.')
        print("Self.IP:" + str(self.ip))
        self.ticks = 0
        self.tickTime = round(time.time())
        nixie.printTubes('', True)
        nixie.printTubes('', True)
    def stopHandler(self):
        nixie.printTubes('', True)
        nixie.printTubes('', True)
    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ipVal = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
        return ipVal
    def displayHandler(self):
        if self.tickTime+1.5 < round(time.time()):
            self.tickTime = round(time.time())
            self.ticks += 1
            if self.ticks > 4:
                self.ticks = 0
        ipNum = self.ip[self.ticks] #calendar
        print("SubIP: " + ipNum)
        nixie.printTubes(ipNum, 2)
        nixie.printTubes(ipNum, 2)
        nixie.colons(False)

class nixieCalendar(nixieClock):
    def __init__(self):
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.twelveHour = Config.readParam('twelveHour', True, True)
    def displayHandler(self):
        calNum = int(time.strftime('%m%d%y')) #calendar
        nixie.printTubes(calNum, 2)
        nixie.colons(False)
class mpdStatus(mpdGeneral, alarmGeneral):    #display song status (elapsed / remaining time)
    def __init__(self):
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
        [elapsedSeconds, totalSeconds] = self.clientTime()
        elapsedSeconds = int(round(elapsedSeconds/1000))
        totalSeconds = int(round(totalSeconds/1000))
        if self.displayMode == 'remaining':
            remainingSeconds = totalSeconds - elapsedSeconds
            displaySeconds = remainingSeconds
        else:
            displaySeconds = elapsedSeconds
        if displaySeconds < 0:
            displaySeconds = 0
        displayMinutes = int(displaySeconds/60)
        modSeconds = displaySeconds%60
        displayTime = displayMinutes*100 + modSeconds
        nixie.printTubes(displayTime, 2)
        nixie.colons(False)
    def changeDisplayMode(self, direction):
        if direction == -1:
            if self.displayMode == 'elapsed':
                self.displayMode = 'remaining'
            else:
                self.displayMode = 'elapsed'

class selectPlaylist(mpdGeneral, alarmGeneral):
    def __init__(self):
        self.buttonHandlers = {'plus':self.nextChannel,'minus':self.prevChannel, 'select':self.changePlaylist, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}

        #for now, pre-defined radio stations, will later be loaded from a flat file -- ultimately to be selected by a web interface
        self.playlists = self.getPlaylists()
        self.playlistURI = Config.readParam('playlistURI')
        if self.playlistURI == None: #no playlist loaded from config, default to first playlist
            self.setPlaylistDefault()
        self.selected = self.findPlaylistIndex(self.playlistURI)
        if self.selected == None: #could not find selected playlist uri. Deleted playlist?
            self.setPlaylistDefault()


        # if self.selected == 0: #I think this was for when playlist 0 was special and broken/
        #     self.selected = 1

        Config.writeParam('selected', self.selected)
        self.changePlaylist(-1, False)
        self.prevSelected = 0
        self.playState = 0
        self.changingPlaylist = False
        self.changingPlaylistIndex = 0
        self.changingPlaylistDelta = -1
        if self.playState:
            self.play(-1)
    def findPlaylistIndex(self, uri):
        index = 0
        for playlist in self.playlists['items']:
            # print("playlist: ")
            # print(self.playlists)
            # print("uri: ")
            # print(uri)
            if playlist['uri'] == uri:
                return index
            else:
                index = index+1
        return None
    def setPlaylistDefault(self):
        self.selected = 0
        self.playlistURI = self.playlists['items'][self.selected]['uri']
        Config.writeParam('playlistURI', self.playlistURI)
    def playStatus(self):
        return True
    def nextChannel(self,direction):
        if direction == -1:
            self.selected = self.selected + 1
            if self.selected >= self.playlists['total']:
                self.selected = 0
            self.displayHandler()
            announcePlaylist(self.playlists['items'][self.selected]['name'], True)
    def prevChannel(self,direction):
        if direction == -1:
            self.selected = self.selected - 1
            if self.selected < 0:
                self.selected = self.playlists['total'] - 1
            self.displayHandler()
            announcePlaylist(self.playlists['items'][self.selected]['name'], True)
    def displayHandler(self):
        nixie.printTubes(self.selected)
        nixie.colons(False)
    def changePlaylist(self,direction, announceChange=True):
        if direction == -1:
            print "self.selected = " + str(self.selected)
            print "self.playlist_name = " + self.playlists['items'][self.selected]['name']
            print "self.playlists (#) = " + str(self.playlists['total'])
            # print "List of playlists: "
            # print controlClient.listplaylists()
            print "loading..."
            nixie.printTubes("101010")
            self.changingPlaylist = True
            self.loadPlaylist(self.playlists['items'][self.selected])
            self.playlistURI = self.playlists['items'][self.selected]['uri']
            Config.writeParam('playlistURI', self.playlistURI)
            self.prevSelected = self.selected
            print "loaded"
            self.changingPlaylist = False
            if announceChange:
                announce("station changed", True)
            print "done"
    def startHandler(self):
        self.playState = self.canonicalPlayStatus()
        self.pause(-1)
        self.playlists = self.getPlaylists()

        self.selected = self.findPlaylistIndex(self.playlistURI)
        self.prevSelected = self.selected

        announcePlaylist(self.playlists['items'][self.selected]['name'], True)
    def stopHandler(self):
        if self.playState:
            self.play(-1)
        self.selected = self.prevSelected

class option (mpdGeneral): #class to describe how to parse each option parameter
    def __init__(self, name='null', minimum=0, maximum=0, value = 0, onget=None, onset=None):
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
    def playStatus(self): #function to tell menu to keep the amp on when on this page
        return True
    def dummy(self, value = 0): #dummy function for fake options. It's 2AM.
        return 0
    def setSetter(self, func=None):
        if func is None:
            func = self.dummy
        self.setter = func
    def clearSetter(self):
        self.setSetter()
    def setGetter(self, func=None):
        if func is None:
            func = self.dummy
        self.getter = func
    def clearGetter(self):
        self.setGetter()

class optionMenu (mpdGeneral, alarmGeneral):
    def __init__(self, options=[]):
        self.buttonHandlers = {'select':self.nextOption, 'minus':self.decValue,'plus':self.incValue, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        self.options = options
        self.playState = 0
        while len(options) < 6:
            options.append(option())
        self.selected = 0
    def playStatus(self): #function to tell menu to keep the amp on when on this page
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
            #Now set the value
            self.options[self.selected].setter(tempValue)
    def decValue(self,direction):
        if direction == -1:
            tempValue = self.options[self.selected].value - 1
            if tempValue < self.options[self.selected].min:
                tempValue = self.options[self.selected].max

            self.options[self.selected].value = tempValue
            #Now set the value
            self.options[self.selected].setter(tempValue)


# def callSetting(settingName, value):
#     for menuItem in Menu.modes:
#         if hasattr(menuItem, settingName):
#             itemHandle = getattribute(menuItem,settingName)
#             menuItem.itemHandle = value
#             Config.writeParam(settingName, value)
#     return value

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

Menu.attachMode(nixieClock())           #clock
Menu.attachMode(mpdStatus())            #spotify playing mode
Menu.attachMode(nixieCalendar())           #calendar
Menu.attachMode(alarmClock())           #alarm clock
Menu.attachMode(selectPlaylist())       #playlists
#Menu.attachMode(selectStation())        #radio stations
#Menu.modes.pop()

options = [option('shuffle', 0, 1, 0, mpdGeneral().getRandom, mpdGeneral().setRandom),
           option('repeat', 0, 1, 0, mpdGeneral().getRepeat, mpdGeneral().setRepeat),
           option('twelve hour mode', 0, 1, 1, callTwelveHour, callTwelveHour),
           option('cathode protection', 0, 1, 1, callAntiCathodePoisoning, callAntiCathodePoisoning)] # each option is unique. Add each one to handle things. could be cleaner
Menu.attachMode(optionMenu(options))    #options
Menu.attachMode(ipAddress())       #playlists
# cycleCount = 0;
# keepAliveTime = 0.5 #minutes
cycleTime = 0.1 #seconds
while True:
    time.sleep(cycleTime)
    Menu.displayUpdate(); #update the display
    # cycleCount += 1
    # if cycleCount >= (keepAliveTime * 60 / cycleTime): #when the number of requesite cycles has passed, keep connections alive.
    #     cycleCount = 0
    #     print "Keep Alive"
    #     controlClient.keepAlive()
    #     statusClient.keepAlive()
    #     #displayClient.keepAlive()
