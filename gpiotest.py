import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)


pin = 17
pin = 27

GPIO.setup(pin, GPIO.IN) #pull_up_down=GPIO.PUD_DOWN)
print("Initially GPIO.input(pin) =",GPIO.input(pin), end=' ')

while 1:
  print(GPIO.input(pin), end=' ')
  sys.stdout.flush()
