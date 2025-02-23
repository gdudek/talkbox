This is the code the the helloBox, an artefact that says hello with a different recording each day.

This code resides in /home/pi/Hello

Hold both buttons down for a clean shutdown.

All the stuff from the SoundFiles sub-directory also needs to be 
copied to the current directory (/home/pi/Hello)

The script update.sh can be used to update the box, but doe snot yet understand that
mp3 files are stored o=in a subdirectory

Launched via /etc/rc.local
  webserver.py
  hello.py
