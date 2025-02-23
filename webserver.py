#
#
# semi-simple DHTML web server.
# Gregory Dudek, 2015.
# WARNING: THIS IS USED BY two projects and symlinked: Voter AND KeynotePowerRemote
#
# file.dtml :   dynamic HTML.
# file.html :   static file (HTML)
# replace  $$$date with actual date.
# replace $$$code[  SOME PYTHON CODE ]$$$ with evaluated material
# replace $$$run[ ... ]$$$end with the results of shell execution
#
# ".cgi", ".py", ".pyh"   -> execute
#  pyh returns HTML (text/html)
# py returns text/plain
#
# .script -> osaxscript  (not tested)
#
my_http_port = 80

VERSION="3.7.1"

DEBUG=1
SUPPORT_WINDOWS=0   # disables dynamic HTML support

import string,cgi,time,os,sys
import urllib.parse 
import traceback
import io
import signal

def noop(sig,frame): pass 
signal.signal(signal.SIGUSR1, noop )

PYTHONVERSION=22    # can be used for jythonc which only supports python 2.2 interface
PYTHONVERSION = int(10*float(sys.version[0:3]))

if PYTHONVERSION >= 26:
    import subprocess  # for CGI
    # debug information to web rowser.
    import cgitb
    cgitb.enable(display=0, logdir="/tmp")
    if DEBUG: print("Will do error logging to /tmp in Python",PYTHONVERSION)
else:
    import popen2
    if DEBUG: print("Using popen2 in Python",PYTHONVERSION)

while len(sys.argv)>1:
    if sys.argv[1]=="-p": 
        my_http_port = int(sys.argv[2])
        del sys.argv[1]
        del sys.argv[1]

print(sys.argv[0],"Version",VERSION,"serving on port",my_http_port)

# Form processing sample code (for fields called "name" and "addr"):
#form = cgi.FieldStorage()
#if not (form.has_key("name") and form.has_key("addr")):
#    print "<H1>Error</H1>"
#    print "Please fill in the name and addr fields."
#    return
#print "<p>name:", form["name"].value


try: import re
except: pass
from http.server import BaseHTTPRequestHandler, HTTPServer
#import pri


_hextochr = dict((('%02x' % i).encode('ascii'), bytes([i])) for i in range(256))


# This allows these modules to be used by dhtml pages
# that are dynamically evaluated in their own protected sandbox environment
# dynamicvars is also used to store variables defined and used within the 
# interpreted pages, and thus allows presistent context.
dynamicvars = { }
if not SUPPORT_WINDOWS:
    exec("import os",dynamicvars)
    exec("import sys",dynamicvars)
    exec("import time",dynamicvars)


def unquote(s):
    """unquote('abc%20def') -> 'abc def'."""
    res = s.split('%')
    for i in range(1, len(res)):
        item = res[i]
        try:
            res[i] = _hextochr[item[:2]] + item[2:]
        except KeyError:
            res[i] = '%' + item
        except UnicodeDecodeError:
            res[i] = chr(int(item[:2], 16)) + item[2:]
    return "".join(res)

def urlparse_qs(url, keep_blank_values=0, strict_parsing=0):
    """Parse a URL query string and return the components as a dictionary.

    Based on the cgi.parse_qs method.This is a utility function provided
    with urlparse so that users need not use cgi module for
    parsing the url query string.

        Arguments:

        url: URL with query string to be parsed

        keep_blank_values: flag indicating whether blank values in
            URL encoded queries should be treated as blank strings.
            A true value indicates that blanks should be retained as
            blank strings.  The default false value indicates that
            blank values are to be ignored and treated as if they were
            not included.

        strict_parsing: flag indicating what to do with parsing errors.
            If false (the default), errors are silently ignored.
            If true, errors raise a ValueError exception.
    """

    scheme, netloc, url, params, querystring, fragment = urllib.parse.urlparse(url)

    pairs = [s2 for s1 in querystring.split('&') for s2 in s1.split(';')]
    query = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = unquote(nv[0].replace('+', ' '))
            value = unquote(nv[1].replace('+', ' '))
            query.append((name, value))

    dict = {}
    for name, value in query:
        if name in dict:
            dict[name].append(value)
        else:
            dict[name] = [value]
    return dict

class webServer(BaseHTTPRequestHandler):
    """ Basic web server very much like SimpleHTTPServer."""
    def log_request(self, resultcode):
        if resultcode != 200: 
            print("Result code", resultcode)
            log_message(str(resultcode))

    def do_GET(self):
        if DEBUG: print("GET Path:",urllib.parse.urlparse(self.path)[2])
        try:
            #print "Self.__dict__:",self.__dict__
            #print "URLPARSE path:",urlparse.urlparse(self.path)[2]

            simple = os.path.basename( urllib.parse.urlparse(self.path)[2] )  # basic file name without directory
            if simple=="": simple="index.html"

            fullpath = "./" + urllib.parse.urlparse(self.path)[2] 
            try: suffix = simple[simple.rindex("."):]  # file name without extension (foo.bar -> foo)
            except: suffix=""
            try: prefix = simple[:simple.index(".")]   # file extension (foo.bar -> .bar)
            except: prefix=""
            if DEBUG: print("suffix <"+suffix+">")

            if  fullpath.find("../")<0:
                simple=fullpath # for true CGI support, this allows deadly ".." path components!!

            if suffix.lower() in [".html", ".htm"]:
                if DEBUG: print("HTML request")
                f = open( os.path.join(os.curdir, prefix)+".html" )
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.send_header('Cache-Control', 'no-cache, max-age=1, must-revalidate, no-store')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            elif suffix.lower() in [".dtml"]:     # dtml is use to get a html file with basic variable substitutions
                if DEBUG: print("DTML request suffix:", suffix)
                f = open( os.path.join(os.curdir, prefix)+".html" )
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.send_header('Cache-Control', 'no-cache, max-age=1, must-revalidate, no-store')
                self.end_headers()

                data = f.read()
                # do substitutions
                data = data.replace("$$$date",time.ctime() )
                all = ""

                # substitute $$$code blocks
                #if 1:#try:
                if not SUPPORT_WINDOWS:
                    for line in data.split("\n"): # on each line...
                        try:
                            result=""
                            # print "LINE:",line
                            # look for $$$code ... ]$$$end
                            exp = re.search("\$\$\$code\[(.*)\]\$\$\$end",line).groups()[0]
                            # print "HAS:",exp

                            # create file-like string to capture output
                            #codeOut = StringIO.StringIO()
                            #codeErr = StringIO.StringIO()
                            # capture output and errors
                            #sys.stdout = codeOut
                            #sys.stderr = codeErr

                            try: 
                                exec(exp,dynamicvars)
                                if DEBUG: print("DEBUG: Executed",exp,"successfully:",data)
                            except AttributeError: pass
                            except:
                                print("Executed code had an error.")
                                print('-'*60)
                                traceback.print_exc(file=sys.stdout)
                                self.wfile.write("<pre>")
                                traceback.print_exc(file=self.wfile)
                                self.wfile.write("</pre>")
                                pass
                            try: 
                                result = str( eval(exp,dynamicvars) )
                                print("DEBUG: Evaluated",exp,"to produce",result)
                            except SyntaxError: pass
                            except:
                                print("Evaluated code had an error.")
                                print('-'*60)
                                traceback.print_exc(file=sys.stdout)
                                self.wfile.write("<pre>")
                                traceback.print_exc(file=self.wfile)
                                self.wfile.write("</pre>")
                                pass
                            # restore stdout and stderr
                            #sys.stdout = sys.__stdout__
                            #sys.stderr = sys.__stderr__
                            #
                            # replace $$$code ... ]$$$end with the result of the execution
                            line = re.sub("\$\$\$code\[(.*)\]\$\$\$end",result,line)
                            # print "PROCESSED:",line
                        except AttributeError: 
                            try:
                                if DEBUG: print("Searching %s for run "%line)
                                # look for $$$run[ ... ]$$$end
                                exp = re.search("\$\$\$run\[(.*)\]\$\$\$end",line).groups()[0]
                                if DEBUG: print("DEBUG: Popen(%s)"%exp)
                                if PYTHONVERSION >= 26:
                                    ran = subprocess.Popen(exp, stdout=subprocess.PIPE)
                                else:
                                    r,w = popen2.popen4(f)
                                    ran=r
                                result = ran.stdout.read()
                                if DEBUG: print("DEBUG: got result",result)
                                line = re.sub("\$\$\$run\[(.*)\]\$\$\$end",result,line)
                            except AttributeError: pass

                        all = all + "\n" + line
                    data = all
                #except: pass
                self.wfile.write(data)

                f.close()
                return

            elif suffix.lower() in [".cgi" ]: # not used
                    if DEBUG: print(os.path.join(os.curdir,simple))
                    query = urlparse_qs(  self.path)
                    os.putenv( "SCRIPT_NAME", simple )
                    os.putenv( "PATH_INFO", os.getcwd() )
                    os.putenv( "QUERY_STRING", '&'.join(map(str,list(query.values())))  )

                    if DEBUG: print(os.path.join(os.curdir,simple))
                    f = open( os.path.join(os.curdir,simple))

                    if PYTHONVERSION >= 26:
                        if DEBUG: print("call subprocess.Popen",os.path.join(os.curdir,simple))
                        io = subprocess.Popen(os.path.join(os.curdir,simple) , shell=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT ).stdout
                    else:
                        r,w = popen2.popen4(f)
                        io=r

                    feedback = io.read()
                    if DEBUG: print("call subprocess.Popen returned",feedback)
                    self.send_response(200)
                    # headend = feedback.index("\n\n")
                    # for i in feedback[:headend].split("\n"):
                    #     if i=="": break
                    #     print "Header:",i.split(":")[0],"Value:"," ".join(i.split(":")[1:])
                    #     self.send_header(i.split(":")[0]," ".join(i.split(":")[1:]))
                    self.end_headers()

                    # feedback=feedback[headend+1:]
                    if DEBUG: print("SCRIPT OUTPUT: <<"+feedback+">>")
                    self.wfile.write( feedback )
                    io.close()
                    return
            elif suffix.lower() in [".cgi", ".py", ".pyh", ".script" ]:
                if DEBUG: print("CGI request: <"+os.path.join(os.curdir,simple)+">")
                query = urlparse_qs(  self.path)
                if DEBUG: print("urlparse_qs:",urlparse_qs(  self.path))

                self.send_response(200)
                if suffix.lower()==".pyh":
                    self.send_header('Content-type','text/html' )
                    f = "/usr/bin/python "+simple[:-1]+" \""+str(query)+"\"" # open( os.path.join(os.curdir,simple))
                    if DEBUG: print("Running:",f)
                elif suffix.lower()==".py":
                    self.send_header('Content-type','text/plain' )
                    f = "/usr/bin/python "+simple+" \""+str(query)+"\"" # open( os.path.join(os.curdir,simple))
                    if DEBUG: print("Running: <<"+f+">>")
                else:  # cgi, script
                    os.putenv( "SCRIPT_NAME", simple )
                    os.putenv( "PATH_INFO", os.getcwd() )
                    os.putenv( "QUERY_STRING", '&'.join(map(str,list(query.values())))  )

                    self.send_header('Content-type','text/html' )
                    if DEBUG: print(os.path.join(os.curdir,simple))
                    f = os.path.join(os.curdir,simple)
                    if DEBUG: print("Running: <<"+f+">>")

                if PYTHONVERSION >= 26:
                    if DEBUG: print("call subprocess.Popen")
                    io = subprocess.Popen( f , shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT ).stdout
                else:
                    r,w = popen2.popen4(f)
                    io=r

                feedback = io.read()
                #print "SCRIPT OUTPUT: <<"+feedback+">>"
                self.send_header('Cache-Control', 'no-cache, max-age=1, must-revalidate, no-store')
                self.send_header('Pragma', 'no-cache') # probably has no effect, not HTML spec required
                #self.send_header('Expires','Fri, 30 Oct 1998 14:19:41 GMT')
                self.end_headers()
                self.wfile.write( feedback )
                io.close()
                return

            elif suffix[1:].lower() in ["jpeg","jpg","png","gif","pgm","bmp","tiff","tif"]:
                if DEBUG: print("Image request")
                f = open( os.path.join(os.curdir,simple))
                self.send_response(200)
                self.send_header('Content-type','image/'+suffix[1:] )
                self.send_header('Cache-Control', 'no-cache, max-age=1, must-revalidate, no-store')
                self.send_header('Pragma', 'no-cache') # probably has no effect, not HTML spec required
                # self.send_header('Expires: Fri, 30 Oct 1998 14:19:41 GMT')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            else:
                if DEBUG: print("arbitrary file request", os.path.join(os.curdir,simple))
                f = open( os.path.join(os.curdir,simple))
                self.send_response(200)
                self.send_header('Content-type',	'text/plain')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
                
            return
                
        except ValueError: # IOError:
            print("File extension:",suffix[1:].lower())
            self.send_error(404,'File Not Found: %s' % self.path)
     

    def do_POST(self):
        global rootnode
        belkinResponse = '''<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>
                            <u:SetBinaryStateResponse xmlns:u="urn:Belkin:service:basicevent:1">
                            <CountdownEndTime>0</CountdownEndTime>
                            </u:SetBinaryStateResponse>
                            </s:Body> </s:Envelope>'''
        url = os.path.basename( urllib.parse.urlparse(self.path)[2] )  # basic file name without directory
        print("POST request for",url)


        if 1: # try:
            if self.headers.getheader('content-type'):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            else:
                print("No content-type header")
                ctype, pdict = "",{}

            print("POST ctype:",ctype,"pdict:",pdict)
            if ctype == 'multipart/form-data':
                postvars =cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.getheader('content-length'))
                postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                print("Unknown ctype",ctype)
                length = int(self.headers.getheader('content-length'))
                data  = self.rfile.read(length).strip()
                if DEBUG: print("rfile:",data)
                import xml.etree.ElementTree as ET
                #tree = ET.parse(data) # disk file name;root = tree.getroot()
                if data:
                   root = ET.fromstring(data)
                   try:
                    if DEBUG: print("ROOT:",root.tag) # '{urn:Belkin:service:basicevent:1}SetBinaryState'
                    if DEBUG: print(root[0].tag)   # '{urn:Belkin:service:basicevent:1}SetBinaryState'
                    if DEBUG: print(root[0][0].tag)   # '{urn:Belkin:service:basicevent:1}SetBinaryState'
                    if DEBUG: print(root[0][0][0].tag)  # 'BinaryState'
                    if DEBUG: print(root[0][0][0].text) # 0 or 1
                    if root[0][0].tag=='{urn:Belkin:service:basicevent:1}SetBinaryState':
                        newstate = int(root[0][0][0].text) # 0 or 1
                        if newstate:
                            os.system('(echo -local vpr ; sleep 1 ) | telnet 192.168.0.163 1111')
                            print("Turned on")
                        else:
                            os.system('(echo off ; sleep 1 ) | telnet 192.168.0.163 1111')
                            print("Turned off")
                   except: pass

                postvars = {}

            print("POST variables:",postvars)

            self.send_response(200) # Moved Permanently
            #self.send_response(301) # Moved Permanently
            self.end_headers()
            try:
                upfilecontent = query.get('upfile')
                print("filecontent", upfilecontent[0][0:20],"...")   #  this is the uploaded file object from our upload.html script
                self.wfile.write("<HTML>POST OK.<BR><BR>")
                self.wfile.write(upfilecontent[0][0:20]+" ...")  #  this is the uploaded file object from our upload.html script
            except: pass
            try:
                if url=="basicevent1": print("Echo request")
                self.wfile.write( belkinResponse )
            except: pass

            if DEBUG: print("POST handling done.")
            
        #except :
        #    pass

def webserve():
    try:
        web = HTTPServer(('', my_http_port), webServer)
        web.serve_forever()
    except KeyboardInterrupt:
        print('Got Interrupt signal.  Goodbye')
        web.socket.close()

if __name__ == '__main__':
    print(('webServer %s in %s on port %d in %s...'%(VERSION,os.curdir,my_http_port,os.getcwd())))
    try:
        import initweb
    except: pass
    webserve()

