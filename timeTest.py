import time, sched

s = sched.scheduler(time.time, time.sleep)
def printScheduled():
    print "alarm"

print "Scheduling"
alarm = s.enter(10, 5, printScheduled, ())
print s.queue

s.run()

print "Running"
