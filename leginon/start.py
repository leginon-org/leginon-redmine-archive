#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import manager
import launcher
import uiclient
import socket
import threading

#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

'''
def startManager(location, event):
	location.update(manager.Manager(('manager',), None).location())
	event.set()

def startLauncher(location, event):
	launcher.Launcher((socket.gethostname(),), {'manager': location})
	event.set()

location = {}
event = threading.Event()
threading.Thread(target=startManager, args=(location, event)).start()
event.wait()
threading.Thread(target=startLauncher, args=(location, event)).start()
event.wait()
'''

location = manager.Manager(('manager',), None).location()
launcher.Launcher((socket.gethostname(),), {'manager': location})
client = uiclient.UIApp(location['UI'], 'Leginon II')

