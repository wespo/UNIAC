#!/usr/bin/python
import mpd
import smartNixie
import time

# use_unicode will enable the utf-8 mode for python2
# see http://pythonhosted.org/python-mpd2/topics/advanced.html#unicode-handling
client = mpd.MPDClient(use_unicode=True)
client.connect("localhost", 6600)

if client.status()['playlistlength'] == '0':
    client.load('Fallout: New Vegas (by tardskii)')
if client.status()['state'] <> 'play':
    client.play()
    print "Play"
nixie = smartNixie.Nixie()
nixie.dimTubes(75)
##for entry in client.lsinfo("/"):
##    print("%s" % entry)
for key, value in client.status().items():
    print("%s: %s" % (key, value))
while True:
    timeNum = int(time.time())
    [elapsedSeconds, totalSeconds] = client.status()['time'].split(':')
    elapsedSeconds = int(elapsedSeconds)
    totalSeconds = int(totalSeconds)
##    remainingSeconds = totalSeconds - elapsedSeconds
    displaySeconds = elapsedSeconds
    displayMinutes = int(displaySeconds/60)
    modSeconds = displaySeconds%60
    displayTime = displayMinutes*100 + modSeconds
    nixie.printTubes(displayTime, 2)  
    while int(time.time()) == timeNum:
        time.sleep(0.1)
