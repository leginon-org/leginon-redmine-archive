#!/usr/bin/env python
#
import os
import time
import glob
import math
import cPickle
import shutil
import subprocess
from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import apImage
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apProject
from appionlib import proc2dLib
from appionlib import apAWS
from pyami import mrc
import sinedon
import MySQLdb

#=====================
#=====================
class RelionMaxLikeScript(appionScript.AppionScript):


	execFile = 'relion_refine_mpi'
	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--numpart", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		self.parser.add_option("--partDiam", dest="partdiam", type="int",
			help="Particle diameter in Angstroms", metavar="#")
		self.parser.add_option("--maxIter", "--max-iter", dest="maxiter", type="int", default=30,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--numRef", "--num-ref", dest="numrefs", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--angStep", "--angle-step", dest="psistep", type="int", default=12,
			help="In-plane rotation sampling step (degrees)", metavar="#")
		self.parser.add_option("--tau", dest="tau", type="float", default=1,
			help="Tau2 Fudge Factor (> 1)", metavar="#")
		self.parser.add_option("--correctnorm",dest="correctnorm",default=False,
			action="store_true", help="Perform normalisation error correction")

		self.parser.add_option("--invert", dest='invert', default=False,
			action="store_true", help="Invert before alignment")
		self.parser.add_option("--flat", "--flatten-solvent", dest='flattensolvent', default=False,
			action="store_true", help="Flatten Solvent in References")
		self.parser.add_option("--zero_mask", "--zero_mask", dest="zero_mask", default=False,
			action="store_true", help="Mask surrounding background in particles to zero (by default the solvent area is filled with random noise)", metavar="#")

		self.parser.add_option("--nompi", dest='usempi', default=True,
			action="store_false", help="Disable MPI and run on single host")
		# Job parameters that the remotehost need
		self.parser.add_option("--nodes", dest="nodes", type="int", default=1,
			help="Number of nodes requested for multi-node capable tasks", metavar="#")
		self.parser.add_option("--ppn", dest="ppn", type="int", default=1,
			help="Minimum Processors per node", metavar="#")
		self.parser.add_option("--mem", dest="mem", type="int", default=4,
			help="Maximum memory per node (in GB)", metavar="#")
		self.parser.add_option("--mpinodes", dest="mpinodes", type=int, default=1,
			help="Number of nodes used for the entire job.", metavar="#")
		self.parser.add_option("--mpiprocs", dest="mpiprocs", type=int, default=1,
			help="Number of processors allocated for a subjob. For memory intensive jobs, decrease this value.", metavar="#")
		self.parser.add_option("--mpithreads", dest="mpithreads", type=int, default=1,
			help="Number of threads to generate per processor. For memory intensive jobs, increase this value.", metavar="#")
		self.parser.add_option("--mpimem", dest="mpimem", type=int, default=1,
			help="Amount of memory (Gb) to allocate per thread. Increase this value for memory intensive jobs. ", metavar="#")
		self.parser.add_option("--walltime", dest="walltime", type=int, default=24,
			help="Maximum walltime in hours", metavar="#")
		self.parser.add_option('--cput', dest='cput', type=int, default=None)

		self.parser.add_option('--usegpu', dest='usegpu',action="store_true",default=False)
		self.parser.add_option('--numgpus', dest='numgpus',type=float,default=0)
		self.parser.add_option('--preread_images', dest='preread_images',action="store_true",default=False)
		self.parser.add_option('--instancetype',dest='instancetype',type=str,default=None)
		self.parser.add_option('--spotprice',dest='spotprice',type=float,default=0)
		self.parser.add_option('--mode',dest='mode',type=str,default='appion')
		self.parser.add_option('--recenter',dest='recenter',action="store_true",default=False,
			help="Recenter particles; relion mode only.")
		self.parser.add_option('--normalize',dest='normalize',action="store_true",default=False,
			help="Normalize particles; relion mode only.")	
		self.parser.add_option('--useaws',dest='useaws',action="store_true",default=False,
			help="Use AWS cloud instance.")


	#=====================
	def checkConflicts(self):
		self.setInstanceTypes()
		if self.params['numgpus'] and type(self.params['numgpus']) != int:
			apDisplay.printError("ERROR: --numgpus parameter must be an integer greater than or equal to zero.")
		if self.params['numgpus'] and self.params['numgpus'] < 0:
			apDisplay.printError("ERROR: --numgpus parameter must be an integer greater than or equal to zero.")
		if self.params['instancetype'] is None and self.params['useaws']:
			apDisplay.printError("No AWS instance specified. Choose from p2.xlarge (1 GPU, $0.90/hour), p2.8xlarge (8 GPU's, $7.20/hour), p2.16xlarge (16 GPU's, $14.4/hour), g3.8xlarge (2 GPU's, $2.28/hour), g3.16xlarge (4 GPU's, $4.56/hour).")


		if self.params['spotprice'] < 0:
			apDisplay.printError("Spot price set to %s, but must be greater than zero. To use on-demand pricing, do not use --spotprice flag or set spotprice to zero." %(self.params['spotprice']))

		# instanceinfo is in format ('<instancename>,<spotprice>) i.e. (str,float)
		for instanceinfo in self.instancetypes:
			if (self.params['instancetype'] == instanceinfo[0]) and (self.params['spotprice'] > instanceinfo[1]):
				apDisplay.printColor("WARNING: Spot price for %s instance set to %s/hour when on-demand price is %s/hour; spot price may exceed on-demand price in rare circumstances."%(instance[0],(self.params['spotprice']),str(instance[1])))

		'''
		if self.params['instancetype'] == 'p2.xlarge' and self.params['spotprice'] > 0.9:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $0.90/hour; spot price may exceed on-demand price in rare circumstances.")

		if self.params['instancetype'] == 'p2.8xlarge' and self.params['spotprice'] > 7.20:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $7.20/hour; spot price may exceed on-demand price in rare circumstances.")


		if self.params['instancetype'] == 'p2.16xlarge' and self.params['spotprice'] > 14.40:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $14.40/hour; spot price may exceed on-demand price in rare circumstances.")


		if self.params['instancetype'] == 'g3.8xlarge' and self.params['spotprice'] > 2.28:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $2.28/hour; spot price may exceed on-demand price in rare circumstances.")



		if self.params['instancetype'] == 'g3.16xlarge' and self.params['spotprice'] > 4.56:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $4.56/hour; spot price may exceed on-demand price in rare circumstances.")


		if self.params['instancetype'] == 'p3.2xlarge' and self.params['spotprice'] > 3.06:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $3.06/hour; spot price may exceed on-demand price in rare circumstances.")

		if self.params['instancetype'] == 'p3.8xlarge' and self.params['spotprice'] > 12.24:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $12.24/hour; spot price may exceed on-demand price in rare circumstances.")

		if self.params['instancetype'] == 'p3.16xlarge' and self.params['spotprice'] > 24.48:
			apDisplay.printColor("WARNING: Spot price set to %s/hour when on-demand price is $24.48/hour; spot price may exceed on-demand price in rare circumstances.")
		'''
		

		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		self.projectid = apProject.getProjectIdFromStackId(self.params['stackid'])
		if self.params['numrefs'] is None:
			apDisplay.printError("a number of classes was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		a = appiondata.ApRunsInStackData(stack=self.stackdata)
		stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		print("mode is",self.params['mode'])
		# check for virtual stack
		self.params['virtualdata'] = None
		if self.params['mode'] == 'appion':
			if not os.path.isfile(stackfile):
				vstackdata = apStack.getVirtualStackParticlesFromId(self.params['stackid'])
				npart = len(vstackdata['particles'])
				self.params['virtualdata'] = vstackdata
			else:
				npart = apFile.numImagesInStack(stackfile)

			if self.params['numpart'] > npart:
				apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
					+" than available "+str(apFile.numImagesInStack(stackfile)))

		self.boxsize = apStack.getStackBoxsize(self.params['stackid'])
		self.clipsize = int(math.floor(self.boxsize/float(self.params['bin']*2)))*2
		if self.params['clipsize'] is not None:
			if self.params['clipsize'] > self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']
		
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)

		if self.params['usempi'] is True:
			#self.mpirun = self.checkMPI()
			self.mpirun = 'mpirun'
			if self.mpirun is None:
				apDisplay.printError("There is no MPI installed")
			if self.params['nproc'] is None:
				self.params['nproc'] = self.params['mpinodes']*self.params['mpiprocs']

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun", die=True)
		if mpiexe is None:
			return None
		relionexe = apParam.getExecPath(self.execFile, die=True)
		if relionexe is None:
			return None
		lddcmd = "ldd "+relionexe+" | grep mpi"
		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		lines = proc.stdout.readlines()
		print "lines=", lines
		if lines and len(lines) > 0:
			return mpiexe

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "maxlike-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		newdict = self.params.copy()
		newdict.update(self.stack)
		cPickle.dump(newdict, pf)
		pf.close()

	#=====================
	def insertMaxLikeJob(self):
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = self.params['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		maxjobdatas = maxjobq.query(results=1)
		if maxjobdatas:
			alignrunq = appiondata.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		maxjobq['REF|projectdata|projects|project'] = self.projectid
		maxjobq['timestamp'] = self.timestamp
		maxjobq['finished'] = False
		maxjobq['hidden'] = False
		if self.params['commit'] is True:
			maxjobq.insert()
		self.params['maxlikejobid'] = maxjobq.dbid
		print "self.params['maxlikejobid']",self.params['maxlikejobid']
		return

	#=====================
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appiondata')
		dbc = MySQLdb.Connect(**config)
		dbc.autocommit(True)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApMaxLikeJobData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['maxlikejobid'])+"'"
		)
		cursor.execute(query)
		cursor.close()
		dbc.close()

	#=====================
	def runUploadScript(self):
		if self.params['commit'] is False:
			return
		uploadcmd = "uploadRelion2DMaxlikeAlign.py "
		uploadcmd += " -p %d "%(self.projectid)
		uploadcmd += " -j %s "%(self.params['maxlikejobid'])
		uploadcmd += " -R %s "%(self.params['rundir'])
		uploadcmd += " -n %s "%(self.params['runname'])

		if self.params['mode'] == 'relion':
			uploadcmd += " --mode %s "%(self.params['mode'])
		print uploadcmd
		proc = subprocess.Popen(uploadcmd, shell=True)
		proc.communicate()

	#=====================
	def estimateIterTime(self, nprocs):
		##FIXME
		return 1
		secperiter = 0.12037
		### get num processors
		print '1. numprocs is = '+str(nproc)
		calctime = (
			(self.params['numpart']/1000.0)
			*self.params['numrefs']
			*(self.stack['boxsize']/self.params['bin'])**2
			/self.params['psistep']
			/float(nproc)
			*secperiter
		)
		self.params['estimatedtime'] = calctime
		apDisplay.printColor("Estimated first iteration time: "+apDisplay.timeString(calctime), "purple")

	#=====================
	def estimateMemPerProc(self):
		classes = self.params['numrefs']
		boxsize = self.stack['boxsize']/self.params['bin']
		# bin 2 / 96 clip; angstep 5 ; numref 7 ; numpart 538 --> 0.108 Gb
		# bin 2 / 96 clip; angstep 5 ; numref 3 ; numpart 538 --> 0.104 Gb
		# bin 4 / 48 clip; angstep 5 ; numref 7 ; numpart 538 --> 0.107 Gb
		# bin 1 / 192 clip; angstep 15 ; numref 2 ; numpart 538 --> 0.104 Gb
		# bin 1 / 160 clip; angstep 15 ; numref 2 ; numpart 538 --> 0.104 Gb
		# bin 1 / 160 clip; angstep 15 ; numref 2 ; numpart 300 --> 0.103 Gb

	#=====================
	def writeRelionLog(self, text):
		f = open("relion.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n\n")
		f.close()

	#=====================
	def createReferenceStack(self):
		avgstack = "part"+self.timestamp+"_average.hed"
		apFile.removeStack(avgstack, warn=False)
		searchstr = "part"+self.timestamp+"_it*_classes.mrcs"
		classStackFiles = glob.glob(searchstr)
		classStackFiles.sort()
		fname = classStackFiles[-1]
		print("reading class averages from file %s"%(fname))
		refarray = mrc.read(fname)
		apImagicFile.writeImagic(refarray, avgstack)
		### create a average mrc
		avgdata = refarray.mean(0)
		apImage.arrayToMrc(avgdata, "average.mrc")
		return

	#=====================
	def relionPreProcessParticles(self):
		exename = 'relion_preprocess'
		preprocess_exename = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()

		preprocess_cmd = '%s --operate_on %s-complete_relion_stack.star --set_angpix %s --operate_out %s-preprocessed.star'%(preprocess_exename,self.stackname,self.params['apix'],self.stackname)

		if self.params['recenter']:
			preprocess_cmd+=' --recenter '
		if self.params['normalize']:
			preprocess_cmd+=' --norm --bg_radius %s '%(float(self.boxsize)/2)
		print("relion_preprocess command: ",preprocess_cmd)
		proc = subprocess.Popen(preprocess_cmd,shell=True,stdout=subprocess.PIPE)
		proc.wait()
		for line in proc.stdout:
			print(line)
		return

	def convertMrcsToImagic(self):
		assert self.relionstack
		assert self.params['localstack']
		print("RELION STACK: ",self.relionstack)
		print("IMAGIC STACK: ",self.params['localstack'])
		refarray = mrc.read(self.relionstack)
		apImagicFile.writeImagic(refarray,self.params['localstack'])
		print("Converted %s to Imagic format (%s)"%(self.relionstack,self.params['localstack']))

	#=====================
	def symlinkStack(self):
		if not os.path.isdir(os.path.join(self.params['rundir'],'mrcs')):
			os.symlink(os.path.join(self.stackpath,"mrcs"),os.path.join(self.params['rundir'],'mrcs'))

		if not os.path.isfile(self.params['rundir']+'/'+self.stackname+'-complete_relion_stack.star'):
			os.symlink(self.stackpath+'/'+self.stackname+'-complete_relion_stack.star',self.params['rundir']+'/'+self.stackname+'-complete_relion_stack.star')

	#=====================
	# set corresponding instance type and on-demand price for spot price messaging
	# this is according to us-east-1 GPU instances, other regions may differ
	# format is ('<instancename>',<on-demand price>,<numgpus>) i.e. (str,float,int)
	def setInstanceTypes(self):
		
		self.instancetypes = [ ('p2.xlarge',0.90,1),
				       ('p2.8xlarge',7.20,8),
				       ('p2.16xlarge',14.4,16),
				       ('g3.8xlarge',2.28,2),
				       ('g3.16xlarge',4.56,4),
				       ('p3.2xlarge',3.06,1),
				       ('p3.8xlarge',12.24,4),
				       ('p3.16xlarge',24.48,8) ]

	#=====================
	# set number of gpu's

	def setNumGpus(self):
		pass
		

	#=====================
	def start(self):
		self.setInstanceTypes()
		self.insertMaxLikeJob()
		self.stack = {}
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.params['apix'] = self.stack['apix']
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		if self.params['virtualdata'] is not None:
			self.stack['file'] = self.params['virtualdata']['filename']
		else:
			self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		#self.estimateIterTime(nprocs)
		self.dumpParameters()


		# if in appion stack mode, run proc2d

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")

		if self.params['mode'] == 'appion':
			a = proc2dLib.RunProc2d()
			a.setValue('infile',self.stack['file'])
			a.setValue('outfile',self.params['localstack'])
			a.setValue('apix',self.stack['apix'])
			a.setValue('bin',self.params['bin'])
			a.setValue('last',self.params['numpart']-1)
			a.setValue('append',False)
			### pixlimit and normalization are required parameters for RELION
			if self.params['correctnorm'] is True:
				a.setValue('pixlimit',4.49)
			a.setValue('normalizemethod','edgenorm')

			if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
				a.setValue('lowpass',self.params['lowpass'])
			if self.params['highpass'] is not None and self.params['highpass'] > 1:
				a.setValue('highpass',self.params['highpass'])
			if self.params['invert'] is True:
				a.setValue('inverted',True)

			if self.params['virtualdata'] is not None:
				vparts = self.params['virtualdata']['particles']
				plist = [int(p['particleNumber'])-1 for p in vparts]
				a.setValue('list',plist)

			# clip not yet implemented
			if self.params['clipsize'] is not None:
				clipsize = int(self.clipsize)*self.params['bin']
				if clipsize % 2 == 1:
					clipsize += 1 ### making sure that clipped boxsize is even
				a.setValue('clip',clipsize)

			if self.params['virtualdata'] is not None:
				vparts = self.params['virtualdata']['particles']
				plist = [int(p['particleNumber'])-1 for p in vparts]
				a.setValue('list',plist)

			a.run()
			print('done with proc2d')
			

		#if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
		#	apDisplay.printError("Missing particles in stack")

		### setup Relion command
		aligntime = time.time()

		if self.params['mode'] == 'appion':
			relionopts =  ( " "+" --i %s "%(self.params['localstack']))
			relionopts += ( " --angpix %.4f "%(self.stack['apix']*self.params['bin']))
		elif self.params['mode'] == 'relion':
			self.stackpath = self.stackdata['path']['path']
			self.stackname = self.stackpath.split('/')[-1]
			# if doing preprocessing, use the output mrcs stack as input to relion
			self.symlinkStack()

			relionstarfile = os.path.join(self.params['rundir'],self.stackname+'-preprocessed.star')
			self.relionstack = os.path.join(self.params['rundir'],self.stackname+'-preprocessed.mrcs')
			apDisplay.printMsg("Performing preprocessing ...")
			self.relionPreProcessParticles()
			apDisplay.printMsg("Preprocessing complete.")

			# relion2 outputs files from relion_preprocess as filename.mrcs.mrcs,  to filename.mrcs
			if os.path.isfile(os.path.join(self.params['rundir'],self.stackname+'-preprocessed.mrcs.mrcs')):
				shutil.move(os.path.join(self.params['rundir'],self.stackname+'-preprocessed.mrcs.mrcs'),os.path.join(self.params['rundir'],self.stackname+'-preprocessed.mrcs'))
			self.convertMrcsToImagic()
			self.imagicstack = self.params['localstack']

			# Delete .mrcs stack to reduce rsync downloading time and data transfer costs. Maybe make this a flag
			os.remove(self.relionstack)
			os.unlink(os.path.join(self.params['rundir'],self.stackname+'-complete_relion_stack.star'))
			os.unlink(os.path.join(self.params['rundir'],'mrcs'))
			relionopts =  ( " --i %s "%(self.imagicstack))
			relionopts += ( " --angpix %.4f "%(self.stack['apix']))

		relionopts += ( " "
			+" --o %s "%(os.path.join(self.params['rundir'], "part"+self.timestamp))
			+" --iter %d "%(self.params['maxiter'])
			+" --K %d "%(self.params['numrefs'])
			+" --psi_step %d "%(self.params['psistep'])
			+" --tau2_fudge %.1f "%(self.params['tau'])
			+" --particle_diameter %.1f "%(self.params['partdiam'])
		)

		relionopts += " --pool 100 "
		relionopts += " --offset_range 5 "
		relionopts += " --offset_step 2 "
		relionopts += " --dont_combine_weights_via_disc "
		relionopts += " --scale "


		if self.params['usegpu'] is True:
			relionopts += " --gpu "
		if self.params['flattensolvent'] is True:
			relionopts += " --flatten_solvent "
		if self.params['zero_mask'] is True:
			relionopts += " --zero_mask "
		if self.params['correctnorm'] is True:
			relionopts += " --norm "
		else:
			relionopts += " --dont_check_norm "

		if self.params['preread_images'] is True:
			relionopts += " --preread_images "

		if self.params['numgpus']:
			runcmd = self.mpirun+" -n "+str(numgpus+1)
		if self.params['usempi'] is True:
			relionexe = "relion_refine_mpi"
			relionopts += " --j %d "%(self.params['mpithreads'])

			if self.params['numgpus'] > 0:
				runcmd = self.mpirun+" -np "+str(self.params['numgpus']+1)+" "+relionexe+" "+relionopts
			else:	
				### find number of processors
				nproc = self.params['mpiprocs'] * self.params['mpinodes']
				runcmd = self.mpirun+" -np "+str(nproc)+" "+relionexe+" "+relionopts
		else:
			relionexe = apParam.getExecPath("relion_refine", die=True)
			runcmd = relionexe+" "+relionopts
		#relionexe = "relion_refine_mpi"
		#runcmd = relionexe+" "
		self.writeRelionLog(runcmd)
		print("RUNCMD IS",runcmd)
		os.chdir(self.params['rundir'])
		print("CURRENT DIRECTORY: ",os.getcwd())

		if self.params['useaws']:
			apAWS.relion_refine_mpi(runcmd,instancetype=self.params['instancetype'],spotprice=self.params['spotprice'],symlinks=True)

		else:

			self.outdir = os.path.join(self.params['rundir'], "part"+self.timestamp)
			mkdircmd = 'mkdir -p %s'%(self.outdir)
			if not os.path.isdir(self.outdir):
				os.mkdir(self.outdir)

			apParam.runCmd(runcmd, package="RELION", verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### minor post-processing
		self.createReferenceStack()
		self.dumpParameters()
		self.runUploadScript()

#=====================
if __name__ == "__main__":
	maxLike = RelionMaxLikeScript()
	maxLike.start()
	maxLike.close()



