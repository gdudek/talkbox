"""
   Allow settings to be adjusted via web interface.
"""

import sys,os
import subprocess
import soundOfTheDay
import time,signal

def webSettings(httplistener):
    # write preliminary HTTP headers
    #httplistener.write("HTTP/1.1 200 OK\r\n")
    #httplistener.write("Content-type: text/html\r\n")
    #httplistener.write("Cache-Control: no-cache, max-age=1, must-revalidate, no-store\r\n")
    #httplistener.write("Connection: close\r\n")
    httplistener.write("\r\n")
    httplistener.write("""<html><head><title>Talkbox</title>
        </head><body>""")
    #httplistener.write('radioConnect.py version '+VERSION+'<br/>')
    httplistener.write('<h1><a href="/">Talkbox</a> Settings</h1><div class="messageContainer">')

    # information using command-line functions
    for process in [ \
              [ "Time now", 'date' ], \
              [ "Uptime", 'uptime' ], \
              [ "Users", 'who' ], \
              [ "Hostname", 'hostname' ], \
              [ "Recent", 'last|head -5' ], \
              [ "Time zone for clock", 'cat /etc/timezone' ], \
              [ "OS", 'uname -a;cat /etc/os-release' ], \
              [ "CPU", 'egrep "model|Bogo|Hard|Revis" /proc/cpuinfo|sort|uniq' ], \
              [ "Model", 'cat /proc/device-tree/model' ], \
              [ "Memory", 'vcgencmd get_mem arm && vcgencmd get_mem gpu && free -lh' ], \
              [ "CPU temperature (55C is normal)", 'vcgencmd measure_temp' ], \
              [ "Display", 'tvservice  -s;fbset  -s |grep mode|grep x' ], \
              [ "Networking", "ifconfig|egrep -v 'packets|collisions|bytes'" ],\
              [ "Ping to home", "ping -c1 dudek.org;echo;echo ---;ping -c1 yahoo.com" ],\
              [ "Disk space", 'df -h' ], \
              [ "Music Player Deamon", 'mpc' ], \
              [ "Sound system", "amixer get 'PCM'" ], \
              [ "Receiver", 'lsusb|egrep -v "Standard|Linux|RT5370"' ], \
              ]:
        status = subprocess.Popen( process[1],
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
        if len(status)>1: httplistener.write( '<b>'+process[0]+'</b> '+"<pre>\n"+str(status)+"</pre><br>\n" )

    # a few global variables from this program
    """
    for statevar in [ \
              [ "LCD stay on", lcdAlwaysOn ], \
              [ "Recording", nowrecording ], \
              [ "inUSA", inUSA ], \
              [ "Date", time.ctime() ], \
            ]:
        httplistener.write( '<b>'+statevar[0]+'</b>: '+str(statevar[1])+"<br/>\n")
    httplistener.write("<b>LCD UP/DOWN button favorites</b>:<pre>"+str(favorites)+"</pre><br/>")
    """

def finish(httplistener):
    httplistener.write("\n</body></html>")
    httplistener.close()


signal.signal(signal.SIGUSR1, signal.SIG_IGN )
signal.signal(signal.SIGUSR2, signal.SIG_IGN )
os.system("killall -SIGUSR1 python")  # cause a checkpoint
time.sleep(2)

print("<b>Status of boot process:</b>")
try: print(open("/home/pi/boot-status").read())
except: print("No boot log available (checked for '/home/pi/boot-status')")

print()

webSettings(sys.stdout)
soundOfTheDay.loadState("playerState",)
print("<b>Current state (saved on disk)</b>")
print("<pre>")
for i in soundOfTheDay.savelist+["versionNumber"]:
   t = eval("soundOfTheDay."+i)
   print(str(i)+":", t, end=' ')
   if "Time" in i or "time" in i:
       if type(t) == type([]):
          print("==> [", end=' ')
          for j in t:
              if not j:
                  print("0,", end=' ')
                  continue
              try: print(time.ctime(float(j)),",", end=' ')
              except: pass
          print("]")
       else:
           try: print(" => ",time.ctime(float(t)))
           except: print("")
   else: print("")

print("</pre>")
finish(sys.stdout)

