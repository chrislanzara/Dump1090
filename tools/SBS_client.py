#!/usr/bin/env python3

"""
Simple Python script for Dump1090 testing:
Supported modes: RAW-OUT, RAW-IN and SBS.

RAW-OUT server: Connect to host at port 30001 and send '*...;' messages and print it to console.
RAW-IN client:  Connect to host at port 30002, receive '*...;' messages and print it to console.
SBS client:     Connect to host at port 30003, listen for 'MSG,' text and print it to console.
"""

import sys, os, time, argparse, socket

REMOTE_HOST  = "localhost"
RAW_OUT_PORT = 30001
RAW_IN_PORT  = 30002
SBS_PORT     = 30003
RAW_OUT_MSG  = b"*8d4b969699155600e87406f5b69f;\n"

class cfg():
  logf     = None
  sock     = None
  loop     = None
  format   = "?? %d bytes\n"
  data_len = 0
  sleep    = 1
  quit     = False

#
# Print to both stdout and log-file
#
def modes_log (s):
  if not s:
     fname = os.path.dirname(__file__) + "\\SBS_client.log"
     cfg.logf = open (fname, "a+t")
     cfg.logf.write ("\n%s: --- Starting -------\n" % time.strftime("%d-%B-%Y %H:%M:%S"))
  else:
     os.write (1, bytes(s, encoding="ascii"))
     cfg.logf.write ("%s: %s" % (time.strftime("%H:%M:%S"), str(s)))

def show_help (error=None):
  if error:
     print (error)
     sys.exit (1)

  print (__doc__[1:])
  print ("""Usage: %s [options] [RAW-OUT | RAW-IN | SBS]
  -h, --help: Show this help.
  --host      Host to connect to.
  --port      TCP port to connect to.
  --wait      Seconds to wait before connecting (default=0).""" % __file__)
  sys.exit (0)

def parse_cmdline():
  parser = argparse.ArgumentParser (add_help = False)
  parser.add_argument ("-h", "--help", dest = "help", action = "store_true")
  parser.add_argument ("--host",       dest = "host", type = str, default = REMOTE_HOST)
  parser.add_argument ("--port",       dest = "port", type = int, default = 0)
  parser.add_argument ("--wait",       dest = "wait", type = int, default = 0)
  parser.add_argument ("mode", nargs = argparse.REMAINDER)
  return parser.parse_args()

def connect_to_host (opt):
  try:
    s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
    # print (dir(s))
    s.connect ((opt.host, opt.port))
    modes_log ("Connected to %s:%d\n" % (opt.host, opt.port))
    return s
  except:
    modes_log ("Connection refused\n")
    cfg.logf.close()
    sys.exit (1)

#
# For receiving RAW-IN messages.
#
def raw_in_loop (sock):
  do_sleep = True
  try:
    if 1:
       data = sock.readline (10)
    else:
       data = sock.recv (100, socket.MSG_WAITALL)
    # print (data)
  except:
    do_sleep = False
    print ("do_sleep = False")
    data = None

  if data:
     modes_log (data)
     cfg.data_len += len(data)
     time.sleep (cfg.sleep)
  elif do_sleep:
     time.sleep (cfg.sleep)
  else:
     modes_log ("Connection gone.\n")
     cfg.quit = True

#
# For receiving SBS messages.
#
def sbs_in_loop (sock):
  data = sock.readline()
  print (data)
  if not data:
     modes_log ("Connection gone.\n")
     cfg.quit = True
  else:
    modes_log (data)
    cfg.data_len += len(data)
    time.sleep (cfg.sleep)

#
# For sending RAW-OUT messages.
#
# Simulate a Dump1090 RAW-IN client for testing
#   read_from_client()
#
# Todo:
#   Send random messages from several airplanes by constructing
#   realistics messages on the fly. Messages with positions close
#   to home. Show the distance in `--interactive` mode.
#
def raw_out_loop (sock):
  modes_log ("Sending RAW message: %s.\n" % str(RAW_OUT_MSG))
  rc = sock.send (RAW_OUT_MSG)
  if rc > 0:
     cfg.data_len += rc
  else:
     raise (ConnectionResetError)
  for i in range(cfg.sleep):
      time.sleep (1)

### main() ####################################

opt = parse_cmdline()
if opt.help:
   show_help()

if len(opt.mode) == 0:
   show_help ("Missing 'mode'. Use '%s -h' for usage" % __file__)

mode = opt.mode[0].upper()
if mode != "SBS" and mode != "RAW-IN" and mode != "RAW-OUT":
   show_help ("Unknown 'mode = %s'. Use '%s -h' for usage" % (opt.mode[0], __file__))

if opt.port == 0:
  if mode == "SBS":
     opt.port = SBS_PORT
  elif mode == "RAW-IN":
     opt.port = RAW_IN_PORT
  elif mode == "RAW-OUT":
     opt.port = RAW_OUT_PORT

modes_log (None)
modes_log ("Connecting to %s:%d\n" % (opt.host, opt.port))

if opt.wait:
   modes_log ("Waiting %d sec before connecting\n" % opt.wait)
   for i in range(opt.wait):
       time.sleep (1)
       os.write (1, b".")
   modes_log ("\n")

cfg.sock = connect_to_host (opt)

if mode == "RAW-OUT":
   cfg.sleep  = 1
   cfg.loop   = raw_out_loop
   cfg.format = "Sent %d bytes\n"
elif mode == "RAW-IN":
   cfg.sleep  = 0.01
   cfg.loop   = raw_in_loop
   cfg.format = "Received %d bytes\n"
 # cfg.sock.setblocking (False)
   cfg.sock   = cfg.sock.makefile (mode="r")
else:
   cfg.sleep  = 0.01
   cfg.loop   = sbs_in_loop
   cfg.format = "Received %d bytes\n"
   cfg.sock   = cfg.sock.makefile (mode="r")

try:
  while not cfg.quit:
    cfg.loop (cfg.sock)

except (ConnectionResetError, ConnectionAbortedError):
  modes_log ("Connection reset.\n")
  cfg.quit = True

except KeyboardInterrupt:
  print ("^C")
  cfg.quit = True

modes_log (cfg.format % cfg.data_len)
cfg.sock.close()
cfg.logf.close()
