#Smart Nixie Python display driver.

#Interfaces are
#Nixie.printTube(tubeNumber, register)
#Nixie.printTubes(number) (will print highest six digits of the number)
#Nixie.setAddresses([list of i2c addresses of tubes])

#!/usr/bin/python

import smbus

class Nixie:
    addresses = [{'address':13, 'decimal':False, 'spare':False},{'address':12, 'decimal':False, 'spare':False},{'address':11, 'decimal':False, 'spare':False},{'address':10, 'decimal':False, 'spare':False}, {'address':9, 'decimal':False, 'spare':False},{'address':8, 'decimal':False, 'spare':False}]#list of tube i2c address, by default
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    def setAddresses(self, addresses): #allows user change of addresses
        self.addresses = addresses
    def muxSpares(self, tubeObj, value):
        decimal = tubeObj['decimal'] * 0x80
        spare = tubeObj['spare'] * 0x40
        bulbs = decimal + spare
        value = (value & 0x3F) | bulbs
        return value
    def setDecimal(self, tubeNumber, value):
        if value == True or value == False:
            self.addresses[tubeNumber]['decimal'] = value
    def setSpare(self, tubeNumber, value):
        if value == True or value == False:
            self.addresses[tubeNumber]['spare'] = value
    def printTube(self, tubeNumber, value): #set the number displayed on an individual tube
        value = self.muxSpares(self.addresses[tubeNumber], value)
        self.bus.write_byte_data(self.addresses[tubeNumber]['address'], 0x00, value)
    def printTubes(self, value, blank=0): #set the number displayed across all tubes, highest digits will be ignored
        tempValue = value;
        for address in reversed(self.addresses):
            if((blank == 1 or blank == 2) and tempValue%10 == 0 and tempValue/10 == 0):
                intValue = 0x10
                intValue = self.muxSpares(address, intValue)
                self.bus.write_byte_data(address['address'], 0x00, intValue)
            else:
                intValue = tempValue%10
                intValue = self.muxSpares(address, intValue)
                self.bus.write_byte_data(address['address'], 0x00, intValue)
            if(blank == 2 and value == 0):
                intValue = 0x00
                intValue = self.muxSpares(address, intValue)
                self.bus.write_byte_data(self.addresses[len(self.addresses)-1]['address'], 0x00, intValue)
            tempValue = tempValue / 10
    def dimTube(self, tubeNumber, percent): #set brightness of an individual tube
        self.bus.write_byte_data(self.addresses[tubeNumber]['address'], 0x0B, percent)
    def dimTubes(self, percent): #set brightness of all tubes
        for address in self.addresses:
            self.bus.write_byte_data(address['address'], 0x0B, percent)
    def setTubeRegister(self,tubeNumber, register, value):
        self.bus.write_byte_data(self.addresses[tubeNumber]['address'], register, value)
    def startBlinking(self, tubeNumber):
        self.bus.write_byte_data(self.addresses[tubeNumber]['address'], 0x0D, 0x03)
    def stopBlinking(self, tubeNumber):
        self.bus.write_byte_data(self.addresses[tubeNumber]['address'], 0x0D, 0x04)
    def stopAllBlinking(self):
        for address in self.addresses:
            self.bus.write_byte_data(address['address'], 0x0D, 0x04)
