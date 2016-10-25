#!/usr/bin/env python

#pythonlib
import os
import re
import math
import time
import shutil
import subprocess
#appion
from appionlib import apFile
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apDDprocess
from appionlib import appionLoop2
from appionlib import appiondata
from appionlib import apInstrument
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert

#from appionlib import ctffind4

#class gctfEstimateLoop(ctffind4.ctfEstimateLoop):
class gctfEstimateLoop(appionLoop2.AppionLoop):
	"""
	appion Loop function that uses Gctf-v1.06
	to estimate the CTF in images.
	Please link your working executable to Gctf-v1.06 that can be found in your PATH environment
	variable
	"""

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--ampcontrast", dest="ampcontrast", type="float", default=0.07,
			help="ampcontrast, default=0.07", metavar="#")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=1024,
			help="fieldsize, default=1024", metavar="#")
		self.parser.add_option("--nominal", dest="nominal", type="float",
			help="nominal override value (in microns, absolute value)")
		self.parser.add_option("--resmin", dest="resmin", type="float", default=50.0,
			help="Low resolution end of data to be fitted in Angstroms", metavar="#")
		self.parser.add_option("--resmax", dest="resmax", type="float", default=4.0,
			help="High resolution end of data to be fitted in Angstroms", metavar="#")
		self.parser.add_option("--defstep", dest="defstep", type="float", default=0.05,
			help="Step width for grid search in microns", metavar="#")
		self.parser.add_option("--numstep", dest="numstep", type="int", default=25,
			help="Number of steps to search in grid", metavar="#")
		self.parser.add_option("--dast", dest="dast", type="float", default=1000.0,
			help="dAst in microns is used to restrain the amount of astigmatism", metavar="#")
	
		self.parser.add_option("--do_EPA", dest="do_EPA", default=False, action="store_true",
			help="Do equiphase averaging")

		self.parser.add_option("--do_Hres_ref", dest="do_Hres_ref", default=False, action="store_true",
			help="Boost high resolution refinement")

		self.parser.add_option("--bestdb", "--best-database", dest="bestdb", default=False,
			action="store_true", help="Use best amplitude contrast and astig difference from database")

		## not actually necessary, since we are using GPU, but we keep it so we don't break things
		self.parser.add_option("--ppn", dest="ppn", type="int", default=1,
			help="number of processors", metavar="#")

		self.parser.add_option("--ddstackid", dest="ddstackid",type="int",
			help="DD stack ID", metavar="#")

		self.parser.add_option("--mdef_aveN", dest="mdef_aveN", type="int",default=1,
				help="Average number of moive frames for movie or particle stack CTF refinement")


		self.parser.add_option("--max_phase_shift", dest="max_phase_shift", type="int",
				help="Maximum value for phase search")


		self.parser.add_option("--min_phase_shift", dest="min_phase_shift", type="int",
				help="Min value for phase search")


		self.parser.add_option("--phase_search_step", dest="phase_search_step", type="int",
				help="Phase search step increment")

                self.parser.add_option("--phaseplate", "--phase_plate", dest="shift_phase", default=False,
                        action="store_true", help="Find additional phase shift")

	

	#======================
	def checkConflicts(self):
		if self.params['resmin'] > 50.0:
			apDisplay.printError("Please choose a higher resolution for resmin must be btw 10 and 50")
		if self.params['resmin'] < 10.0:
			apDisplay.printError("Please choose a lower resolution for resmin")
		if self.params['resmax'] > 15.0 or self.params['resmax'] > self.params['resmin']:
			apDisplay.printError("Please choose a higher resolution for resmax")
		if self.params['defstep'] < 0.0001 or self.params['defstep'] > 2.0:
			apDisplay.printError("Please keep the defstep between 0.0001 & 2 microns")
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		return


	#======================
	def setProcessingDirName(self):
		self.processdirname = "gctf"

	#======================
	def preLoopFunctions(self):
		self.ctfrun = None
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)
		self.ctfprgmexe = self.getCtfProgPath()
		# check and process more often because it is slower than data collection
		self.setWaitSleepMin(1)
		self.setProcessBatchCount(1)
		return

	#======================
	def getCtfProgPath(self):
		
		exename = "gctfCurrent"
		ctfprgmexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ctfprgmexe):
			ctfprgmexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ctfprgmexe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		apDisplay.printMsg("Running program %s"%(exename))
		
		return ctfprgmexe 

	#======================
	def postLoopFunctions(self):
		ctfdb.printCtfSummary(self.params, self.imgtree)

	#======================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return None
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None
		if conf > self.params['reprocess']:
			return False
		else:
			return True

	#======================
	def processImage(self, imgdata):
		"""
		time ./ctffind3.exe << eof
		Input image file name                  [input.mrc] : 15aug13neil2_14jul14d_05sq_012hl_02ed-a.mrc
		Output diagnostic filename
		[diagnostic_output.mrc]                            : 15aug13neil2_14jul14d_05sq_012hl_02ed-a-pow.mrc
		Pixel size                                   [1.0] : 2.7
		Acceleration voltage                       [300.0] : 300 
		Spherical aberration                         [2.7] : 2.7
		Amplitude contrast                          [0.07] : 0.07
		Size of power spectrum to compute            [512] : 512
		Minimum resolution                          [30.0] : 20
		Maximum resolution                           [5.0] : 5
		Minimum defocus                           [5000.0] : 
		Maximum defocus                          [50000.0] : 
		Defocus search step                        [500.0] : 
		Expected (tolerated) astigmatism           [100.0] : 
		Find additional phase shift?                  [no] : 
		"""
#		paramInputOrder = [ 'output', 'apix', 'kv', 'cs', 'ac', 'boxsize', 'do_EPA','mdef_aveN',
#			'resL', 'resH', 'defS', 'astm','input','phase_shift_L','phase_shift_H','phase_shift_S']
		paramInputOrder = [ 'output', 'apix', 'kv', 'cs', 'ac', 'boxsize', 'do_EPA', 'do_Hres_ref', 'do_mdef_refine', 'mdef_aveN',
			'resL', 'resH', 'defL', 'defH', 'defS', 'astm','input']
                # finalize paramInputOrder
                if self.params['shift_phase']:
                        paramInputOrder.extend(['phase_shift_H','phase_shift_L','phase_shift_S'])
#                paramInputOrder.append('expert_opts')
#                paramInputOrder.append('newline')


		#get Defocus in Angstroms
		self.ctfvalues = {}
		if self.params['nominal'] is not None:
			nominal = abs(self.params['nominal']*1e4)
			apDisplay.printWarning("overriding CTF value with user nominal value %.1f A"%(nominal))
			ctfvalue = None
			bestdef = nominal
		else:
			nominal = abs(imgdata['scope']['defocus']*-1.0e10)
			ctfvalue = ctfdb.getBestCtfByResolution(imgdata)
			if ctfvalue is not None:
				"""
				## CTFFIND V3.5 (7-March-2012) prefers the smaller of the two values for astigmatic images
				I found that say you have an image with 1.1um and 1.5um defocus astigmatism. If you give 
				CTFFIND the average value of 1.3um for the defocus and 0.4um astig (dast) then it will 
				try to fit 1.3um and 1.8um, so you need to give it the minimum value (1.1um) for it to 
				fit 1.1um and 1.5um.
				"""
				bestdef = min(ctfvalue['defocus1'],ctfvalue['defocus2'])*1.0e10
			else:
				bestdef = nominal
		if ctfvalue is not None and self.params['bestdb'] is True:
			bestampcontrast = round(ctfvalue['amplitude_contrast'],3)
			beststigdiff = round(abs(ctfvalue['defocus1'] - ctfvalue['defocus2'])*1e10,1)
		else:
			bestampcontrast = self.params['ampcontrast']
			beststigdiff = self.params['dast']*10000.

		imageresmax = self.params['resmax']
		if ctfvalue is not None and self.params['bestdb'] is True:
			### set res max from resolution_80_percent
			gmean = (ctfvalue['resolution_80_percent']*ctfvalue['resolution_50_percent']*self.params['resmax'])**(1/3.)
			if gmean < self.params['resmin']*0.9:
				# replace only if valid Issue #3291
				imageresmax = round(gmean,2)
				apDisplay.printColor("Setting resmax to the geometric mean of resolution values", "purple")

		# dstep is the physical detector pixel size
		apix = apDatabase.getPixelSize(imgdata)
		# inputparams defocii and astig are in Angstroms

		# may be gain/dark corrected movie that has been binned
		origpath, binning = self.getOriginalPathAndBinning(imgdata)

		# ddstack might be binned.
		apix *= binning

		inputparams = {
			'orig': origpath,
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'apix': apix,
			'kv': imgdata['scope']['high tension']/1000.0,			
			'cs': self.params['cs'],
			'ac': bestampcontrast,
			'boxsize': self.params['fieldsize'],
			'resL': self.params['resmin'],
			'resH': imageresmax,
			'defS': self.params['defstep']*10000, #round(defocus/32.0, 1),
			'astm': beststigdiff,
			'do_EPA' : self.params['do_EPA'],
			'do_Hres_ref' : self.params['do_Hres_ref'],
			'mdef_aveN' : self.params['mdef_aveN'],
			'do_mdef_refine' : 0,
#			'phase': 'no', # this is a secondary amp contrast term for phase plates
#			'newline': '\n',
			'phase_shift_H': self.params['max_phase_shift'],
			'phase_shift_L': self.params['min_phase_shift'],
			'phase_shift_S': self.params['phase_search_step']
		}


	

		defrange = self.params['defstep'] * self.params['numstep'] * 1e4 ## do 25 steps in either direction # in angstrum
		inputparams['defL']= round(bestdef-defrange, 1) #in angstrom 
		if inputparams['defL'] < 0:
			apDisplay.printWarning("Defocus minimum is less than zero")
			inputparams['defL'] = inputparams['defS']
		inputparams['defH']= round(bestdef+defrange, 1) #in angstrom
		apDisplay.printColor("Defocus search range: %d A to %d A (%.2f to %.2f um)"
			%(inputparams['defL'], inputparams['defH'], 
			inputparams['defL']*1e-4, inputparams['defH']*1e-4), "cyan")

		### secondary lock check right before it starts on the real part
		if self.params['parallel'] and os.path.isfile(apDisplay.short(imgdata['filename'])+".mrc"):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return
		### create local link to image
		if not os.path.exists(inputparams['input']):
			os.symlink(inputparams['orig'], inputparams['input'])

		if os.path.isfile(inputparams['output']):
#			# program crashes if this file exists
			apFile.removeFile(inputparams['output'])

		t0 = time.time()
		apDisplay.printMsg("running ctf estimation at "+time.asctime())
		for paramName in paramInputOrder:
			apDisplay.printColor("%s = %s"%(paramName,inputparams[paramName]),"magenta")
#		ctfprogproc = subprocess.Popen(self.ctfprgmexe, shell=True, stdin=subprocess.PIPE,)		
#		apDisplay.printColor(self.ctfprgmexe, "magenta")

		gctfcommandstring = ''
		for paramName in paramInputOrder:
		#	apDisplay.printColor(inputparams[paramName],"magenta")

		#	ctfprogproc.stdin.write(str(inputparams[paramName])+'\n')
			
			if paramName == 'input':
		#		ctfprogproc.stdin.write((' '+str(inputparams[paramName])+' ').strip("\n"))
		#		apDisplay.printColor((' '+str(inputparams[paramName])+' ').strip("\n"),"magenta")
				gctfcommandstring = gctfcommandstring + (' '+str(inputparams[paramName])+' ')

			elif paramName == 'output':
				continue
			elif type(inputparams[paramName]) == type(True):
				gctfcommandstring += ' --'+str(paramName)
			else:
		#		ctfprogproc.stdin.write((' --'+str(paramName)+' '+str(inputparams[paramName])).strip("\n"))
		#		apDisplay.printColor((' --'+str(paramName)+' '+str(inputparams[paramName])).strip("\n"),"magenta")
				gctfcommandstring = gctfcommandstring + (' --'+str(paramName)+' '+str(inputparams[paramName])+' ')
			
		#		ctfprogproc.stdin.write(gctfcommandstring)
		apDisplay.printColor(gctfcommandstring,"magenta")

		ctfprogproc = subprocess.Popen(self.ctfprgmexe+gctfcommandstring, shell=True, stdin=subprocess.PIPE,)
                apDisplay.printColor(self.ctfprgmexe+gctfcommandstring, "magenta")
		ctfprogproc.stdin.write(gctfcommandstring)
		apDisplay.printColor(gctfcommandstring,"magenta")

		ctfprogproc.communicate()
		tdiff = time.time()-t0
		apDisplay.printMsg("ctf estimation completed in "+apDisplay.timeString(tdiff))
		#if tdiff < 1.0:
		#	apDisplay.printError("Failed to run CTFFIND4 program...")

		### cannot run ctffind_plot_results.sh on CentOS 6
		# This script requires gnuplot version >= 4.6, but you have version 4.2

		### parse ctf estimation output
		self.ctfvalues = {}
		#ctfproglog = apDisplay.short(imgdata['filename'])+"-pow.txt"		
		ctfproglog = apDisplay.short(imgdata['filename'])+"_gctf.log"		

		print 'ctfproglog = ',ctfproglog
		apDisplay.printMsg("reading %s"%(ctfproglog))
		logf = open(ctfproglog, "r")
		print 'current path is ',os.getcwd()
		for line in logf:
			sline = line.strip()
			if (re.match('Defocus_U',sline)):
				sline = next(logf).strip()
				bits = sline.split()

				if len(bits) == 6:

					self.ctfvalues = {

						'imagenum' : int(1),
						'defocus2' : float(bits[0])*1e-10,
						'defocus1' : float(bits[1])*1e-10,
						'angle_astigmatism' : float(bits[2]) + 90,  # see bug #4047 for astig conversion
						'amplitude_contrast' : inputparams['ac'],
						'cross_correlation' : float(bits[3]),
						'do_EPA' : inputparams['do_EPA'],
						'defocusinit' : bestdef*1e-10,
						'cs' : self.params['cs'],
						'volts' : imgdata['scope']['high tension'],
						'confidence' : float(bits[3]),
						'confidence_d' : round(math.sqrt(abs(float(bits[3]))), 5),
						'extra_phase_shift':  float(0)

					}

				elif len(bits) == 7:

					self.ctfvalues = {

						'imagenum' : int(1),
						'defocus2' : float(bits[0])*1e-10,
						'defocus1' : float(bits[1])*1e-10,
						'angle_astigmatism' : float(bits[2]) + 90,  # see bug #4047 for astig conversion
						'amplitude_contrast' : inputparams['ac'],
						'cross_correlation' : float(bits[4]),
						'do_EPA' : inputparams['do_EPA'],
						'defocusinit' : bestdef*1e-10,
						'cs' : self.params['cs'],
						'volts' : imgdata['scope']['high tension'],
						'confidence' : float(bits[4]),
						'confidence_d' : round(math.sqrt(abs(float(bits[4]))), 5),
						'extra_phase_shift': round(math.radians(float(bits[3])),5), # radians

					}

				

				print 'defocus2 = '+str(self.ctfvalues['defocus2'])
				print 'defocus1 = '+str(self.ctfvalues['defocus1'])
				print 'angle_astigmatism = '+str(self.ctfvalues['angle_astigmatism'])
	
			if sline.startswith('Resolution'):
				bits = sline.split()
				self.ctfvalues['ctffind4_resolution'] = float(bits[6])
				#print 'ctffind4_resolution = '+self.ctfvalues['ctffind4_resolution']

		if len(self.ctfvalues.keys()) == 0:
			#
			apDisplay.printError("GCTF program did not produce valid results in the log file")
		sourcectffile = apDisplay.short(imgdata['filename'])+'.ctf'
		
		targetmrcfile = self.params['rundir']+'/'+imgdata['filename']
		targetmrcfile = apDisplay.short(imgdata['filename'])
		targetmrcfile = targetmrcfile + '-pow.mrc'

		shutil.move(sourcectffile,targetmrcfile)
		#convert powerspectra to JPEG
		outputjpgbase = apDisplay.short(imgdata['filename'])+"-pow.jpg"
		self.lastjpg = outputjpgbase
		outputjpg = os.path.join(self.powerspecdir, self.lastjpg)

		powspec = apImage.mrcToArray(inputparams['output'])
		apImage.arrayToJpeg(powspec, outputjpg)
		shutil.move(inputparams['output'], os.path.join(self.powerspecdir, inputparams['output']))
		self.ctfvalues['graph1'] = outputjpg

		#apFile.removeFile(inputparams['input'])

		return

	#======================
	def commitToDatabase(self, imgdata):
		import pprint

		self.insertCtfRun(imgdata)
	
		pprint.pprint('***********insertCTFRUN**************')
		pprint.pprint((imgdata))
		pprint.pprint((self.ctfvalues))
		pprint.pprint((self.ctfrun))
		pprint.pprint((self.params['rundir']))

	
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])

	#======================
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApCtfFind4ParamsData()
		copyparamlist = ('ampcontrast','fieldsize','cs','bestdb','resmin','defstep')
		for p in copyparamlist:
			if p in self.params:
				paramq[p] = self.params[p]


			
		# create an acerun object
		runq = appiondata.ApAceRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runnames = runq.query(results=1)

		if (runnames):
			prevrun = runnames[0]
			if not (prevrun['ctffind4_params'] == paramq):
				for i in prevrun['ctffind4_params']:
					if prevrun['ctffind4_params'][i] != paramq[i]:
						# float value such as cs of 4.1 is not quite equal
						if type(paramq[i]) == type(1.0) and abs(prevrun['ctffind4_params'][i]-paramq[i]) < 0.00001:
							continue
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
						apDisplay.printError("All parameters for a single CTF estimation run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = prevrun
			return False

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
		# if no run entry exists, insert new run entry into db
		runq['ctffind4_params'] = paramq
		runq.insert()
		self.ctfrun = runq
		return True

	def getOriginalPathAndBinning(self,imgdata):
		if self.params['ddstackid'] is None:
			origPath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
			binning = 1
		else:
			self.dd = apDDprocess.DDStackProcessing()
			self.dd.setDDStackRun(self.params['ddstackid'])
			self.dd.setImageData(imgdata)
			self.ddstackrun = self.dd.getDDStackRun()
			self.ddstackpath = self.ddstackrun['path']['path']
			if not imgdata['camera']['align frames']:
				# ddstack of the ddstack may be different from the source image
				binning = self.ddstackrun['params']['bin']
				source_imgdata = imgdata
			else:
				# but should be the same as the aligned image
				binning = 1
				pair = self.dd.getAlignImagePairData(self.ddstackrun,False)
				source_imgdata = pair['source']
			origPath = os.path.join(self.ddstackpath,source_imgdata['filename']+"_st.mrc")
		return origPath, binning

if __name__ == '__main__':
	imgLoop = gctfEstimateLoop()
	imgLoop.run()

