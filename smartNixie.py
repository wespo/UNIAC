#Smart Nixie Python display driver.

#Interfaces are
#Nixie.printTube(tubeNumber, register)
#Nixie.printTubes(number) (will print highest six digits of the number)
#Nixie.setAddresses([list of i2c addresses of tubes])

#!/usr/bin/python

import smbus

class Nixie:
    addresses = [13,12,11,10,9,8]   #list of tube i2c address, by default
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    def setAddresses(self, addresses): #allows user change of addresses
        self.addresses = addresses
    def printTube(self, tubeNumber, value): #set the number displayed on an individual tube
        self.bus.write_byte_data(self.addresses[tubeNumber], 0x00, value)
    def printTubes(self, value, blank=0): #set the number displayed across all tubes, highest digits will be ignored
        tempValue = value;
        for address in reversed(self.addresses):
            if((blank == 1 or blank == 2) and tempValue%10 == 0 and tempValue/10 == 0):
                self.bus.write_byte_data(address, 0x00, 0x10)
            else:
                self.bus.write_byte_data(address, 0x00, tempValue%10)
            if(blank == 2 and value == 0):
                self.bus.write_byte_data(self.addresses[len(self.addresses)-1], 0x00, 0x00)
            tempValue = tempValue / 10
    def dimTube(self, tubeNumber, percent): #set brightness of an individual tube
        self.bus.write_byte_data(self.addresses[tubeNumber], 0x0B, percent)
    def dimTubes(self, percent): #set brightness of all tubes
        for address in self.addresses:
            self.bus.write_byte_data(address, 0x0B, percent)
    def setTubeRegister(self,tubeNumber, register, value):
        self.bus.write_byte_data(self.addresses[tubeNumber], register, value)
    def startBlinking(self, tubeNumber):
        self.bus.write_byte_data(self.addresses[tubeNumber], 0x0D, 0x03)
    def stopBlinking(self, tubeNumber):
        self.bus.write_byte_data(self.addresses[tubeNumber], 0x0D, 0x04)
    def stopAllBlinking(self):
        for address in self.addresses:
            self.bus.write_byte_data(address, 0x0D, 0x04)
