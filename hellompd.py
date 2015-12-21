#!/usr/bin/python
import mpd
import smartNixie
import time

# use_unicode will enable the utf-8 mode for python2
# see http://pythonhosted.org/python-mpd2/topics/advanced.html#unicode-handling
client = mpd.MPDClient(use_unicode=True)
client.connect("localhost", 6600)

nixie = smartNixie.Nixie()

##for entry in client.lsinfo("/"):
##    print("%s" % entry)
##for key, value in client.status().items():
##    print("%s: %s" % (key, value))
while True:
    timeNum = int(time.time())
    elapsedSeconds = int(client.status()['time'].split(':')[0])
    elapsedMinutes = int(elapsedSeconds/60)
    modSeconds = elapsedSeconds%60
    elapsedTime = elapsedMinutes*100 + modSeconds
    nixie.printTubes(elapsedTime)    
    while int(time.time()) == timeNum:
        time.sleep(0.1)
