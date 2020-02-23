from MCP230XX import MCP230XX as MCP230XX
import time
import RPi.GPIO as IO

i2cAddress = 0x20
intPin = 4
MCP = MCP230XX('MCP23008', i2cAddress, '16bit')
IO.setmode(IO.BCM)
IO.setup(4,IO.IN)
IO.add_event_detect(intPin,IO.RISING,callback=MCP.callbackA)
for pin in range(0,7):
    MCP.set_mode(pin, 'input')
    # MCP.add_interrupt()
MCP.set_mode(7,'output')

MCP.interrupt_options(outputType = 'activehigh', bankControl = 'separate')

MCP.add_interrupt(6, callbackFunctHigh=lambda x:pp('Plus',x))
MCP.add_interrupt(5, callbackFunctHigh=lambda x:pp('Minus',x))
MCP.add_interrupt(4, callbackFunctHigh=lambda x:pp('Mode',x))
MCP.add_interrupt(3, callbackFunctHigh=lambda x:pp('Play',x))
MCP.add_interrupt(2, callbackFunctHigh=lambda x:pp('Select',x))
MCP.add_interrupt(1, callbackFunctHigh=lambda x:pp('Snooze',x))
MCP.add_interrupt(0, callbackFunctHigh=lambda x:pp('Alarm',x))

def pp(name,x):
    print name
    print x

while True:
    # for pin in range(0,7):
    #     print MCP.input(pin),
    # print("")
    MCP.output(7,1);
    time.sleep(0.25);
    MCP.output(7,0);
    time.sleep(0.25);



#
# def printPinCalled(pinNum):
#     print(pinNum)
