import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)

pin = 14

try: pin = int(sys.argv[1])
except: pass

print("Blinking BCM pin",pin)
time.sleep(10)  # in case of emergency, since output can be dangerous
print("Go...")

GPIO.setup(pin, GPIO.OUT)

while 1:
   GPIO.output(pin,GPIO.HIGH)
   time.sleep(1)
   GPIO.output(pin,GPIO.LOW)
   time.sleep(1)
