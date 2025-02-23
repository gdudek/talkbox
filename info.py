import os
import sys

query = {}
if len(sys.argv)>1:
   query = eval(sys.argv[1])
try:
    arg = int(query["vol"][0])
except:
    pass
os.system("hcitool scan")
sys.stdout.flush()
print('(echo scan on;sleep 60;echo scan off; echo quit)|bluetoothctl"')
sys.stdout.flush()
os.system("(echo scan on;sleep 60;echo scan off; echo quit)|bluetoothctl")
sys.stdout.flush()
print("WIFI scan")
sys.stdout.flush()
os.system("iw wlan0 scan -u passive|grep SSID|grep -v Extended")
