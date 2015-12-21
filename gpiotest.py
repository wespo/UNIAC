import RPi.GPIO as GPIO

def test(channel):
    if GPIO.input(channel) == False:
        print str(channel)+", Falling!"
    
        
def gpioSetup(pin):
    GPIO.setmode(GPIO.BCM) #GPIO configuration
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=test, bouncetime=50)

gpioSetup(17)
gpioSetup(18)
gpioSetup(27)
gpioSetup(22)
gpioSetup(23)
gpioSetup(24)
gpioSetup(25)
