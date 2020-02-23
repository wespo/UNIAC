import mpd
import time
import multiprocessing

class MPDClientBlocking():
    def __init__(self):
        ## multiprocessing variables

        ## MPD Variables
        self.busy = True;
        self.client = mpd.MPDClient(use_unicode=True)
        self.autoConnectLocal()
        self.busy = False
        self.internalPlayStatus = False
        self.playStatusCount = 0
        self.lastStatus = {}
        self.statusTime = time.time()
    def autoConnectLocal(self):
        startupTimeout = 30
        print "Attempting to connect to MPD Daemon. Process will time out after " + str(startupTimeout) + " seconds."
        t = time.time() + startupTimeout #wait up to two minutes for mopidy to start.
        while time.time()<t:
            try:
                self.connect()
                print "Connected Successfully"
                break
            except:
                pass
        # print "connecting to Mopidy..."
        # retry_count = 1
        # x = multiprocessing.Process(target=self.connect)
        # while retry_count < 20:
        #     x.start()
        #     time.sleep(2.5)
        #     x.join(15)
        #     if x.is_alive():
        #         print "attempt #" + str(retry_count) + " failed. Retrying."
        #         x.terminate()
        #         time.sleep(2.5)
        #     else:
        #         print "connected."
        #         return True
        #     retry_count = retry_count + 1
        print "max retries reached, connection failed."
        return False
    def storeStatus(self, status):
        self.lastStatus = status
        self.statusTime = time.time()

    def connect(self):
        self.client.connect("localhost", 6600)

    def keepAlive(self):
        if self.busy == True:
            return False
        self.busy = True
        success = self.unsafeKeepAlive()
        self.busy = False
        return success
    def unsafeKeepAlive(self):
        success = False
        try:
            self.client.ping()
            success = True
        except (mpd.MPDError, mpd.ConnectionError, IOError):
            print 'MPD Connection Error.'
            print 'Reconnecting to MPD service.'
            try:
                self.client.connect("localhost", 6600)
                success = True
                print "Reconnected successfully"
            except:
                print "Reconnect failed"
        except:
            print "Other error, go fuck yourself"
        return success
    def safeClient(self, method):
        try:
            currentStatus = method()
        except mpd.base.ConnectionError:
            self.connect()
            currentStatus = method()
        return currentStatus
    def playStatus(self):
        # #only check playStatus occcassionally
        # if self.playStatusCount > 20:
        #     self.playStatusCount = 0
        # else:
        #     self.playStatusCount += 1
        #     return self.internalPlayStatus
        if self.busy == True:
            print("playStatus: Busy")
            return -1
        else:
            self.busy = True
        currentStatus = self.safeClient(self.client.status)
        #print(currentStatus)
        errCount = 0
        while 'state' not in currentStatus:
            print "playStatus: check error. Rechecking status"
            print currentStatus
            currentStatus = self.client.status()
            print "playStatus: status checked"
            print currentStatus
            errCount += 1
            if errCount > 20:
                break;
        if currentStatus['state'] == 'play':
            self.internalPlayStatus = True
        else:
            self.internalPlayStatus = False
        self.busy = False
        self.storeStatus(currentStatus)
        return int(self.internalPlayStatus)

    def play(self):
        if self.busy == True:
            print("play: Busy")
            return -1
        else:
            self.busy = True
        self.safeClient(self.client.play)
        self.internalPlayStatus = True
        self.busy = False
    def pause(self):
        if self.busy == True:
            print("pause: Busy")
            return -1
        else:
            self.busy = True
        self.safeClient(self.client.pause)
        self.busy = False

    def next(self):
        if self.busy == True:
            print("next: Busy")
            return -1
        else:
            self.busy = True
        self.safeClient(self.client.next)
        self.busy = False

    def previous(self):
        if self.busy == True:
            print("previous: Busy")
            return -1
        else:
            self.busy = True
        self.safeClient(self.client.previous)
        self.busy = False

    def clear(self):
        if self.busy == True:
            print("clear: Busy")
            return -1
        else:
            self.busy = True
        self.safeClient(self.client.clear)
        self.busy = False

    def getPlaylists(self):
        busyCount = 0;
        while self.busy == True:
            print("getPlaylists: Busy")
            time.sleep(0.25)
            busyCount += 1
            if busyCount > 20:
                self.busy = False
                return [{}]

        lists = [{}]
        errCount = 0
        while lists[0].has_key('playlist') == False:
            lists = self.safeClient(self.client.listplaylists)
            errCount += 1
            if errCount > 20:
                self.busy = False
                return [{}]
        return lists
    def loadPlaylist(self, playlist):
        if self.busy == True:
            print("loadPlaylist: Busy")
            return False
        else:
            self.busy = True
        loadCount = 0
        while loadCount < 10:
            self.client.load(playlist)
            loadCount = loadCount + 1
        self.busy = False
        return True

    def clientTime(self):
        deltaT = time.time() - self.statusTime
        if(deltaT < 0.25): #no need to update
            return self.lastStatus['time'].split(':')
        if self.busy == True:
            print("clientTime: Busy")
            return [0,0]
        else:
            self.busy = True
        currentStatus = self.safeClient(self.client.status)
        self.storeStatus(currentStatus)
        errCount = 0
        while 'time' not in currentStatus:
            print("Time not found. Checking again.")
            currentStatus = self.client.status()
            errCount += 1
            if errCount > 10:
                print("Did not find time, aborting.")
                self.busy = False
                return [0,0]
        self.busy = False
        self.storeStatus(currentStatus)
        return currentStatus['time'].split(':')

    def setParam(self, param, value): #-1 to toggle
        if self.busy == True:
            print("getParam: Busy")
            return -1
        else:
            self.busy = True
        currentStatus = self.safeClient(self.client.status)
        errCount = 0
        while param not in currentStatus:
            currentStatus = self.client.status()
            errCount += 1
            if errCount > 10:
                self.busy = False
                return -1

        paramMethod = getattr(self.client, param)
        paramMethod(value)
        self.busy = False
        return int(currentStatus[param]) #current value

    def getParam(self, param):
        if self.busy == True:
            print("getParam: Busy")
            return -1
        else:
            self.busy = True
        currentStatus = self.safeClient(self.client.status)
        errCount = 0
        while param not in currentStatus:
            currentStatus = self.client.status()
            errCount += 1
            if errCount > 10:
                self.busy = False
                return -1
        self.busy = False
        self.storeStatus(currentStatus)
        return int(currentStatus[param]) #current value
