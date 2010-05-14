#!/usr/bin/python -O

#python
import re
import os
import sys
import time
import random
import subprocess
#appion
import leginon.leginondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import apStack
from appionlib import apParam
from appionlib import apFile
from appionlib import apCtf
from appionlib import apAlignment
from appionlib import apDatabase

class testScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ --commit --show-cmd --verbose ]")
		### showcmd
		self.parser.add_option("-S", "--show-cmd", dest="showcmd", default=True,
			action="store_true", help="Show each command before running")
		self.parser.add_option("--no-show-cmd", dest="showcmd", default=True,
			action="store_false", help="Do not show each command before running")
		### verbose
		self.parser.add_option("-v", "--verbose", dest="verbose", default=True,
			action="store_true", help="Show command output while running")
		self.parser.add_option("-q", "--quiet", dest="verbose", default=True,
			action="store_false", help="Do not show command output while running")

		self.parser.add_option("-u", "--uploadimages", dest="uploadimages", default=False,
			action="store_true", help="Do not show command output while running")
		self.parser.add_option("--session", dest="sessionname",
			help="Session name containing GroEL images to process", metavar="XX")

		return

	#=====================
	def checkConflicts(self):
		if self.params['uploadimages'] is False and self.params['sessionname'] is None:
			apDisplay.printError("Please set uploadimages to true or provide a GroEL session name")
		if self.params['uploadimages'] is True and self.params['sessionname'] is not None:
			apDisplay.printError("Please set uploadimages to false or remove session name")
		return

	#=====================
	def setRunDir(self):
		if self.params['uploadimages'] is True:
			try:
				basedir = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
				basedir.replace("leginon", "appion")
			except:
				basedir = os.getcwd()
			self.params['rundir'] = os.path.join(basedir, self.timestamp, "testsuite", self.timestamp)
		else:
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			basedir = os.path.abspath(sessiondata['image path'])
			basedir.replace("leginon", "appion")
			basedir = re.sub("/rawdata","",basedir)
			self.params['rundir'] = os.path.join(basedir, "testsuite", self.timestamp)
		return

	#=====================
	def runCommand(self, cmd):
		t0 = time.time()
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "magenta")
			sys.stderr.write(
				apDisplay.colorString("COMMAND: \n","magenta")
				+apDisplay.colorString(cmd, "cyan")+"\n")
			apDisplay.printColor("###################################", "cyan")
		try:
			if self.params['verbose'] is False:
				proc = subprocess.Popen(cmd, shell=True, 
					stdout=subprocess.PIPE)#, stderr=subprocess.PIPE)
			else:
				proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		except:
			apDisplay.printError("could not run command: "+cmd)
		runtime = time.time() - t0
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "cyan")
			apDisplay.printColor("command ran in "+apDisplay.timeString(runtime), "cyan")
		if runtime < 1:
			apDisplay.printError("command runtime was too short: "
				+apDisplay.timeString(runtime))
		elif runtime < 10:
			apDisplay.printWarning("command runtime was very short: "
				+apDisplay.timeString(runtime))
			return False

		return True

	#=====================
	def runFindEM(self):
		runid = "findem"
		cmd = (os.path.join(self.appiondir, "bin", "templateCorrelator.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" diam=140 bin=4 maxpeaks=50 overlapmult=3 nocontinue "
			+" templateIds=53 range1=0,180,30 thresh=0.50 maxthresh=0.60 "
			+" lp=25 hp=600 pixlimit=3.0 median=3 ")
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def downloadImagesFromAMI(self):
		imglist = []
		from urllib import urlretrieve
		imgdict = {
			110: '06jul12a_00022gr_00037sq_00025hl_00005en.mrc',
			111: '06jul12a_00035gr_00063sq_00012hl_00004en.mrc',
			112: '06jul12a_00015gr_00028sq_00004hl_00002en.mrc',
			113: '06jul12a_00015gr_00028sq_00023hl_00002en.mrc',
			114: '06jul12a_00015gr_00028sq_00023hl_00004en.mrc',
			115: '06jul12a_00022gr_00013sq_00002hl_00004en.mrc',
			116: '06jul12a_00022gr_00013sq_00003hl_00005en.mrc',
		}
		for key in imgdict.keys():
			imgfile = os.path.join(self.params['rundir'], imgdict[key])
			url = ("http://ami.scripps.edu/redmine/attachments/download/%d/%s"
				%(key, imgdict[key]))
			apDisplay.printMsg("Downloading image '%s'"%(imgdict[key]))
			urlretrieve(url, imgfile)
			if not os.path.isfile(imgfile):
				apDisplay.printError("could not download file: %s"%(url))
			if apFile.fileSize(imgfile) < 30e6:
				apDisplay.printError("error in downloaded file: %s"%(url))
			imglist.append(imgfile)
		return imglist

	#=====================
	def createImageBatchFile(self, imglist):
		imgstats = {
			'pixelsize': 0.815e-10,
			'binx': 1,
			'biny': 1,
			'mag': 100000,
			'defocus': -2.0e-6,
			'voltage': 120000,
		}

		imagedatfile = os.path.join(self.params['rundir'], "image%s.dat"%(self.sessionname))
		f = open(imagedatfile, "w")
		for imgfile in imglist:
			outstr = ("%s\t%.3e\t%d\t%d\t%d\t%.3e\t%d\n"
				%(imgfile, imgstats['pixelsize'], imgstats['binx'], imgstats['biny'], 
				imgstats['mag'], imgstats['defocus'], imgstats['voltage']))
			f.write(outstr)
		f.close()
		return imagedatfile

	#=====================
	def getInstrumentIds(self):
		### get scope
		scopeq = leginon.leginondata.InstrumentData()
		print scopeq
		scopeq['name'] = 'SimTEM'
		scopedatas = scopeq.query(results=1)
		if not scopedatas or len(scopedatas) < 1:
			apDisplay.printError("Could not find simulated scope")
		random.shuffle(scopedatas)
		scopeid = scopedatas[0].dbid
		apDisplay.printMsg("Selected scope %d from host %s"	
			%(scopeid, scopedatas[0]['hostname']))

		### get camera
		cameraq = leginon.leginondata.InstrumentData()
		cameraq['name'] = 'SimCCDCamera'
		cameradatas = cameraq.query(results=1)
		if not cameradatas or len(cameradatas) < 1:
			apDisplay.printError("Could not find simulated CCD camera")
		random.shuffle(scopedatas)
		carmeraid = cameradatas[0].dbid
		apDisplay.printMsg("Selected camera %d from host %s"	
			%(carmeraid, cameradatas[0]['hostname']))
		return scopeid, carmeraid

	#=====================
	def uploadImages(self):
		### get simulated instrument ids
		scopeid, cameraid = self.getInstrumentIds()
		### Download images
		imglist = self.downloadImagesFromAMI()
		### create batch file
		imagedatfile = self.createImageBatchFile(imglist)
		### run command
		script = os.path.join(self.appiondir, "bin", "imageloader.py ")
		params = (" --runname=%s --projectid=%d --session=%s --batch=%s --scopeid=%d --cameraid=%d --description='%s' "
			%(self.sessionname, self.params['projectid'], self.sessionname, 
			imagedatfile, scopeid, cameraid, self.params['description']+' running test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def dogPicker(self):
		runnum = apParticle.getNumSelectionRunsFromSession(self.sessionname)
		dogname = "dogrun%d-%s"%(runnum+1, self.timestamp)

		script = os.path.join(self.appiondir, "bin", "dogPicker.py ")
		params = (" --runname=%s --projectid=%d --session=%s --diam=%d --thresh=%.2f --maxthresh=%.2f --invert --no-wait --planereg --maxsize=%.2f --numslices=%d --sizerange=%d"
			%(dogname, self.params['projectid'], self.sessionname, 150, 0.42, 0.8, 0.5, 3, 50))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)
		return dogname

	#=====================
	def aceTwo(self, bin, blur=10):
		runnum = apCtf.getNumCtfRunsFromSession(self.sessionname)
		acetwoname = "acetwo%d-%s"%(runnum+1, self.timestamp)

		script = os.path.join(self.appiondir, "bin", "pyace2.py ")
		params = (" --runname=%s --projectid=%d --session=%s --no-wait --bin=%d --edge1=%.1f --cs=2.0 "
			%(acetwoname, self.params['projectid'], self.sessionname, bin, blur))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def makeStack(self):
		runnum = apStack.getNumStacksFromSession(self.sessionname)
		stackname = "stack%d-%s"%(runnum+1, self.timestamp)

		selectid = apParticle.getRecentSelectionIdFromSession(self.sessionname)

		script = os.path.join(self.appiondir, "bin", "makestack2.py ")
		params = ((" --runname=%s --projectid=%d --session=%s --no-wait --boxsize=%d --bin=%d --acecutoff=%.2f --invert --phaseflip --flip-type=ace2image --selectionid=%d --description='%s'")
			%(stackname, self.params['projectid'], self.sessionname, 512, 2, 0.7, selectid, 'running test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)
		return stackname

	#=====================
	def filterStack(self, stackname):
		runnum = apStack.getNumStacksFromSession(self.sessionname)
		filtstackname = "meanfilt%d-%s"%(runnum+1, self.timestamp)

		stackid = apStack.getStackIdFromRunName(stackname, self.sessionname)

		script = os.path.join(self.appiondir, "bin", "stackFilter.py ")
		params = ((" --runname=%s --projectid=%d --old-stack-id=%d --minx=%d --maxx=%d --miny=%d --maxy=%d --description='%s'")
			%(filtstackname, self.params['projectid'], stackid, 
			600, 1000, 82, 105, 
			'filtering junk with test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

		return filtstackname

	#=====================
	def maxLike(self, substackname):
		runnum = apAlignment.getNumAlignRunsFromSession(self.sessionname)
		maxlikename = "maxlike%d-%s"%(runnum+1, self.timestamp)

		stackid = apStack.getStackIdFromSubStackName(substackname, self.sessionname)

		print (self.params['projectid'], stackid, 10, 2000, 3, 1, 12, 'max like with test suite application')

		script = os.path.join(self.appiondir, "bin", "maxlikeAlignment.py")
		params = (" --runname=%s --projectid=%d --stack=%d --lowpass=%d --highpass=%d --num-ref=%d --bin=%d --savemem --converge=slow --mirror --fast --fast-mode=narrow --max-iter=%d --description='%s'"
			%(maxlikename, self.params['projectid'], stackid, 10, 2000, 3, 1, 12, 
			'max like with test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

		return maxlikename

		#uploadMaxlikeAlignment.py --rundir=/ami/data00/appion/10may07o04/align/maxlike1 -t 10may07q59 --commit --projectid=5 

	#=====================
	def uploadMaxLike(self, maxlikename):
		maxjobdata = apAlignment.getMaxlikeJobDataForUpload(maxlikename)
		tstamp = maxjobdata['timestamp']
		script = os.path.join(self.appiondir, "bin", "uploadMaxlikeAlignment.py")
		params = (" --projectid=%d --timestamp=%s "%(self.params['projectid'], tstamp,))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================.
	def start(self):
		if self.params['uploadimages'] is True:
			self.sessionname = self.timestamp
			self.uploadImages()
		else:
			self.sessionname = self.params['sessionname']

		### Dog Picker
		self.dogPicker()

		### Ace 2
		self.aceTwo(bin=2, blur=10)
		self.aceTwo(bin=2, blur=6)
		self.aceTwo(bin=4)

		### Make stack
		stackname = self.makeStack()

		### Filter stack
		filtstackname = self.filterStack(stackname)

		### Maximum likelihood
		maxlikename = self.maxLike(filtstackname)

		### Upload max like
		self.uploadMaxLike(maxlikename)

		### Upload templates
		### Template pick
		### Make stack
		### Filter stack
		### Upload model
		### Do reconstruction
		### Upload recon
		return

#=====================
if __name__ == "__main__":
	tester = testScript()
	tester.start()
	tester.close()

