import RPi.GPIO as GPIO
import time
import sys

GPIO.setmode(GPIO.BCM)


pin = 17
pin = 25

GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Initially GPIO.input(pin) =",GPIO.input(pin), end=' ')

# now we'll define two threaded callback functions  
# these will run in another thread when our events are detected  
def my_callback(channel):  
    print("falling edge detected on 17"  ,channel)
  
def my_callback2(channel):  
    print("transition edge detected on ",channel,"value=>", GPIO.input(channel))

# when a falling edge is detected on port 17, regardless of whatever   
# else is happening in the program, the function my_callback will be run  
# GPIO.add_event_detect(17, GPIO.FALLING, callback=my_callback, bouncetime=300)  

# when a falling edge is detected on port 23, regardless of whatever   
# else is happening in the program, the function my_callback2 will be run  
# 'bouncetime=300' includes the bounce control written into interrupts2a.py  
GPIO.add_event_detect(pin, GPIO.BOTH, callback=my_callback2, bouncetime=300)  

try:  
  print("Waiting for rising edge on port"  ,pin)
  #GPIO.wait_for_edge(pin, GPIO.BOTH)  
  time.sleep(120)

except KeyboardInterrupt:  
  GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
GPIO.cleanup()     
