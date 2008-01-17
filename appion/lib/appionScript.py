#!/usr/bin/python -O

#builtin
import sys
import os
import re
import time
import math
import random
import cPickle
from optparse import OptionParser
#appion
import apDisplay
import apDatabase
import apParam
#leginon
from pyami import mem

class AppionScript(object):
	def __init__(self):
		#set the name of the function; needed for param setup
		self.functionname = apParam.getFunctionName(sys.argv[0])
		self.setProcessingDirName()

		### setup default parser: output directory, etc.
		self.parser = OptionParser(usage=self.usage)
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)

		### check if user wants to print help message
		self.checkConflicts()

		### write function log
		apParam.writeFunctionLog(sys.argv)

		### setup output directory
		self._setupOutputDirectory()

		### any custom init functions go here
		self.onInit()

	def _setupOutputDirectory(self):
		if self.params['outdir'] is None and 'session' in self.params:
			#auto set the output directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			self.params['outdir'] = os.path.join(path, self.processdirname)

		#create the output directory, if needed
		apDisplay.printMsg("Output directory: "+self.params['outdir'])
		apParam.createDirectory(self.params['outdir'])		

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	usage = ( "Usage: %prog --session=<session> --description='<text>' [options]" )

	def setupParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the template (must be in quotes)", metavar="TEXT")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")

	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID, e.g. --session=07jun06a")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")

	def setProcessingDirName(self):
		self.processdirname = self.functionname

	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		raise NotImplementedError()

	def onInit(self):
		return

class TestScript(AppionScript):
	def start(self):
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	print "__init__"
	testscript = TestScript()
	print "start"
	testscript.start()


