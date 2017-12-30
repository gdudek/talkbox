#!/usr/bin/python 
# /* vim: set tabstop=8 softtabstop=8 shiftwidth=8 noexpandtab : */

import RPi.GPIO as GPIO
import time
import soundOfTheDay
import sys,os
import signal
import traceback, subprocess

REQUESTINTERVAL = 7*60*60 #10 min    # how often to make a recurring noise if we have been abandoned for a long time: 7*60*60 = 7 hours
LONGTIME        = 15*24*(60*60)      # how long in seconds coulds a a long time since we were opened: 5*24*(60*60)= 5 days
STAY_ON_DELAY   = 300                # how long to light button when getting attention
debug = 0
lastOpenTime = time.time()           # last time open was opened or red button pressed

if len(sys.argv)>1 and sys.argv[1]=="-d": debug=1
if debug>=2:
    REQUESTINTERVAL = 1*60  # 5 min  # recurring
    LONGTIME        = 4*60 # 10 min
    STAY_ON_DELAY   = 35
if debug:
    print "Debugging level",debug
    print "LONGTIME:",LONGTIME," = ",LONGTIME/60/60.,"hours","or",LONGTIME/60,"minutes"

lidPin = 17 # Broadcom pin 17 (P1 pin 11)
vibroPin = 27 
#
redButtonIn  = 23
redButtonLED = 25
#
dmitriyButtonLED = 24 
dmitriyButtonPin = 6 

soundOfTheDay.nclicks = { 'lid':0, 'red':0, 'dmitriy': 0, 'vibroPin': 0 }

# Can disable some sensors if they are too annoying.
# Currenly not implemented for buttons
# Use:
#   soundOfTheDay.disabledSensors.append("lid")


from collections import defaultdict
nowHandlingCallback = defaultdict(lambda: 0)  # disctionary of callbacks to ignore

lightButtonWhileSoundPlaying = 0

flashMode = 0


def ssid():
    status = subprocess.Popen("iw wlan0 info|grep ssid 2>&1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    time.sleep(1.4)
    status = status.read().strip()
    if debug>1: print "Status:",status
    if not status or ("not found" in status):
        sys.exit(1)
    return status.split(" ")[-1]


def turnOnhandler(signum, frame):
    """ Turn on red LED and schedule subsequent turnoff """
    GPIO.output(redButtonLED,GPIO.HIGH)
    signal.signal(signal.SIGALRM,  turnOffhandler )
    signal.alarm(2)

def turnOffhandler(signum, frame):
    """ Turn of LED's """
    global lastOpenTime
    global flashMode
    allLEDsOff()
    if flashMode:
            signal.signal(signal.SIGALRM,  turnOnhandler )
            signal.alarm(2)

def allLEDsOff():
    " Turn off all LED's "
    GPIO.output(redButtonLED,GPIO.LOW)
    GPIO.output(dmitriyButtonLED,GPIO.LOW)

def got_gpio_interrupt(channel):  
    global vibroPin
    global nowHandlingCallback
    #GPIO.remove_event_detect(channel)
    if nowHandlingCallback[channel]: return
    nowHandlingCallback[channel]=1
    if debug: 
        print "Got GPIO interrupt on pin",channel,
        # get name of pin
        print list({k for (k,v) in globals().items() if v==channel })[0]
    if (channel == vibroPin) and not ('vibroPin' in soundOfTheDay.disabledSensors):
        if debug: print "Vibration detected:",GPIO.input(vibroPin)
        soundOfTheDay.playRandomSpecialFileClass("motion")
        soundOfTheDay.nclicks['vibroPin'] += 1
    #GPIO.add_event_detect(channel, GPIO.FALLING, callback=got_gpio_interrupt, bouncetime=700)
    if debug: print "Handler finished"
    callbacksToReenable.append(channel)


def got_button_interrupt(channel):  
    global redButtonIn,dmitriyButtonPin,redButtonLED,dmitriyButtonLED
    global nowHandlingCallback
    global lastOpenTime
    global lightButtonWhileSoundPlaying
    global flashMode
    if debug: print "nowHandlingCallback:",nowHandlingCallback
    if nowHandlingCallback[channel]:
        if debug: print "discarding nested call on",channel
        return
    nowHandlingCallback[channel]=1
    #BUGGY: GPIO.remove_event_detect(channel)
    if debug: 
        print "Got GPIO interrupt on pin",channel,
        # get name of pin
        print list({k for (k,v) in globals().items() if v==channel })[0]
    if channel == redButtonIn:
        if lightButtonWhileSoundPlaying: 
            if debug: print "Lighting up red LED"
            GPIO.output(redButtonLED,GPIO.HIGH)
        soundOfTheDay.nclicks['red'] += 1
        soundOfTheDay.playToday( specialCount=soundOfTheDay.nclicks['red'] )

        lastOpenTime = time.time()
        flashMode=0

        if debug: print time.ctime()
        if debug: print "Returned from playToday()"
        if lightButtonWhileSoundPlaying: GPIO.output(redButtonLED,GPIO.LOW)
        if soundOfTheDay.nclicks['red']==300:
                soundOfTheDay.playSpecialFile("unlocked.mp3")
        if soundOfTheDay.nclicks['red']>=300:
            lightButtonWhileSoundPlaying = 1
        while GPIO.input(redButtonIn)==0:
            if GPIO.input(dmitriyButtonPin)==0:
                soundOfTheDay.playSpecialFile("shutdown.mp3")
                soundOfTheDay.cleanup()
                GPIO.cleanup()
                os.system("shutdown -h now")
    if channel == dmitriyButtonPin:
        if lightButtonWhileSoundPlaying: GPIO.output(dmitriyButtonLED,GPIO.HIGH)
        soundOfTheDay.nclicks['dmitriy'] += 1
        soundOfTheDay.playToday( dmitriy=1 )
        if lightButtonWhileSoundPlaying: 
            if debug: print "Turning off red LED"
            GPIO.output(dmitriyButtonLED,GPIO.LOW)
    #BUGGY: GPIO.add_event_detect(channel, GPIO.FALLING, callback=got_button_interrupt, bouncetime=700)
    if debug: print "Handler finished"
    callbacksToReenable.append(channel)

callbacksToReenable = [ ]
def delayedReenableInterrupts():
    """ Reenble callbacks that were temporarily disabled. """
    global callbacksToReenable
    global nowHandlingCallback
    for channel in callbacksToReenable:
        if debug: 
            print "reenable",channel,time.ctime(),
            # get name of pin
            print list({k for (k,v) in globals().items() if v==channel })[0]
        nowHandlingCallback[channel] = 0
    # note there is a risk of an interrupt coming right here, leading to a race condition!
    callbacksToReenable=[]
         

def runmain():
    global REQUESTINTERVAL,LONGTIME
    global lastOpenTime
    global flashMode

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(lidPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Button pin set as input w/ pull-down
    GPIO.setup(vibroPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(redButtonIn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(redButtonLED, GPIO.OUT)
    GPIO.setup(dmitriyButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(dmitriyButtonLED, GPIO.OUT)
    allLEDsOff()

    soundOfTheDay.selfTest(globals())

    soundOfTheDay.setdebug(debug)
    soundOfTheDay.playSpecialFile("imalive.mp3")
    if ( ssid() not in soundOfTheDay.seen_ssid_list ):
        soundOfTheDay.seen_ssid_list.append( ssid() )
        soundOfTheDay.playRandomSpecialFileClass("newplace")

    initialState = GPIO.input(lidPin)
    if debug: print "Initial state of lidPin pin",lidPin,"is",initialState
    if debug: print "Initial state of vibration pin",vibroPin,"is",GPIO.input(vibroPin)

    GPIO.add_event_detect(vibroPin, GPIO.FALLING, callback=got_gpio_interrupt, bouncetime=700)
    GPIO.add_event_detect(redButtonIn, GPIO.FALLING, callback=got_button_interrupt, bouncetime=700)
    GPIO.add_event_detect(dmitriyButtonPin, GPIO.FALLING, callback=got_button_interrupt, bouncetime=700)

    while 1:

        initialState = GPIO.input(lidPin)
        vibroPinState = GPIO.input(vibroPin)

        while GPIO.input(lidPin) == initialState:
            # box is closed or open, in this fixed state
            #if vibroPinState != GPIO.input(vibroPin):
            #    # box vibrated
            #    if debug: print "Vibration detected:",GPIO.input(vibroPin)
            #    soundOfTheDay.playRandomSpecialFileClass("motion")
            #    # soundOfTheDay.playToday( )
       
            now = time.time()
            # box closed
            if (GPIO.input(lidPin) == 1) and \
                (now - lastOpenTime)>LONGTIME and (int(now) % REQUESTINTERVAL==0):
                    if debug: 
                        print "Requesting attention since unopened for",(now - lastOpenTime)/60,"minutes","mod:",int(now)%REQUESTINTERVAL
                    # request attention
                    GPIO.remove_event_detect(vibroPin)
                    # light up that inviting red button
                    GPIO.output(redButtonLED,GPIO.HIGH)

                    if (now - lastOpenTime)>2*LONGTIME:
                        if debug: print "Delay so long that flash mode is",flashMode
                        flashMode=1
                    # turn off the button in a while if nobody pays attention
                    signal.alarm(STAY_ON_DELAY)


                    soundOfTheDay.playRandomSpecialFileClass("attention")
                    GPIO.add_event_detect(vibroPin, GPIO.FALLING, callback=got_gpio_interrupt, bouncetime=700)
                    time.sleep(2)  # make sure we are outside the request interval to avoid repeat triggers in the same second
                    if debug: print "Attention request done."
            time.sleep(0.2) # CPU generosity
            delayedReenableInterrupts()

        if (GPIO.input(lidPin) == 0) and not ('lid' in soundOfTheDay.disabledSensors): # box open
                if debug: print "lid is open"
                if debug: print time.ctime()
                GPIO.remove_event_detect(vibroPin)
                soundOfTheDay.nclicks['lid'] += 1
                soundOfTheDay.playToday( )
                lastOpenTime = time.time()
		flashMode=0

        # while box remains open
        n = 1
        while (GPIO.input(lidPin) == 0) and  not ('lid' in soundOfTheDay.disabledSensors):
            if debug: print "lid is still open"
            if debug and (n%10)==0: print "open time",n
            time.sleep(1)
            n = n+1
            if n%60 == 0:   # been open a long time!
                GPIO.remove_event_detect(vibroPin)
                soundOfTheDay.playSpecialFile("closeit.mp3")
                n = 0
            delayedReenableInterrupts()
        try:
           GPIO.add_event_detect(vibroPin, GPIO.FALLING, callback=got_gpio_interrupt, bouncetime=700)
        except RuntimeError: pass

def clickRed(signum, frame):
    """ Same effect as clicking red button. """
    soundOfTheDay.playToday( )

def checkpoint(signum, frame):
    """ Save status to file(s) and server. """
    import urllib2
    s = "http://www.dudek.org/talkboxstats?"
    soundOfTheDay.saveState()
    for i in soundOfTheDay.nclicks:
       s = s+str(i)+"="+str(soundOfTheDay.nclicks[i])+"&"
    if debug: print s
    try:
        f = urllib2.urlopen(s, None, 3)
        xml = f.read()
        f.close()
    except urllib2.HTTPError: pass
    except urllib2.URLError: pass
    except:
       print traceback.format_exc()

def mainloop():
    try: 
        print "Mainloop"
        signal.signal(signal.SIGALRM,  turnOffhandler )
        signal.signal(signal.SIGUSR1, checkpoint )
        signal.signal(signal.SIGUSR2, clickRed )
        runmain()
    except KeyboardInterrupt:
       print "Bye."
    except:
       print traceback.print_exc()
       if sys.__dict__.has_key("last_value"): 
           soundOfTheDay.foundError = sys.last_value
       else:
           soundOfTheDay.foundError = time.ctime()+" "+str(traceback.format_tb( sys.exc_info()[2] ))
    finally:
       print "sys.exc_info()",sys.exc_info()
       soundOfTheDay.cleanup()
       if debug: print "\nGPIO cleanup"
       GPIO.cleanup()
    
while 1:
    print "Starting talkbox", soundOfTheDay.versionNumber
    mainloop()
    time.sleep(60) # don't restart for a minute. Give time for double control-C and avoid overheating
