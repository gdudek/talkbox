#
# print the sound of the day
#


import time
import sys, os
import subprocess
import glob
import pickle
import random

if sys.platform=="darwin": player="play"
else: player="mpc"  # mpd/mpc is a heavier solution than mpg123, but can avoid the clicks a bit better.

versionNumber = 1.7
debug = 0  #  0,1,2  bigger is more verbose
silent = 0
#SOUNDDIR="/Users/dudek/Code/HelloSounds/"
SOUNDDIR="/home/pi/Hello/"
SOUNDDIR=""
required_executables=[player,"lsof -h","sox --version","killall -V"]
timesPlayed = { }
gaveRepetitionWarning = [0,0,0,0]   # only once ever, give a warning about multiple door-openings

savelist = [ "timesPlayed", "checkLast", "lastWriteTime", "lastPlayTime", "nclicks", "gaveRepetitionWarning", "__foundError","lastFilePlayed", "__startupTime", "disabledSensors", "outFlavor", "__debug", "firsttime", "seen_ssid_list" ] # leading __ means save but don't reload

executionsThisLoad = 0 # how many times have we been called, used for disk IO strategy
lastWriteTime = 0      # last time state file was written to disk
# output flavors
outFlavor = ["natasha", "dmitriy", "attention", "misc" ]
lastFilePlayed = [None]*len(outFlavor)  # last file played for selected type
lastPlayTime = [0]*len(outFlavor)       # time last file was played of selected type
nclicks={} # needs to be loaded from calling module
foundError = ""
firsttime = 1
startupTime = time.time()
disabledSensors =  [ ]
seen_ssid_list = [ ]



def programIsRunning(program):
    """ Check if piano bar process is alive. """
    status = subprocess.Popen("lsof -n -P -c mopidy|grep -v grep|grep "+program, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
    print(status)
    return ( len(status)>1 )

def cleanup():
    """ We are about to close down. """
    global lastWriteTime
    lastWriteTime = time.time()
    saveState( "playerState" )


def selfTest( sysglob={} ):
    """ make sure everything is OK to run. """

    global required_executables
    global nclicks
    if not required_executables: return

    mp3files = glob.glob(SOUNDDIR+"[0-9].mp3")
    if not mp3files:
         print("** No playable mp3 files in",SOUNDDIR,"**")
         sys.exit(2)
    for i in required_executables:
        if debug: print("looking for:",i.split()[0])
        status = subprocess.Popen(i+"< /dev/null 2>&1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        time.sleep(0.1)
        status = status.read().strip()
        if debug>1: print("Status:",status)
        if not status or ("not found" in status):
            print("ERROR: required program",i.split()[0],"not runnable")
            sys.exit(1)
        if debug: print("found: required program",i.split()[0])
    required_executables = None  # release the storage since we only need to check once.
    if debug: print("Selftest done.",nclicks)
     


def saveState(saveStateFile="playerState"):
    """ Save a bunch of global variables in a pickle, for faster restarting.
        We have a list of variable sof interest, but start and end with check-variables with the
        values "first" and "last".
    """
    if debug: print ("Saving state")
    output = open(saveStateFile, 'wb')
    checkFirst = "first"
    checkLast = "last"

    if savelist[-1]!="checkLast": savelist.append("checkLast")
    
    if debug: print("  pickle,checkFirst")
    pickle.dump(eval("checkFirst"), output)
    if debug: print("  pickle,versionNumber")
    pickle.dump(eval("versionNumber"), output)
    if debug: print("  pickle,SAVELIST++")
    pickle.dump( ["checkFirst","versionNumber","savelist",] + savelist, output) # save list of what else we are saving
    
    for i in savelist:
        if i[0:2]=="__":
            realVar = i[2:]  # leading __ just means don't reload this
            exec( "global "+realVar )
            exec( i +" = "+realVar  )
        else: exec( "global "+i )
        if debug: print(("pickle",i,eval(i)))
        pickle.dump(eval(i), output)
    output.close()
    if debug: print ("Saved state.")
    
def loadState(loadStateFile):
    global nclicks
    if debug: print(("Loading saved state from",loadStateFile))
    savedstate = open(loadStateFile, 'rb')
    first = pickle.load(savedstate)
    if first != "first":
        print("*** SAVE FILE ERROR ***")
    savedVersion = pickle.load(savedstate) # we can do version-dependent loading
    if debug: print(("savedVersion is",savedVersion))
    if (versionNumber!=savedVersion): 
        print("*"*40)
        print ("State file version mismatch. Prepare for disaster.")
        print("You should probably delete",loadStateFile,"and restart from scratch.")
        print("*"*40)

    loadlist = pickle.load(savedstate)
    if debug: print(("loading",loadlist))

    for i in loadlist[3:]:
        # leading asterisk means don't load this variable
        if debug and i[0:2]=="__":   print("VARIABLE",i,"NOT LOADABLE")
        if debug: print(("loading",i), end=' ')
        exec( "global "+i )
        try: globals()[i] = pickle.load(savedstate)
        except: print("Error loading",i)
        if debug: print(globals()[i])
    if (first != "first") or (checkLast != "last"):
        print(("*** ERROR: load from pickle was bad (checksum failure) ***", first,last))
        # sys.exit(1) 

def setdebug(state):
    global debug
    debug = state

### Main ############
#####################

def playit(fileToPlay):
    """ Play a file. Use the mpd daemon to reduce the clicky-poppy sounds from turnign audio on and off.
        Otherwise mpg123 would be a cleaner solution.
    """
    global silent
    if silent: return
    if player=="mpc":
        os.system("mpc -q consume on;mpc -q clear;mpc -q add "+fileToPlay +";mpc -q play")
        status = "unknown"
        while len(status)>1:
            status = subprocess.Popen("mpc current", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().strip()
            if debug>1: print("mpd playing:",str(status))
    else:
        os.system(player+" -q "+fileToPlay +" </dev/null ")
    
    

def playRandomSpecialFileClass(fileFamily):
    """  Play a randomly-selected file with a name that starts with fileFamily
         followed by a numnber or a hyphen and a number, e.g. foo-21
         Return 0 if no file could be found and played.
    """
    try:
        # find a label for this kind of file
        flavor = outFlavor.index(fileFamily)
    except:
        print("Adding new flavor:",fileFamily)
        outFlavor.append(fileFamily)
        flavor = outFlavor.index(fileFamily)

    mp3files = glob.glob(SOUNDDIR+fileFamily+"[0-9].mp3")
    mp3files = glob.glob(SOUNDDIR+fileFamily+"-*.mp3")
    if not mp3files: return 0

    fileToPlay = random.choice( mp3files )
    try:
        lastPlayTime[flavor]   = time.time()
        lastFilePlayed[flavor] = fileToPlay 
    except:
        lastPlayTime.append( time.time() )
        lastFilePlayed.append( fileToPlay )
    return playSpecialFile(fileToPlay)


def playSpecialFile(fileToPlay):
    """ Play the sound from a specific file.
        Return 0 (false) if no such file could be found, else return 1.
    """
    global lastWriteTime
    try:  
        if not timesPlayed: 
            loadState( "playerState" )
    except IOError: print("No saved state file")

    if os.access( fileToPlay, 0 ):
        if debug: print("play ",fileToPlay)
    else:
        print("Cannot play",fileToPlay,"not found or not readable.")
        return 0

    #  PLAY THE SELECTED FILE:  fileToPlay
    if debug: print("PLAYING:",fileToPlay)
    if not silent:
        playit(fileToPlay)
    else:
        print(fileToPlay,"artificially silenced.")
    if fileToPlay in timesPlayed: 
            timesPlayed[fileToPlay] += 1
    else:
            timesPlayed[fileToPlay] = 1
    lastWriteTime = time.time()
    saveState( "playerState" )
    return 1



def playToday(date=None, dmitriy=None, specialCount=0 ):  # can accept datetime.date(2007,12,5)
    """ Play sound of the day. If dmitriy==1 then use dmitriy-sound.
        specialCount is the number of clicks to date, some of which trigger and announcement.
    """

    global lastWriteTime, lastPlayTime, lastFilePlayed
    global gaveRepetitionWarning,firsttime, executionsThisLoad

    if dmitriy: flavor = outFlavor.index("dmitriy")
    else: flavor=outFlavor.index("natasha")  # default, for Natasha
    fileToPlay = None
    freshFileToPlay = 1

    if debug: print('playToday start, gaveRepetitionWarning',gaveRepetitionWarning)

    try:  
        if not timesPlayed: 
            loadState( "playerState" )
    except IOError: 
        print("No saved state file")
    if firsttime:
        fileToPlay = "startup.mp3"
        firsttime=0
        playit(fileToPlay)
        lastWriteTime = time.time()
        saveState( "playerState" )
        return

    if len(sys.argv)>1: 
        todayString = sys.argv[1]
        today = sys.argv[1]
        print("Spoofed date to be ",todayString)
    elif date:
        todayString = date.strftime("%b-%d")
        today = date.strftime("%m-%d")
    else:
        todayString = time.strftime("%b-%d")  # e.g.  Jan-01
        today = time.strftime("%m-%d")  # e.g.  Jan-01

    if debug: print("Today is",today)
    if debug: print("dmitriy",dmitriy)

    todayfile = SOUNDDIR+today+".mp3"
    todayStringfile = SOUNDDIR+todayString+".mp3"
    if debug: print("Look for",todayfile,"or",todayStringfile)

    if (time.time()-lastPlayTime[flavor] < 300) and lastFilePlayed[flavor]:  # sounds stick for 5 minutes to avoid running through them too fast
        if gaveRepetitionWarning[flavor] == 0:
            fileToPlay = "takeiteasy.mp3"
            gaveRepetitionWarning[flavor] = 1
            freshFileToPlay = 0
        else:
            fileToPlay = lastFilePlayed[flavor]
            if fileToPlay == "takeiteasy.mp3":
                fileToPlay=None
            else:
                freshFileToPlay = 0
    else:
        if os.access( todayfile, 0 ):
            if debug: print("play ",todayfile)
            fileToPlay = todayfile
        elif os.access( todayStringfile, 0 ): 
            if debug: print("play ",todayStringfile)
            fileToPlay = todayStringfile
        else:
            print("NO special FILE FOR",today)


    if os.access( "click-"+str(specialCount)+".mp3", 0 ):
        fileToPlay = "click-"+str(specialCount)+".mp3"

    if todayString == "Jan-01": # Krys's birthday
        pass
    if todayString == "Feb-24": # Krys's birthday
        pass
    if todayString == "Aug-04": # Nick's birthday
        pass
    if todayString == "Sep-07": # Natasha's birthday
        fileToPlay = SOUNDDIR+random.choice(["sto_lat_stolat_natasha.mp3","I_feel_good_clip.mp3"])
        print("Natasha's birthday chose:",fileToPlay)
   
    if todayString == "10-31": # Gregory's birthday
        fileToPlay = SOUNDDIR+random.choice(["10-31.mp3","10-31-werewolves.mp3"])
    if todayString == "Oct-11": # Gregory's birthday
        pass
    if todayString == "Jul-01": # Canada day
        pass
    if todayString == "Jul-04": # US Independence day
        pass
    if todayString == "Dec-24": # US Independence day
        pass
    if todayString == "Dec-25": # US Independence day
        pass
    if todayString == "Dec-31": # US Independence day
        pass


    if not fileToPlay or not os.access( fileToPlay, 0 ):
            # No special file. Pick a random greeting.
            if dmitriy==1: dmitriy="dr-"
            else: dmitriy=""
            mp3files = glob.glob(SOUNDDIR+dmitriy+"[0-9].mp3")
            mp3files = mp3files+glob.glob(SOUNDDIR+dmitriy+"[0-9][0-9].mp3")
            mp3files = mp3files+glob.glob(SOUNDDIR+dmitriy+"[0-9][0-9][0-9].mp3")
            if debug>1: print("mp3files:",mp3files)

            # assure all files are in the the dict (not really needed since handled later on)
            for i in mp3files:
                if i not in list(timesPlayed.keys()): timesPlayed[i]=0
            if debug>1: print("timesPlayed","-".join([ str(x) for x in list(timesPlayed.values()) ]))

            eligible = {k:v for (k,v) in list(timesPlayed.items()) if k in mp3files}
            if debug: print("Eligible:",eligible)
            # find one item with smallest number of plays
            minitem = min(eligible, key=eligible.get)

            # now find all other items with same play count and pick one at random
            mindict = {k:v for (k,v) in list(eligible.items()) if v == eligible[minitem] }
            if debug: print("Least played items:", mindict)

            # now select one at random from the obscure items
            fileToPlay = random.choice( list(mindict.keys()) )
              
            if debug>2: print(fileToPlay, timesPlayed[fileToPlay])

    #  PLAY THE SELECTED FILE:  fileToPlay
    if debug: print("PLAYING:",fileToPlay)
    if not silent:
        playit(fileToPlay)
    else:
        print(fileToPlay,"artificially silenced.")
    lastPlayTime[flavor]   = time.time()
    lastFilePlayed[flavor] = fileToPlay 

    if fileToPlay in timesPlayed: 
            timesPlayed[fileToPlay] += 1
    else:
            timesPlayed[fileToPlay] = 1

    # Only write to save file at most once per five minutes, and also
    # after every 5th play.
    #
    executionsThisLoad += 1
    if freshFileToPlay and (executionsThisLoad<8 or (executionsThisLoad%5 ==0)) and ((time.time()-lastWriteTime)>5*60):
        # write to disk less often to save the Flash
        lastWriteTime = time.time()
        saveState( "playerState" )
    else:
        if debug: print("Write to disk omitted to save the SD card.")


if __name__ == '__main__':
    import datetime
    debug = 2
    silent = 1
    
    selfTest()
    print("TODAY")
    playToday( )
    print("TEST DAYS")
    playToday( datetime.date(2007,7,1) )
    playToday( datetime.date(2007,7,4) )
    playToday( datetime.date(2007,8,4) )
    playToday( datetime.date(2007,9,7) )
    playToday( datetime.date(2007,9,7) )
    playToday( datetime.date(2007,9,7) )

