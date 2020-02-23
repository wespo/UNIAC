from MPDClientBlocking import MPDClientBlocking

#start connections to Mopidy
controlClient = MPDClientBlocking()
statusClient = MPDClientBlocking()
displayClient = MPDClientBlocking()

class mpdGeneral: #general purpose class for MPD interfaces
    blocked = False;
    # def isConnected(self): #method to reconnect to the client if need be
    #     try:
    #         controlClient.ping()
    #     except (mpd.MPDError, mpd.ConnectionError, IOError):
    #         print 'MPD Connection Error.'
    #         print 'Reconnecting to MPD service.'
    #         try:
    #             controlClient.connect("localhost", 6600)
    #             return True
    #         except:
    #             print "Reconnect failed"
    #             return False
    #
    #     except:
    #         "Other error, go fuck yourself"
    #         return False
    def playStatus(self):
        return statusClient.playStatus()
    def canonicalPlayStatus(self):
        return statusClient.playStatus()
    def playPause(self, direction):
        if direction == -1:
            return self.pause(-1)
        else:
            return -1
    def play(self, direction):
        if direction == -1:
            return controlClient.play()
        else:
            return -1
    def pause(self, direction, pauseIfPlaying=False):
        if direction == -1:
            return controlClient.pause()
        else:
            return -1
    def nextTrack(self, direction):
        if direction == -1:
            return controlClient.next()
        else:
            return -1
    def previousTrack(self, direction):
        if direction == -1:
            return controlClient.previous()
        else:
            return -1
    def clearPlaylist(self):
        if direction == -1:
            return controlClient.clear()
        else:
            return -1
    def getPlaylists(self):
        lists = statusClient.listplaylists()
        print "# Playlists found:" + str(len(lists))
        return lists
    def loadPlaylist(self, playlist):
        return controlClient.loadPlaylist(playlist)
    def clientTime(self):
        return displayClient.clientTime()
    def setRandom(self, value): #-1 to toggle
        return controlClient.setParam('random',value)
    def getRandom(self):
        return statusClient.getParam('random') #current value
    def setRepeat(self, value): #-1 to toggle
        return controlClient.setParam('repeat', value)
    def getRepeat(self):
        return statusClient.getParam('repeat') #current value
