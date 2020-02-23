import nixieDisplay
import time

import sys

nixie = nixieDisplay.Nixie()
#Write a single register
print 'Running Nixie Clock'

nixie.setDecimal(2,True)
nixie.setSpare(2,True)
nixie.setDecimal(4,True)
nixie.setSpare(4,True)

if(len(sys.argv) > 1):
    if(sys.argv[1] == "True"):
        nixie.setAllFade(True)

while True:
    timeNum = int(time.strftime('%I%M%S'))
    if int(time.strftime('%H')) > 11:
        nixie.setSpare(1,True)
    else:
        nixie.setSpare(1,False)
    #print("printing:")
    nixie.printTubes(timeNum)
    if int(time.strftime('%I')) < 10:
        nixie.printTube(0,10)
    while int(time.strftime('%I%M%S')) == timeNum:
        time.sleep(0.1)
