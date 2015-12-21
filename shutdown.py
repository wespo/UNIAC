import RPi.GPIO as GPIO
import time
import os

shutdown_pin = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(shutdown_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

def Int_shutdown(channel):
        os.system("sudo shutdown -h now")

GPIO.add_event_detect(shutdown_pin, GPIO.FALLING, callback = Int_shutdown, bouncetime=2000)

while 1:
    time.sleep(20)
