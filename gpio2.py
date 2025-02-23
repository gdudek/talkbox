import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)


pin = 17
pin = 27

try: pin = int(sys.argv[1])
except: pass

#GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.setup(25, GPIO.OUT)
print("Initially GPIO.input(%d) ="%pin,GPIO.input(pin))

while 1:
    was = GPIO.input(pin)
    #print "Pin",pin,"is",was
    print(was, end=' ')
    sys.stdout.flush()
    n = 0
    while was == GPIO.input(pin):
       n = n+1
       print("%7d"%n,was,"\r", end=' ')
#       GPIO.output(25,GPIO.LOW)
    print()

    was = GPIO.input(pin)
    #print "Pin",pin,"is",was
    print(was, end=' ')
    sys.stdout.flush()
    n = 0
    while was == GPIO.input(pin):
       n = n+1
       print("%7d"%n,was,"\r", end=' ')
#       GPIO.output(25,GPIO.HIGH)
    print()
