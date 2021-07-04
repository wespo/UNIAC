#contains all the UI menu classes
import RPi.GPIO as GPIO
import time
from MCP230XX import MCP230XX as MCP230XX
import os

version = "0.04"

class menu:
    #class for system menu, rotates through menu items by calling changeMode(1 for button up, -1 for button down).
    #'mode' is a special case button that moves to the next menu -- see the buttonPress method
    def __init__(self, buttons = {}):
        self.modes = [] #list of all available modes in the menu
        self.eventFunctions = []
        self.buttons = buttons
        GPIO.setmode(GPIO.BCM) #GPIO configuration
        self.systemLock = False #flag to keep display function from colliding with MPD
        self.pressTime = int(time.time())
        self.button_lights = 7 #UNIAC 3.0 (MCP23008) #22 #UNIAC 2.0 #5 UNIAC 1.0
        self.button_light_status = True
        self.button_timeout = 10
        #temporary amplifier perma-on:
        self.amp = 17 #UNIAC-003? (Untested) 11# (single board -- questionably tested) 18 (Original)
        self.mcpAddress = 0x20
        self.intPin = 4
        self.shdnPin = 22
        self.MCP = MCP230XX('MCP23008', self.mcpAddress, '16bit')
        self.MCP.interrupt_options(outputType = 'activehigh', bankControl = 'separate')

        GPIO.setwarnings(False)
        #amp
        GPIO.setup(self.amp, GPIO.OUT)
        GPIO.output(self.amp, True)
        #lights
        self.MCP.set_mode(self.button_lights,'output')
        self.MCP.output(self.button_lights, 1);
        time.sleep(1);
        self.MCP.output(self.button_lights, 0);
        #interrupts
        GPIO.setup(self.intPin,GPIO.IN)
        GPIO.add_event_detect(self.intPin,GPIO.RISING,callback=self.MCP.callbackA)
        GPIO.setup(self.shdnPin,GPIO.IN)
        GPIO.add_event_detect(self.shdnPin,GPIO.RISING,callback=self.shdn)
        try:
            self.MCP.callbackA(1) #fixes hung up library due to unserviced interrupt
        except:
            print("No unserviced interrupts. Yay!")
        self.startup()

    #shutdown handler
    def shdn(self, item):
        print("Shutting down, at the command of the soft power down subsystem...")
        os.system("sudo shutdown -h now")
    def startup(self):
        powerPins = {'nixie_hven':[25,2], 'nixie_en':[23,2], 'vu_en':[24,5], 'vu_hven':[12,2]} #gpio for power up
        for powerPin in ['nixie_en','vu_hven','vu_en','nixie_hven']:
            print("Powering up " + powerPin)
            pin = powerPins[powerPin][0]
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin, True)
            time.sleep(powerPins[powerPin][1])


    #mode handlers
    def attachMode(self, item):
        self.modes.append(item)
        if hasattr(item,'eventFunction'):
            self.eventFunctions.append(item.eventFunction)
        if len(self.modes) == 1 and hasattr(self.modes[0],'startHandler'):
            self.modes[0].startHandler()
    def changeMode(self, direction): #function rotates modes array, attaches any mode button handlers to matching buttons
        if hasattr(self.modes[0],'stopHandler'):
            self.modes[0].stopHandler()
        if(direction == -1): #mode down (rotate array right)
            self.modes.insert(0, self.modes.pop())
        elif(direction == 1): #mode up (rotate array left)
            self.modes.append(self.modes.pop(0))
        if hasattr(self.modes[0],'startHandler'):
            self.modes[0].startHandler()
        self.modes[0].displayHandler()
    #rotates through the list until if finds a default mode.
    #a menu page with a 'default' attribute is one that we want to land on when the system goes idle
    #if it is already on such a page, it will do nothing, but if not if will cycle through pages until
    #it finds a page with the default attribute
    def defaultMode(self, direction = 1):
        if hasattr(self.modes[0],'defaultMenu'): #are we already on a default menu?
                return
        if hasattr(self.modes[0],'stopHandler'):
            #If the current menu is not a default,
            #we're going to have to change. Call
            #the stop handler if there is one
            self.modes[0].stopHandler()
        while (hasattr(self.modes[0],'canonicalMenu') == False):
            if(direction == -1): #mode down (rotate array right)
                self.modes.insert(0, self.modes.pop())
            elif(direction == 1): #mode up (rotate array left)
                self.modes.append(self.modes.pop(0))
        if hasattr(self.modes[0],'startHandler'):
            self.modes[0].startHandler()
        self.modes[0].displayHandler()
    #button handlers
    def addButton(self, name, channel):    #adds a button to the system the name will be used by the member menus
        self.buttons[channel] = name
        self.MCP.set_mode(channel, 'input')
        self.MCP.add_interrupt(channel, callbackFunctHigh=self.buttonPress)
    def addButtons(self, buttonList): #takes a dictionary of buttons and channels the keys of the dictionary will be used by the member menus
        newButtons = dict(zip(buttonList.values(),buttonList))
        self.buttons.update(newButtons)
        for channel in self.buttons.keys():
            self.MCP.set_mode(channel, 'input')
            self.MCP.add_interrupt(channel, callbackFunctHigh=self.buttonPress)
    def removeButton(self, name):          #removes a button
        GPIO.remove_event_detect(self.buttons[name])
        del self.buttons[name]
    def buttonPress(self, channel): #only one interrupt for the pedal, so we have to check if the pedal is falling or rising and call the right handler
        self.pressTime = int(time.time())
        self.MCP.output(self.button_lights, True);
        self.button_light_status = True
        if self.buttons[channel] == 'mode':
                self.changeMode(1)
        elif self.buttons[channel] in self.modes[0].buttonHandlers.keys():
            self.systemLock = True
            self.modes[0].buttonHandlers[self.buttons[channel]](-1)
        # elif channel ==
        self.systemLock = False
        time.sleep(0.1)
    def buttonRead(self, channel):
        return self.MCP.input(channel)
    #display handler
    def displayUpdate(self):    #function updates the display with the current handler
        while self.systemLock == True:
            pass
        #try:
        if(((int(time.time()) - self.pressTime) > self.button_timeout) and (self.button_light_status == True)):
            self.MCP.output(self.button_lights, False)
            self.button_light_status = False
            self.defaultMode()
        self.modes[0].displayHandler()
        for eventFunction in self.eventFunctions:
            if eventFunction():
                GPIO.output(self.amp, True)
                time.sleep(0.5)
                print "calling alarm announce"
                eventFunction(True)
        # ps = self.modes[0].playStatus();
        self.modes[0].playStatus()
        ps = 1
        if ps == 1:
            GPIO.output(self.amp, True)
        elif ps == 0:
            GPIO.output(self.amp, False)
        else:
            print("play status error, leaving amp in previous state")
        #except:
        #    pass
