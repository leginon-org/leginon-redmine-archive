#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

"""
Fill in the values below and rename this file leginonconfig.py
The only required values are IMAGE_PATH and the values starting
with DB_.  There are several optional values as well.

leginonconfig.py: Configuration file for leginon defaults and such
We could also do this using the ConfigParser module and have this
be a more standard .ini file thing.
"""

#######################################################################
#   UTILITY FUNCTIONS FOR THIS SCRIPT
#     (do not change any of this, skip to next section)
#######################################################################

import errno
import os
import ConfigParser

logevents = False

pathmapping = {}
def mapPath(path):
		if not pathmapping:
			return path

		for key, value in pathmapping.items():
			if value == path[:len(value)]:
				path = key + path[len(value):]
				break
		return path

def unmapPath(path):
		if not pathmapping:
			return path

		for key, value in pathmapping.items():
			if key == path[:len(key)]:
				path = value + path[len(key):]
				break

		return os.path.normpath(path)

# Here is a replacement for os.mkdirs that won't complain if dir
# already exists (from Python Cookbook, Recipe 4.17)
def mkdirs(newdir, mode=0777):
	try: os.makedirs(newdir, mode)
	except OSError, err:
		if err.errno != errno.EEXIST or not os.path.isdir(newdir):
			raise
### raise this if something is wrong in this config file
class LeginonConfigError(Exception):
	pass

configparser = ConfigParser.SafeConfigParser()
defaultfilename = 'default.cfg'
try:
	configparser.readfp(open(defaultfilename), defaultfilename)
except IOError:
	raise LeginonConfigError('Cannot find configuration file leginon.cfg')
configparser.read('leginon.cfg')

#######################################################################
#    DATABASE
#######################################################################

## Main leginon database
section = 'Database'
DB_HOST = configparser.get(section, 'hostname')
DB_NAME = configparser.get(section, 'name')
DB_USER = configparser.get(section, 'username')
DB_PASS = configparser.get(section, 'password')

## This is a check to see if DB is configured above (DB_PASS can be '')
if '' in (DB_HOST, DB_NAME, DB_USER):
	raise LeginonConfigError('need database info in leginonconfig.py')

# This is optional.  If not using a project database, leave these
# set to None
section = 'Project Database'
DB_PROJECT_HOST = configparser.get(section, 'hostname')
DB_PROJECT_NAME = configparser.get(section, 'name')
DB_PROJECT_USER = configparser.get(section, 'username')
DB_PROJECT_PASS = configparser.get(section, 'password')


#######################################################################
#	IMAGE DIRECTORY
#######################################################################
#
# IMAGE_PATH is a base directory - a session subdirectory will 
# automatically be created under it when the first image is saved
# for that session.
# Be sure to use os.path.join() if you want to keep it platform independent
# You may want to use the common path components HOME, for the current
# system user home directory (not leginon user), and CURRENT, which is 
# the current directory (where this process was executed, not necessarily
# where this script resides)

HOME = os.path.expanduser('~')
CURRENT = os.getcwd()
IMAGE_PATH = configparser.get('Images', 'path')

### check to see if image path has been set, then create it
if not IMAGE_PATH:
	raise LeginonConfigError('set IMAGE_PATH in leginonconfig.py')
try:
	mkdirs(mapPath(IMAGE_PATH))
except:
	print 'error creating IMAGE_PATH %s' % (IMAGE_PATH,)


#######################################################################
#    Leginon User Name (optional)
#######################################################################
# This will allow you to bypass the opening login window and directly
# login as this user.  This is mainly used for debugging, because for
# most installations, all users will be using a common leginonconfig.py
# Leave it blank to be presented with a user name selector at start up.
USERNAME = configparser.get('User', 'name')

