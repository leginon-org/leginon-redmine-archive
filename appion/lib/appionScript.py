#!/usr/bin/python -O

import pyami.quietscipy

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
import apFile
#leginon
from pyami import mem


class AppionScript(object):
	#=====================
	def __init__(self):
		### setup some expected values
		sys.stderr.write("\n\n")
		self.quiet = False
		self.startmem = mem.active()
		self.t0 = time.time()
		self.createDefaultStats()
		self.timestamp = apParam.makeTimestamp()
		apDisplay.printMsg("Time stamp: "+self.timestamp)
		self.functionname = apParam.getFunctionName(sys.argv[0])
		apDisplay.printMsg("Function name: "+self.functionname)
		self.appiondir = apParam.getAppionDirectory()
		apDisplay.printMsg("Appion directory: "+self.appiondir)
		apParam.setUmask()
		self.parsePythonPath()

		### setup default parser: run directory, etc.
		self.parser = OptionParser()
		#self.setupGlobalParserOptions()
		self.setupParserOptions()
		self.params = apParam.convertParserToParams(self.parser)
		self.checkForDuplicateCommandLineInputs()
		self.params['rundir'] = self.params['outdir']

		### setup correct database after we have read the project id
		if False and self.params['projectid'] is not None:
			apDisplay.printWarning("Using split database")
			# use a project database
			newdbname = "ap"+str(self.params['projectid'])
			sinedon.setConfig('appionData', db=newdbname)

		### check if user wants to print help message
		if self.params['commit'] is False:
			apDisplay.printWarning("Not committing data to database")
		else:
			apDisplay.printMsg("Committing data to database")
		self.checkConflicts()

		### setup run directory
		self.setProcessingDirName()
		self.setupRunDirectory()
		if apDatabase.queryDirectory(self.params['rundir']):
			self.preExistingDirectoryError()

		### write function log
		self.logfile = apParam.writeFunctionLog(sys.argv, msg=(not self.quiet))

		### any custom init functions go here
		self.onInit()

	#=====================
	def checkForDuplicateCommandLineInputs(self):
		args = sys.argv[1:]
		argdict = {}
		for arg in args:
			elements=arg.split('=')
			opt = elements[0].lower()
			if opt in argdict:
				apDisplay.printError("Multiple arguments were supplied for argument: "+str(opt))
			else:
				argdict[opt] = True

	#=====================
	def createDefaultStats(self):
		self.stats = {}
		self.stats['startTime']=time.time()
		self.stats['count'] = 1
		self.stats['lastcount'] = 0
		self.stats['startmem'] = mem.active()
		self.stats['memleak'] = False
		self.stats['peaksum'] = 0
		self.stats['lastpeaks'] = None
		self.stats['imagesleft'] = 1
		self.stats['peaksumsq'] = 0
		self.stats['timesum'] = 0
		self.stats['timesumsq'] = 0
		self.stats['skipcount'] = 0
		self.stats['waittime'] = 0
		self.stats['lastimageskipped'] = False
		self.stats['notpair'] = 0
		self.stats['memlist'] = [mem.active()]

	#=====================
	def setupRunDirectory(self):
		#IF NO RUNDIR IS SET
		if self.params['outdir'] is None:
			self.setOutDir()
		#create the run directory, if needed
		if self.quiet is False:
			apDisplay.printMsg("Run directory: "+self.params['outdir'])
		apParam.createDirectory(self.params['outdir'], warning=(not self.quiet))
		os.chdir(self.params['outdir'])

	#=====================
	def close(self):
		self.onClose()
		apParam.closeFunctionLog(params=self.params, logfile=self.logfile, msg=(not self.quiet))
		apFile.removeFile("spider.log")
		if self.quiet is False:
			apDisplay.printMsg("memory increase during run: %.3f MB"%((mem.active()-self.startmem)/1024.0))
			apDisplay.printMsg("outdir:\n "+self.params['outdir'])
			apDisplay.printColor("COMPLETE SCRIPT:\t"+apDisplay.timeString(time.time()-self.t0),"green")
		apParam.killVirtualFrameBuffer()

	#=====================
	def parsePythonPath(self):
		pythonpath = os.environ.get("PYTHONPATH")
		paths = pythonpath.split(":")
		leginons = []
		appions = []
		for p in paths:
			if "appion" in p:
				appions.append(p)
			if "leginon" in p:
				leginons.append(p)
		if len(appions) > 1:
			apDisplay.printWarning("There is more than one appion directory in your PYTHONPATH")
			print appions
		if len(leginons) > 1:
			apDisplay.printWarning("There is more than one leginon directory in your PYTHONPATH")
			print leginons

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def preExistingDirectoryError(self):
		apDisplay.printWarning("Run directory already exists in the database")

	#=====================
	def setupParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.set_usage("Usage: %prog --session=<session> --commit --description='<text>' [options]")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the template (must be in quotes)", metavar="TEXT")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--runid", "-r", dest="runid", default=self.timestamp,
			help="Run ID name, e.g. --runid=run1", metavar="NAME")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID, e.g. --session=07jun06a")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = self.functionname

	#=====================
	def setOutDir(self):
		import apStack
		if ( self.params['outdir'] is None 
		and 'session' in self.params 
		and self.params['session'] is not None ):
			#auto set the run directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname)
			self.params['outdir'] = path
		if ( self.params['outdir'] is None 
		and 'reconid' in self.params 
		and self.params['reconid'] is not None ):
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'], msg=False)
		if ( self.params['outdir'] is None 
		and 'stackid' in self.params
		and self.params['stackid'] is not None ):
			#auto set the run directory
			stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			path = os.path.abspath(stackdata['path']['path'])
			path = os.path.dirname(path)
			path = os.path.dirname(path)
			self.params['outdir'] = os.path.join(path, self.processdirname)

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		raise NotImplementedError()

	#=====================
	def onInit(self):
		return

	#=====================
	def onClose(self):
		return

class TestScript(AppionScript):
	def start(self):
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	print "__init__"
	testscript = TestScript()
	print "start"
	testscript.start()
	print "close"
	testscript.close()
	


