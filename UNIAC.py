#!/usr/bin/python
import mpd
import smartNixie
import time
import pickle
import Menu as MenuClass
from socket import error as SocketError

ESPEAK_USER = 'pi'

import os
print 'Starting UNIAC: The Ultimate NIxie Alarm Clock'
print 'Model: UNIAC-S900-Vu-Pro'
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
nixie = smartNixie.Nixie()
nixie.dimTubes(75)
nixie.stopAllBlinking()

#setup menu system
Menu = MenuClass.menu()

#add buttons so menu system knows the hardware.
#the 'name' addribute will be used as a lookup on child classes.
buttons = {'plus':6, 'minus':12, 'mode':13, 'playpause':16, 'select':19,'snooze':20,'alarmenable':21} #list the physical buttons on the board
#add buttons to the menu system
Menu.addButtons(buttons)

def announce(message, block = False):
    if block:
        blockString = '\"\''
    else:
        blockString = '\" &\''
    newMessage = 'su ' + ESPEAK_USER + ' -c \'espeak -ven+f3 -k5 -a150 -p20 -s120 "' + message + blockString
    os.system(newMessage)

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
    def clientStatus(self): #method to reconnect to the client if need be
        try:
            client.status()
        except mpd.ConnectionError:
            print 'MPD Connection Error.'
            print 'Reconnecting to MPD service.'
            time.sleep(0.05)
            client.connect("localhost", 6600)
            time.sleep(0.05)
        except SocketError:
            print 'Socket Error.'
            print 'Reconnecting to MPD service'
            #time.sleep(0.05)
            #client.connect("localhost", 6600)
            time.sleep(0.05)
        except: 
            print 'Reconnecting to MPD service'
            time.sleep(0.05)
            client.connect("localhost", 6600)
            time.sleep(0.05)

    def playStatus(self):
        self.clientStatus()
        currentStatus = client.status();
        while 'state' not in currentStatus:
            currentStatus = client.status()
        if currentStatus['state'] == 'play':
            return 1
        else:
            return 0
    def playPause(self, direction):
        if direction == -1:
            self.clientStatus()
            currentStatus = client.status();
            while 'state' not in currentStatus:
                currentStatus = client.status()
            print "play"
            self.pause(-1)
            time.sleep(0.1)
    def play(self, direction):
        if direction == -1:
            self.clientStatus()
            try:
                client.play()
            except:
                pass
            time.sleep(0.1)
    def pause(self, direction, pauseIfPlaying=False):
        if pauseIfPlaying and self.playStatus() == False:
            return
        if direction == -1:
            self.clientStatus()
            try:
                client.pause()
            except:
                pass
            time.sleep(0.1)            
    def nextTrack(self, direction):
        if direction == -1:
            self.clientStatus()
            try:
                client.next()
            except:
                pass
            time.sleep(0.1)
    def previousTrack(self, direction):
        if direction == -1:
            self.clientStatus()
            try:
                client.previous()
            except:
                pass
            time.sleep(0.1)
    def clearPlaylist(self):
        self.clientStatus()
        client.clear()
    def loadPlaylist(self, playlist):
        self.clientStatus()
        client.load(playlist)
    def clientTime(self):
        self.clientStatus()
        currentStatus = client.status()
        while 'time' not in currentStatus:
            currentStatus = client.status()
        return client.status()['time'].split(':')
    def setRandom(self, value): #-1 to toggle
        self.clientStatus()
        currentStatus = client.status()
        while 'random' not in currentStatus:
            currentStatus = client.status()
        if value == -1:
            value = int(not(int(client.status()['random']))) #negate current value
        if value == 1 or value == 0:
            client.random(value)
    def getRandom(self):
        self.clientStatus()
        currentStatus = client.status()
        while 'random' not in currentStatus:
            currentStatus = client.status()
        return int(currentStatus['random']) #current value
    def getXfade(self):
        self.clientStatus()
        return int(client.status()['xfade']) #current value
    def setXfade(self, value): #-1 to toggle
        self.clientStatus()
        if value == -1:
            value = int(not(int(client.status()['xfade']))) #negate current value
        if value == 1 or value == 0:
            client.crossfade(value)

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
            if alarm.alarmEnabled:
                alarm.alarmEnabled = False
                alarm.playing = False
                print "Alarm Disabled"
            else:
                alarm.alarmEnabled = True
                print "Alarm Enabled"
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
    def alarmEvent(self):
        #print str(time.localtime().tm_hour) + " " + str(time.localtime().tm_min) + " " + str(time.localtime().tm_sec) + " : " + str(alarm.hours) + " " + str(alarm.minutes) + " " + str(alarm.seconds) + " : " + str(alarm.playing) + " " + str(alarm.alarmEnabled)
        if alarm.playing:
            return
        elif time.localtime().tm_hour == alarm.hours and time.localtime().tm_min == alarm.minutes and alarm.playing == False and alarm.alarmEnabled:
            alarm.playing = True
            print "Alarm Trigger"
            #play alarm
            announce("It is " +  time.strftime('%H, %M, %p.'), True)
            self.play(-1)
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
    def eventFunction(self):
        self.alarmEvent()
    def displayHandler(self):
        alarmTime = self.getAlarmTime()
        nixie.printTubes(alarmTime['hours']*10000 + alarmTime['minutes']*100)
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
        

class nixieClock(mpdGeneral, alarmGeneral): #regular ol' clock
    def __init__(self):
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
    def displayHandler(self):
        timeNum = int(time.strftime('%H%M%S')) #%I for 12-hour mode
        nixie.printTubes(timeNum, 2)

class mpdStatus(mpdGeneral, alarmGeneral):    #display song status (elapsed / remaining time)
    def __init__(self):
        self.buttonHandlers = {'playpause':self.playPause, 'plus':self.nextTrack, 'minus':self.previousTrack, 'select':self.changeDisplayMode, 'snooze':self.snooze, 'alarmenable':self.toggleAlarm}
        
        self.displayMode = 'elapsed'
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
        self.channels = ['Fallout: New Vegas (by tardskii)','All Out 90\'s (by spotify)','Billy Joel','Electro Swing All Day (by barrillel)','Soothing (by chalcedonian)','Ambient | Focus Friendly Video Game Music']
        self.selected = Config.readParam('selected', True, 0)
        self.changePlaylist(-1, False)
        self.prevSelected = 0
        self.playState = 1
        if self.playState:
            self.play(-1)

    def nextChannel(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected + 1)%6
            nixie.startBlinking(self.selected)
            announce(self.channels[self.selected])
    def prevChannel(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected - 1)%6
            nixie.startBlinking(self.selected)
            announce(self.channels[self.selected])
    def displayHandler(self):
        nixie.printTubes(123456)

    def changePlaylist(self,direction, announceChange=True):
        if direction == -1:
            self.clearPlaylist() #clear playlist
            self.loadPlaylist(self.channels[self.selected]) #load new playlist
            self.prevSelected = self.selected
            if announceChange:
                announce("station changed")
            Config.writeParam('selected', self.selected)
    
    def startHandler(self):
        self.playState = self.playStatus()
        if self.playState:
            self.pause(-1)
        nixie.startBlinking(self.selected)
        self.prevSelected = self.selected
        announce(self.channels[self.selected])
    def stopHandler(self):
        if self.playState:
            self.play(-1)
        nixie.stopAllBlinking()
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
    def appendOption(self, option):
        self.options.append(option)
    def refreshOptions(self):
        for option in self.options:
            option.value = option.getter()
    def startHandler(self):
        self.playState = self.playStatus()
        if self.playState:
            self.pause(-1)
        self.refreshOptions()
        nixie.startBlinking(self.selected)
        announce(self.options[self.selected].name)
    def stopHandler(self):
        if self.playState:
            self.play(-1)
        nixie.stopAllBlinking()
    def displayHandler(self):
        disp = ''
        for option in self.options:
            disp = disp + str(option.value)
        nixie.printTubes(int(disp))
    def nextOption(self,direction):
        if direction == -1:
            nixie.stopBlinking(self.selected)
            self.selected = (self.selected + 1)%len(self.options)
            nixie.startBlinking(self.selected)
            announce(self.options[self.selected].name)
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


Menu.attachMode(mpdStatus())            #spotify playing mode
Menu.attachMode(nixieClock())           #clock
#alarm.alarmEnabled = bool(Menu.buttonRead(buttons['alarmenable'])) #Special case. In this clock, the system is a mechanical toggle, so it needs to be detected on startup
Menu.attachMode(alarmClock())           #alarm clock
Menu.attachMode(selectStation())        #radio stations

options = [option('shuffle', 0, 1, 0, mpdGeneral().getRandom, mpdGeneral().setRandom)] # each option is unique. Add each one to handle things. could be cleaner
Menu.attachMode(optionMenu(options))    #options

while True:
    time.sleep(0.1)
    Menu.displayUpdate();
