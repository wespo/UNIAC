import smartNixie
import time

nixie = smartNixie.Nixie()
#Write a single register
print 'Running Nixie Clock'

timeNum = int(time.strftime('%I%M%S'))
nixie.printTubes(timeNum)    
for percent in range(0,31):
    nixie.dimTubes(percent)
    time.sleep(0.1)

while True:
    timeNum = int(time.strftime('%I%M%S'))
    nixie.printTubes(timeNum)    
    while int(time.strftime('%I%M%S')) == timeNum:
        time.sleep(0.1)
