import os
import sys

query = {}
if len(sys.argv)>1:
   query = eval(sys.argv[1])

try:
    vol = int(query["vol"][0])
except:
    vol=int( sys.argv[0].split("_")[-1].split(".")[0] )
print("Set vol:",vol)
os.system("amixer set 'PCM' %d%%"%vol)
