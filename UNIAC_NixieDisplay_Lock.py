#!/usr/bin/python
import mpd
import nixieDisplay
import time
import re
import pickle
import Menu as MenuClass
from socket import error as SocketError
import sys

ESPEAK_USER = 'pi'


##import sys
##logfilename = 'UNIAC.log'
##sys.stdout = open(logfilename, 'w')
##print logfilename

import os
print 'Starting UNIAC: The Ultimate Nixie Internet Alarm Clock'
print 'Model: UNIAC-S1000-Portable'
print 'Version: 2.1'

if len(sys.argv) > 1:
    if(sys.argv[1] == "autostart"):
        print("starting mopidy in 30 seconds")
        time.sleep(30)
        os.popen('mopidy &')

def UNIACPS():
    pythonProcesses = os.popen('ps -e | grep python').readlines()
    pythonProcesses.pop()
    for process in pythonProcesses:
        psNum = str.split(process)[0]
        print "killing: " + psNum
        os.system('sudo kill ' + psNum)

#UNIACPS()

# use_unicode will enable the utf-8 mode for python2
# see http://pythonhosted.org/python-mpd2/topics/advanced.html#unicode-handling
client = mpd.MPDClient(use_unicode=True)
startupTimeout = 120
print "Attempting to connect to MPD Daemon. Process will time out after " + str(startupTimeout) + " seconds."
t = time.time() + startupTimeout #wait up to two minutes for mopidy to start.
while time.time()<t:
    try:
        client.connect("localhost", 6600)
        print "Connected Successfully"
        break
    except:
        pass

##if client.status()['playlistlength'] == '0':
##    client.load('Fallout: New Vegas (by tardskii)')
##if client.status()['state'] <> 'play':
##    client.play()
##    print "Play"
nixie = nixieDisplay.Nixie()
nixie.dimTubes(75)
nixie.stopAllBlinking()
nixie.setAllFade(True)

#setup menu system
Menu = MenuClass.menu()

#add buttons so menu system knows the hardware.
#the 'name' addribute will be used as a lookup on child classes.
buttons = {'plus':16, 'minus':20, 'mode':26, 'playpause':12, 'select':13,'snooze':6,'alarmenable':5} #list the physical buttons on the board
#add buttons to the menu system
Menu.addButtons(buttons)

def announce(message, block = False):
    if block:
        blockString = '\"'
    else:
        blockString = '\" &'


    newMessage = 'sudo espeak -ven+f3 -k5 -a150 -p20 -s120 \"' + message + blockString
    #os.system(newMessage)

def announcePlaylist(message, block = False): #cleans up playlist name string
    message = message.encode('ascii','ignore')
    re.sub("\s\s+"," ", message)
    print message
    parenIndex = message.find('(')
    if parenIndex > 0:
        message = message[0:parenIndex]
    message = ' '.join(str.split(message)[0:4])
    announce(message, block)

class config:
    def __init__(self, path='UNIAC.conf'):
        self.path = path
        if os.path.isfile(self.path):
            confFileStream = open(self.path, 'r')
            self.conf = pickle.load(confFileStream)
            confFileStream.close()
        else:            self.conf = {}
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

Config = config()

class mpdGeneral: #general purpose class for MPD interfaces
    blocked = False;
    def isConnected(self): #method to reconnect to the client if need be
        try:
            client.ping()
        except (mpd.MPDError, mpd.ConnectionError, IOError):
            print 'MPD Connection Error.'
            print 'Reconnecting to MPD service.'
            try:
                client.connect("localhost", 6600)
                return True
            except:
                print "Reconnect failed"
                return False

        except:
            "Other error, go fuck yourself"
            return False
    def playStatus(self):
        if mpdGeneral.blocked == True:
            print("PlayStatus: MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if self.isConnected() == False:
            mpdGeneral.blocked = False
            return -1
        currentStatus = client.status();
        while 'state' not in currentStatus:
            currentStatus = client.status()
        if currentStatus['state'] == 'play':
            mpdGeneral.blocked = False
            return 1
        else:
            mpdGeneral.blocked = False
            return 0
    def canonicalPlayStatus(self):
        if mpdGeneral.blocked == True:
            print("canonicalPlayStatus MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if self.isConnected() == False:
            mpdGeneral.blocked = False
            return -1
        currentStatus = client.status();
        while 'state' not in currentStatus:
            currentStatus = client.status()
        if currentStatus['state'] == 'play':
            mpdGeneral.blocked = False
            return 1
        else:
            mpdGeneral.blocked = False
            return 0
    def playPause(self, direction):
        if direction == -1:
            self.isConnected()
            currentStatus = client.status();
            while 'state' not in currentStatus:
                currentStatus = client.status()
            print "play"
            pauseTimeout = 0;
            sleepCyc = 0.05;
            while self.pause(-1) < 0:
                print "trying to pause"
                time.sleep(sleepCyc)
                pauseTimeout = pauseTimeout + sleepCyc
                if pauseTimeout > 2:
                    print "gave up"
                    break;

    def play(self, direction):
        if mpdGeneral.blocked == True:
            print("play MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if direction == -1:
            self.isConnected()
            try:
                client.play()
            except:
                pass
            time.sleep(0.1)
            mpdGeneral.blocked = False
    def pause(self, direction, pauseIfPlaying=False):
        if mpdGeneral.blocked == True:
            print("pause MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if pauseIfPlaying and self.playStatus() == False:
            mpdGeneral.blocked = False
            return 0
        if direction == -1:
            self.isConnected()
            try:
                client.pause()
            except:
                print "error in pause"
            time.sleep(0.1)
            mpdGeneral.blocked = False
            return 0
    def nextTrack(self, direction):
        if mpdGeneral.blocked == True:
            print("nextTrack MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if direction == -1:
            self.isConnected()
            try:
                print("next")
                client.next()
            except:
                pass
            time.sleep(0.1)
        mpdGeneral.blocked = False
    def previousTrack(self, direction):
        if mpdGeneral.blocked == True:
            print("previousTrack MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        if direction == -1:
            self.isConnected()
            try:
                client.previous()
                mpdGeneral.blocked = False
                return True
            except:
                mpdGeneral.blocked = False
                return False
            time.sleep(0.1)
    def clearPlaylist(self):
        if mpdGeneral.blocked == True:
            print("clearPlaylist MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        try:
            client.clear()
            mpdGeneral.blocked = False
            return True
        except:
            mpdGeneral.blocked = False
            return False
    def getPlaylists(self):
        if mpdGeneral.blocked == True:
            print("getPlaylists MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        try:
            lists = [{}]
            count = 0
            while lists[0].has_key('playlist') == False:
                lists = client.listplaylists()
                count = count + 1
                print "# Playlists found:" + str(len(lists))
                if count > 100000:
                    mpdGeneral.blocked = False
                    return []
            mpdGeneral.blocked = False
            return lists
        except:
            mpdGeneral.blocked = False
            return []
    def loadPlaylist(self, playlist):
        if mpdGeneral.blocked == True:
            print("loadPlaylist MPDGeneral Blocked. Retry Later")
            return False
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        loadCount = 0
        while loadCount < 10:
            wd = Watchdog(5)
            try:
                client.load(playlist)
            except Watchdog:
                print("client load timeout. Retrying " + str(10-loadCount) + " more times.")
            wd.stop()
            loadCount = loadCount + 1

        mpdGeneral.blocked = False
        return True
    def clientTime(self):
        if mpdGeneral.blocked == True:
            print("clientTime MPDGeneral Blocked. Retry Later")
            return [0,0]
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        currentStatus = client.status()
        while 'time' not in currentStatus:
            currentStatus = client.status()
        mpdGeneral.blocked = False
        #print "time: " + currentStatus['time']
        return currentStatus['time'].split(':')
    def setRandom(self, value): #-1 to toggle
        if mpdGeneral.blocked == True:
            print("setRandom MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        client.random(self.setParam('random', value))
        mpdGeneral.blocked = False
    def getRandom(self):
        if mpdGeneral.blocked == True:
            print("getRandom MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        mpdGeneral.blocked = False
        return self.getParam('random') #current value
    def setRepeat(self, value): #-1 to toggle
        if mpdGeneral.blocked == True:
            print("setRepeat MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        client.repeat(self.setParam('repeat', value))
        mpdGeneral.blocked = False
    def getRepeat(self):
        if mpdGeneral.blocked == True:
            print("getRepeat MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        mpdGeneral.blocked = False
        return self.getParam('repeat') #current value
    def setParam(self, param, value): #-1 to toggle
        self.isConnected()
        currentStatus = client.status()
        while param not in currentStatus:
            currentStatus = client.status()
        if value == -1:
            value = int(not(int(client.status()[param]))) #negate current value
        if value == 1 or value == 0:
            return value
    def getParam(self, param):
        self.isConnected()
        currentStatus = client.status()
        while param not in currentStatus:
            currentStatus = client.status()
        return int(currentStatus[param]) #current value
    def getXfade(self):
        if mpdGeneral.blocked == True:
            print("getXfade MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        curVal = int(client.status()['xfade']) #current value
        mpdGeneral.blocked = False
        return curVal
    def setXfade(self, value): #-1 to toggle
        if mpdGeneral.blocked == True:
            print("setXfade MPDGeneral Blocked. Retry Later")
            return -1
        else:
            mpdGeneral.blocked = True
        self.isConnected()
        if value == -1:
            value = int(not(int(client.status()['xfade']))) #negate current value
        if value == 1 or value == 0:
            client.crossfade(value)
        mpdGeneral.blocked = False

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
        self.twelveHour = Config.readParam('twelveHour', True, True)
    def displayHandler(self):
        if self.twelveHour:
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
    def startHandler(self):
        if self.playStatus():
            self.defaultMenu = 'default'
        else:
            if hasattr(self, 'defaultMenu'):
                del self.defaultMenu
    def statusPlayPause(self, direction):
        self.playPause(direction)
        if self.playStatus():
            self.defaultMenu = 'default'
        else:
            if hasattr(self, 'defaultMenu'):
                del self.defaultMenu
    def displayHandler(self):
        [elapsedSeconds, totalSeconds] = self.clientTime()
        elapsedSeconds = int(elapsedSeconds)
        totalSeconds = int(totalSeconds)
        if self.displayMode == 'remaining':
            remainingSeconds = totalSeconds - elapsedSeconds
            displaySeconds = remainingSeconds
        else:
            displaySeconds = elapsedSeconds
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

class selectStation(mpdGeneral, alarmGeneral):
    def __init__(self):
        self.buttonHandlers = {'plus':self.nextChannel,'minus':self.prevChannel, 'select':self.changePlaylist, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}

        #for now, pre-defined radio stations, will later be loaded from a flat file -- ultimately to be selected by a web interface
        self.channels = ['Fallout: New Vegas (by tardskii)',"All Out 90's (by spotify)",'Billy Joel','Electro Swing All Day (by barrillel)','Soothing (by chalcedonian)','Ambient | Focus Friendly Video Game Music']
        self.selected = Config.readParam('selected', True, 0)
        self.changePlaylist(-1, False)
        self.prevSelected = 0
        self.playState = 1
        if self.playState:
            self.play(-1)
    def playStatus(self):
        return True
    def nextChannel(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected + 1)%6
            nixie.startBlinking(self.selected)
            announce(self.channels[self.selected], True)
    def prevChannel(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected - 1)%6
            nixie.startBlinking(self.selected)
            announce(self.channels[self.selected], True)
    def displayHandler(self):
        nixie.printTubes(123456)
        nixie.colons(True)
    def changePlaylist(self,direction, announceChange=True):
        if direction == -1:
            count = 0;
            while self.clearPlaylist() == False: #clear playlist
                count = count + 1
                time.sleep(0.1)
                if count > 20:
                    break
            count = 0;
            while self.loadPlaylist(self.channels[self.selected]) == False: #load new playlist
                count = count + 1
                time.sleep(0.1)
                if count > 20:
                    break
            self.prevSelected = self.selected
            if announceChange:
                announce("station changed", True)
            Config.writeParam('selected', self.selected)

    def startHandler(self):
        self.playState = self.canonicalPlayStatus()
        if self.playState:
            self.pause(-1)
        nixie.startBlinking(self.selected)
        self.prevSelected = self.selected
        announce(self.channels[self.selected], True)
    def stopHandler(self):
        if self.playState:
            self.play(-1)
        nixie.stopAllBlinking()
        self.selected = self.prevSelected

class selectPlaylist(mpdGeneral, alarmGeneral):
    def __init__(self):
        self.buttonHandlers = {'plus':self.nextChannel,'minus':self.prevChannel, 'select':self.changePlaylist, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}

        #for now, pre-defined radio stations, will later be loaded from a flat file -- ultimately to be selected by a web interface
        self.playlist_name = 'playlist' #playlist name is the 3rd element
        self.channels = self.getPlaylists()
        self.selected = Config.readParam('selected', True, 0)
        if self.selected == 0:
            self.selected = 1

        Config.writeParam('selected', self.selected)
        self.changePlaylist(-1, False)
        self.prevSelected = 0
        self.playState = 1
        if self.playState:
            self.play(-1)
    def playStatus(self):
        return True
    def nextChannel(self,direction):
        if direction == -1:
            self.selected = self.selected + 1
            print(self.channels)
            if self.selected >= len(self.channels):
                self.selected = 0
            self.displayHandler()
            announcePlaylist(self.channels[self.selected][self.playlist_name], True)
    def prevChannel(self,direction):
        if direction == -1:
            self.selected = self.selected - 1
            if self.selected < 0:
                self.selected = len(self.channels) - 1
            self.displayHandler()
            announcePlaylist(self.channels[self.selected][self.playlist_name], True)
    def displayHandler(self):
        nixie.printTubes(self.selected)
        nixie.colons(False)
    def changePlaylist(self,direction, announceChange=True):
        if direction == -1:
            count = 0;
            while self.clearPlaylist() == False: #clear playlist
                count = count + 1
                time.sleep(0.1)
                if count > 20:
                    break
            count = 0;
            print "self.selected = " + str(self.selected)
            print "self.playlist_name = " + self.playlist_name
            print "self.channels (#) = " + str(len(self.channels))
            # print "List of playlists: "
            # print client.listplaylists()
            print "self.channels[self.selected][self.playlist_name]" + self.channels[self.selected][self.playlist_name]
            while self.loadPlaylist(self.channels[self.selected][self.playlist_name]) == False: #load new playlist
                print "load playlist timeout. retrying."
                count = count + 1
                time.sleep(0.01)
                if count > 20:
                    break
            self.prevSelected = self.selected
            print "loaded"
            if announceChange:
                announce("station changed", True)
            Config.writeParam('selected', self.selected)

    def startHandler(self):
        self.playState = self.canonicalPlayStatus()
        self.channels = self.getPlaylists()
        if self.playState:
            self.pause(-1)
        self.prevSelected = self.selected
        announcePlaylist(self.channels[self.selected][self.playlist_name], True)
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
        nixie.printTubes(int(disp))
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

def callTwelveHour(value=None):
    retVal = value
    for menuItem in Menu.modes:
        if hasattr(menuItem, 'twelveHourMode'):
            retVal = menuItem.twelveHourMode(value)
    return retVal


Menu.attachMode(nixieClock())           #clock
Menu.attachMode(mpdStatus())            #spotify playing mode
Menu.attachMode(nixieCalendar())           #calendar
#alarm.alarmEnabled = bool(Menu.buttonRead(buttons['alarmenable'])) #Special case. In this clock, the system is a mechanical toggle, so it needs to be detected on startup
Menu.attachMode(alarmClock())           #alarm clock
Menu.attachMode(selectPlaylist())       #playlists
#Menu.attachMode(selectStation())        #radio stations
#Menu.modes.pop()
options = [option('shuffle', 0, 1, 0, mpdGeneral().getRandom, mpdGeneral().setRandom),
           option('repeat', 0, 1, 0, mpdGeneral().getRepeat, mpdGeneral().setRepeat),
           option('twelve hour mode', 0, 1, 1, callTwelveHour, callTwelveHour)] # each option is unique. Add each one to handle things. could be cleaner
Menu.attachMode(optionMenu(options))    #options

cycleCount = 0;
cycleTime = 0.1 #seconds
keepAliveTime = 2 #minutes
while True:
    time.sleep(cycleTime)
    Menu.displayUpdate();
    cycleCount += 1
    if cycleCount >= (keepAliveTime * 60 / cycleTime): #every 5 minutes
        cycleCount = 0
        print "Keep Alive"
        Menu.modes[0].isConnected()