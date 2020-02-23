#Smart Nixie Python display driver.

#Interfaces are
#Nixie.printTube(tubeNumber, register)
#Nixie.printTubes(number) (will print highest six digits of the number)
#Nixie.setAddresses([list of i2c addresses of tubes])

#!/usr/bin/python

import smbus

def StringToBytes(val):
    retVal = []
    for c in val:
            retVal.append(ord(c))
    return retVal

class Nixie:
    blankState = {'index':0, 'value':10, 'dpl':False, 'dpr':False, 'blink':False, 'fade':False};
    zeroState = {'index':0, 'value':0, 'dpl':False, 'dpr':False, 'blink':False, 'fade':False};
    tubeStates = [zeroState.copy(),zeroState.copy(),zeroState.copy(),zeroState.copy(),zeroState.copy(),zeroState.copy()]#list of tube
    address = 9;
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    def __init__(self):
        self.initTubeStates();
    def initTubeStates(self):
        for idx in range(len(self.tubeStates)):
            self.tubeStates[idx]['index'] = idx
    def setAddress(self, address): #allows user change of addresses
        self.address = address
    def setDecimal(self, tubeNumber, value):
        if value == True or value == False:
            self.tubeStates[tubeNumber]['dpr'] = value
            self.writeTube(tubeNumber)
    def setSpare(self, tubeNumber, value):
        if value == True or value == False:
            self.tubeStates[tubeNumber]['dpl'] = value
            self.writeTube(tubeNumber)
    def writeTube(self, tubeNumber):
        #print("writng")
        tubeString = str(tubeNumber) + " "
        if(self.tubeStates[tubeNumber]['blink']):
            tubeString = tubeString + "b"
        if(self.tubeStates[tubeNumber]['dpl']):
            tubeString = tubeString + "."
        tubeString = tubeString + str(self.tubeStates[tubeNumber]['value']);
        if(self.tubeStates[tubeNumber]['dpr']):
            tubeString = tubeString + "."
        if(self.tubeStates[tubeNumber]['fade']):
            tubeString = tubeString + " 1"
        tubeString = tubeString + "\n";
        #print (tubeString)
        #self.bus.write_i2c_block_data(self.address, 0x00,StringToBytes(tubeString))
        for tubeChar in StringToBytes(tubeString):
            #print(tubeChar)
            try:
                self.bus.write_byte_data(self.address, tubeChar, 0x00)
            except:
                pass
                #print("Warning: IO Error on I2C Bus to Nixie Display")

    def printTube(self, tubeNumber, value): #set the number displayed on an individual tube
        #print("Tube:"+ str(tubeNumber) + "\tOld:" + str(self.tubeStates[tubeNumber]['value']) + "\tNew:"+str(value))
        if self.tubeStates[tubeNumber]['value'] != str(value):
            self.tubeStates[tubeNumber]['value'] = str(value)
            self.writeTube(tubeNumber)
    def printTubes(self, value, blank=True): #set the number displayed across all tubes, highest digits will be ignored
        valStr = str(value)
        valStr = valStr[0:len(self.tubeStates)]
        offset = len(self.tubeStates)-len(valStr)
        numDigits = min(len(self.tubeStates),len(valStr));
        tubeNums = [10,10,10,10,10,10];
        for tubeIdx in range(numDigits):
            tubeNums[offset+tubeIdx] = int(valStr[tubeIdx]);
        for tubeIdx in range(len(self.tubeStates)):
            self.printTube(tubeIdx, tubeNums[tubeIdx]);

    # def printTubes(self, value, blank=0): #set the number displayed across all tubes, highest digits will be ignored
    #     valStr = str(value)
    #     valStr = valStr[0:6]
    #     offset = 6-len(valStr)
    #     for tubeIdx in range(min(len(self.tubeStates),len(valStr))):
    #         self.printTube(offset+tubeIdx, valStr[tubeIdx])

    def dimTube(self, tubeNumber, percent): #set brightness of an individual tube
        return -1 #not implemented
    def dimTubes(self, percent): #set brightness of all tubes
        return -1 #not implemented
    def startBlinking(self, tubeNumber):
        self.tubeStates[tubeNumber]['blink'] = True
        self.writeTube(tubeNumber)
    def stopBlinking(self, tubeNumber):
        self.tubeStates[tubeNumber]['blink'] = False
        self.writeTube(tubeNumber)
    def stopAllBlinking(self):
        for tubeIdx in range(len(self.tubeStates)):
            self.stopBlinking(tubeIdx)
    def setFade(self,tubeNumber, value):
        if value == True or value == False:
            self.tubeStates[tubeNumber]['fade'] = value
    def setAllFade(self,value):
        for tubeIdx in range(len(self.tubeStates)):
            self.setFade(tubeIdx, value)
    def updateNow(self, fade=False):
        for tubeIdx in range(len(self.tubeStates)):
            tempFade = self.tubeStates[tubeIdx]['fade']; #force obey fade flag
            self.tubeStates[tubeIdx]['fade'] = fade;
            self.writeTube(tubeIdx);
            self.tubeStates[tubeIdx]['fade'] = tempFade;
    def colons(self, onOff):
            self.setDecimal(2, onOff);
            self.setSpare(2, onOff);
            self.setDecimal(4, onOff);
            self.setSpare(4, onOff);
