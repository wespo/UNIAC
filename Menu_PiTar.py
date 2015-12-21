#contains all the UI menu classes
import os
import Adafruit_CharLCD as LCD
import RPi.GPIO as GPIO
import time
import copy

version = "0.01b"
#setup LCD
lcd = LCD.Adafruit_CharLCDPlate()
lcd.clear()
lcd.set_color(1,1,1)
lcd.message("Welcome to\nPiTar v" + version)
time.sleep(1.5)
class menu:
    #class for system menu, rotates through menu items by calling changeMode(1 for up, -1 for down).
    #Handles +/-/select for each menuItem by calling plusHandler, minusHandler, and SelectHandler on each event.
    def __init__(self):
        self.modes = [] #list of all available modes in the menu
        self.attachInit = False #flag for wether GPIO interrupt is attached
        GPIO.setmode(GPIO.BCM) #GPIO configuration
        GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.pedalState = GPIO.input(4)
    def attachMode(self, item):
        if self.attachInit <> True:
            self.attachEvent()
            self.attachInit = True
        self.modes.append(item)
    def modeUD(self, direction): #rotate through the various modes
        if(direction == -1): #mode down (rotate array right)
            self.modes.insert(0, self.modes.pop())
        elif(direction == 1): #mode up (rotate array left)
            self.modes.append(self.modes.pop(0))
        self.modes[0].displayHandler()
    def buttonUD(self, direction): #call the up / down button handlers for the current menu page
        GPIO.remove_event_detect(4)
        if(direction == 1):
            self.modes[0].plusHandler()
        if(direction == -1):
            self.modes[0].minusHandler()
        GPIO.add_event_detect(4, GPIO.BOTH, callback=self.pedalEvent, bouncetime=50)
    def pedalUp(self): #call the pedal up / down function for the current menu page and status
        print "pedalUP"
        self.modes[0].pedalUp()
    def pedalDown(self):
        print "pedalDOWN"
        self.modes[0].pedalDown()
    def buttonPress(self, upDown): #handles select button press event
            self.modes[0].buttonHandler(upDown)
    def printStates(self): #old debug cruft
        print self.modes[0].volume
    def displayUpdate(self):
        self.modes[0].displayHandler()
    def pedalEvent(self, channel): #only one interrupt for the pedal, so we have to check if the pedal is falling or rising and call the right handler
        time.sleep(0.05)
        inputState = GPIO.input(4)
        if inputState <> self.pedalState: #check that it's really a change of state.
            self.pedalState = inputState
            if(inputState == 0):
                self.pedalDown()
            else:
                self.pedalUp()
    def attachEvent(self):
        #re-setup pedal GPIO interrupt. Fixes pedal bug on calling os.system -_-
        GPIO.remove_event_detect(4)
        GPIO.add_event_detect(4, GPIO.BOTH, callback=self.pedalEvent, bouncetime=50)
    def readLCD(self): #reads the keypad buttons below the LCD screen.
        if(lcd.is_pressed(LCD.UP)):
            while(lcd.is_pressed(LCD.UP)):
                self.buttonUD(1)
                time.sleep(0.1)
        if(lcd.is_pressed(LCD.DOWN)):
            while(lcd.is_pressed(LCD.DOWN)):
                self.buttonUD(-1)
                time.sleep(0.1)
        if(lcd.is_pressed(LCD.LEFT)):
            while(lcd.is_pressed(LCD.LEFT)):
                self.modeUD(1)
                time.sleep(0.1)
        if(lcd.is_pressed(LCD.RIGHT)):
            while(lcd.is_pressed(LCD.RIGHT)):
                self.modeUD(-1)
                time.sleep(0.1)
        if(lcd.is_pressed(LCD.SELECT)):
            while(lcd.is_pressed(LCD.SELECT)):
                self.buttonPress(1)
                time.sleep(0.1)

def send2Pd(message=''): #function to send data to the signal chain. expects syntax of the format '<channel> <value>;', e.g. '30 1;'
    newMessage = "echo '" + message + "' | pdsend 3000"
    print newMessage
    os.system(newMessage)
    
#create volume mode
class volume:
    nameString = "Volume"
    def __init__(self, volumeLevel = 100):
        self.volumeLevel = volumeLevel
        self.oldVolumeLevel = 0
        self.volumeSet()
    def volumeChange (self, direction, amount):
        self.volumeLevel = self.volumeLevel + (direction * amount)
        if(self.volumeLevel > 100):
            self.volumeLevel = 100
        if (self.volumeLevel < 0):
            self.volumeLevel = 0
        self.volumeSet()
    def plusHandler(self):
        self.volumeChange(1,1)
    def minusHandler(self):
        self.volumeChange(-1,1)
    def volumeMute(self): #lazy mute just starts with a 0 in alternate volume buffer
        temp = self.volumeLevel
        self.volumeLevel = self.oldVolumeLevel
        self.oldVolumeLevel = temp
        self.volumeSet()
    def buttonHandler(self, upDown):
        self.volumeMute()
    def pedalUp(self):
        pass
    def pedalDown(self):
        pass
    def displayHandler(self):
        messageString = self.nameString + "\n" + "Volume = " + str(self.volumeLevel)
        lcd.clear()
        lcd.message(messageString)
        print(messageString)
    def volumeSet(self):
        messageString = "0 " + str(self.volumeLevel) + ";"
        send2Pd(messageString)
        self.displayHandler()
        
class looper: #class to interface with the looper module
    nameString = "Looper"
    def __init__(self):
        self.loopers = [] #master array of looper statuses
        for n in range(1,9):
            self.loopers.append({'id':n, 'playRecord':'Record','startStop':'stopped'})
    def plusHandler(self):
        self.loopers.append(self.loopers.pop(0))
        self.displayHandler()
    def minusHandler(self):
        self.loopers.insert(0, self.loopers.pop())
        self.displayHandler()
    def buttonHandler(self, upDown):
        if(self.loopers[0]['playRecord'] == 'Record'):
            self.loopers[0]['playRecord'] = 'Play'
            send2Pd(str(4*(self.loopers[0]['id']-1)+3) + ' ' + '1;') #send stop playing signal
        else:
            self.loopers[0]['playRecord'] = 'Record'
            send2Pd(str(4*(self.loopers[0]['id']-1)+2) + ' ' + '1;') #send stop recording signal
        self.loopers[0]['startStop'] = 'stopped' #always stop when switching

        self.displayHandler()
    def pedalUp(self):
        #these are the only outputs for this class. Send record/play start signal to appropriate looper
        if(self.loopers[0]['playRecord'] == 'Record'):
            send2Pd(str(4*(self.loopers[0]['id']-1)+2) + ' ' + '1;') #4 inputs per looper, loper channels are 1-32
            self.loopers[0]['startStop'] = 'stopped'
            self.buttonHandler(1) #treat it like the user switched to play mode?
            #self.displayHandler() #commented out because buttonHandler() calls display handler as well.
    def pedalDown(self):
        #these are the only outputs for this class. Send record/play start signal to appropriate looper
        if(self.loopers[0]['playRecord'] == 'Record'):
            send2Pd(str(4*(self.loopers[0]['id']-1)+1) + ' ' + '1;')
            self.loopers[0]['startStop'] = 'ongoing'
        elif(self.loopers[0]['playRecord'] == 'Play'):
            if(self.loopers[0]['startStop'] == 'ongoing'):
                send2Pd(str(4*(self.loopers[0]['id']-1)+3) + ' ' + '1;')
                self.loopers[0]['startStop'] = 'stopped'
            elif(self.loopers[0]['startStop'] == 'stopped'):
                send2Pd(str(4*(self.loopers[0]['id']-1)+4) + ' ' + '1;')
                self.loopers[0]['startStop'] = 'ongoing'
        self.displayHandler()
    def displayHandler(self):
        messageString = self.nameString + " " + str(self.loopers[0]['id']) + "\n" + self.loopers[0]['playRecord'] + " " + self.loopers[0]['startStop']
        print(messageString)
        lcd.clear()
        lcd.message(messageString)


class tremolo: #class to interface with the looper module
    nameString = "Tremolo"
    def __init__(self):
        #name, value, routeindex for Pd, scalefactor
        self.modes = [["Freq",0,32,4],["Shape",5,33,5], ["Depth",0,34,4],["Clear",-1,-1,"Up/Dn"]] #this should have been a list of dicts, too late!
        self.defaults = copy.deepcopy(self.modes) #backup for clear button.
        self.setAll()
    def setAll(self):
        for index in range(0, len(self.modes)): #yes this is terrible, I'm not spending undue time doing it "pythonically"
                if(self.modes[index][2] <> -1):
                    send2Pd(str(self.modes[index][2]) + ' ' + str(self.modes[index][1]) + ';')
    def clear(self):
        self.modes = copy.deepcopy(self.defaults)
        self.setAll()
            
    def plusHandler(self):
        if(self.modes[0][0] == "Clear"): #clear button is a special case
            self.clear()
        else:
            self.modes[0][1] = self.modes[0][1] + 1
            if(self.modes[0][1] > 100):
                self.modes[0][1] = 100
            send2Pd(str(self.modes[0][2]) + ' ' + str(self.modes[0][1]) + ';')
        self.displayHandler()
    def minusHandler(self):
        if(self.modes[0][0] == "Clear"):
            self.clear()
        else:
            self.modes[0][1] = self.modes[0][1] - 1
            if(self.modes[0][1] < 0):
                self.modes[0][1] = 0
            send2Pd(str(self.modes[0][2]) + ' ' + str(self.modes[0][1]) + ';')
        self.displayHandler()
    def buttonHandler(self, upDown):
        self.modes.append(self.modes.pop(0))
        self.displayHandler()
    def pedalUp(self):
        pass
    def pedalDown(self):
        pass
    def displayHandler(self):
        if(self.modes[0][1] == -1):
            messageString = self.nameString + '\n' + self.modes[0][0] + ": " + self.modes[0][3]
        else:
            messageString = self.nameString + '\n' + self.modes[0][0] + ': ' + str(float(self.modes[0][1])/self.modes[0][3])
        print(messageString)
        lcd.clear()
        lcd.message(messageString)
