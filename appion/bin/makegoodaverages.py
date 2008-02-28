#!/usr/bin/python -O

#python
import os
import math
import sys
import time
import cPickle
#scipy
import numpy
#eman
import EMAN
#db
import sinedon
import MySQLdb
#appion
import apDB
import appionData
import apDisplay
import apStack
import apEulerCalc
import appionScript
import apEulerJump
apdb=apDB.apdb

def getParticleInfo(reconid, iteration):
	"""
	Get all particle data for given recon and iteration
	"""
	refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)
	
	refineq=appionData.ApRefinementData()
	refineq['refinementRun']=refinerundata
	refineq['iteration']=iteration
	refinedata=apdb.query(refineq, results=1)
	
	refineparticleq=appionData.ApParticleClassificationData()
	refineparticleq['refinement']=refinedata[0]
	t0 = time.time()
	apDisplay.printMsg("querying particles on "+time.asctime())
	refineparticledata = apdb.query(refineparticleq)
	apDisplay.printMsg("received "+str(len(refineparticledata))+" particles in "+apDisplay.timeString(time.time()-t0))
	return (refineparticledata)

def determineClasses(particles):
	"""Takes refineparticledata and returns a dictionary of classes"""
	apDisplay.printMsg("sorting refineparticledata into classes")
	t0 = time.time()
	classes={}
	class_stats={}
	quality=numpy.zeros(len(particles))
	for ptcl in range(0,len(particles)):
		quality[ptcl]=particles[ptcl]['quality_factor']
		key=particles[ptcl]['eulers'].dbid
		if key not in classes.keys():
			classes[key]={}
			classes[key]['particles']=[]
		classes[key]['euler']=particles[ptcl]['eulers']
		classes[key]['particles'].append(particles[ptcl])
	class_stats['meanquality']=quality.mean()
	class_stats['stdquality']=quality.std()
	class_stats['max']=quality.max()
	class_stats['min']=quality.min()
	### print stats
	print "-- quality factor stats --"
	apDisplay.printMsg("mean/std :: "+str(round(class_stats['meanquality'],2))+" +/- "
		+str(round(class_stats['stdquality'],2)))
	apDisplay.printMsg("min/max  :: "+str(round(class_stats['min'],2))+" <> "
		+str(round(class_stats['max'],2)))
	apDisplay.printMsg("finished sorting in "+apDisplay.timeString(time.time()-t0))
	return classes, class_stats

def makeClassAverages(lst, outputstack, classdata, params):
	#align images in class
	images=EMAN.readImages(lst,-1,-1,0)
	for image in images:
		image.rotateAndTranslate()
		if image.isFlipped():
			image.hFlip()

	#make class average
	avg=EMAN.EMData()
	avg.makeMedian(images)
	
	#write class average
	e = EMAN.Euler()
	alt = classdata['euler']['euler1']*math.pi/180
	az = classdata['euler']['euler2']*math.pi/180
	phi = classdata['euler']['euler3']*math.pi/180
	e.setAngle(alt,az,phi)
	avg.setRAlign(e)
	avg.setNImg(len(images))
	avg.applyMask(params['mask'],0)
	avg.writeImage(outputstack,-1)
	
def makeEvenOddClasses(lst,classdata,params):
	f=open(lst,'r')
	f.readline()
	lines=f.readlines()
	f.close()
	even=open('even.lst','w')
	odd=open('odd.lst','w')
	even.write("#LST\n")
	odd.write("#LST\n")
	neven=0
	nodd=0
	for line in range(0,len(lines)):
		if line%2:
			nodd+=1
			odd.write(lines[line])
		else:
			neven+=1
			even.write(lines[line])
	even.close()
	odd.close()
	evenstack=os.path.splitext(params['outputstack'])[0]+'.even.hed'
	oddstack=os.path.splitext(params['outputstack'])[0]+'.odd.hed'
	
	if neven>0:
		makeClassAverages('even.lst',evenstack,classdata,params)
	if nodd>0:
		makeClassAverages('odd.lst',oddstack,classdata,params)
	os.remove('even.lst')
	os.remove('odd.lst')

def removePtclsByLst(rejectlst, params):
	"""
	Removes particles by reading a list of particle numbers generated externally.

	Requirements:
		the input file has one particle per line 
		the first piece of data is the particle number from the db
	"""
	f=open(params['rejectlst'],'r')
	lines=f.readlines()
	f.close()
	for n in lines:
		words = n.split()
		rejectlst.append(int(words[0]))
	return rejectlst


#=====================
#=====================
class makeGoodAveragesScript(appionScript.AppionScript):

	#=====================
	def removePtclsByJumps(self, particles, rejectlst):
		eulerjump = apEulerJump.ApEulerJump()
		numparts = len(particles)
		apDisplay.printMsg("finding euler jumps for "+str(numparts)+" particles")
		### prepare file
		f = open('jumps.txt','w', 0666)
		f.write("#partnum\t")
		headerlist = ('mean', 'median', 'stdev', 'min', 'max')
		for key in headerlist:
			f.write(key+"\t")
		### start loop
		t0 = time.time()
		t1 = time.time()
		medians = []
		for ptcl in range(1, numparts+1):
			f.write('%d\t' % ptcl)
			jumpdata = eulerjump.getEulerJumpData(ptcl, self.params['reconid'])
			### no longer write individual jump values
			#f.write('%3.3f\t' % (dist))
			medians.append(jumpdata['median'])
			if jumpdata['median'] > self.params['avgjump']:
				rejectlst.append(ptcl)
			for key in headerlist:
				f.write("%3.4f\t" % (jumpdata[key]))
			if ptcl % 500 == 0:
				print ("particle=% 5d; median jump=% 3.2f, time=%s" % (ptcl,jumpdata['median'],
					apDisplay.timeString(time.time()-t1)))
				t1 = time.time()
				f.flush()
		apDisplay.printMsg("complete "+str(numparts)+" particles in "+apDisplay.timeString(time.time()-t0))
		### print stats
		print "-- median euler jumper stats --"
		medians = numpy.asarray(medians, dtype=numpy.float32)
		apDisplay.printMsg("mean/std :: "+str(round(medians.mean(),2))+" +/- "
			+str(round(medians.std(),2)))
		apDisplay.printMsg("min/max  :: "+str(round(medians.min(),2))+" <> "
			+str(round(medians.max(),2)))
		return rejectlst

	#=====================
	def removePtclsByQualityFactor(self, particles, rejectlst, cutoff):
		for ptcl in particles:
			if ptcl['quality_factor'] < cutoff:
				rejectlst.append(ptcl['particle']['particleNumber'])
		return rejectlst

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reconid=<DEF_id> --iter=<iter> --mask=<radius>\n\t "
			+"[ --stackname=<name> "
			+" --avgjump=<avg> --sigma=<sigma> --eotest ]")
		self.parser.add_option("-r", "--reconid", dest="reconid", type="int",
			help="reconstruction run id", metavar="INT")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="Mask radius in pixels", metavar="INT")
		self.parser.add_option("-i", "--iter", dest="iter", type="int",
			help="Final eulers applied to particles will come from this iteration", metavar="INT")
		self.parser.add_option("-s", "--sigma", dest="sigma", type="float",
			help="Number of std devs greater than the mean quality factor to include", metavar="FLOAT")
		self.parser.add_option("-j", "--avgjump", dest="avgjump", type="float",
			help="Throw away ptcls with median euler jumps greater than this", metavar="FLOAT")
		self.parser.add_option("--rejectlst", dest="rejectlst",
			help="Throw away ptcls in the specified text file. One particle per line with particle # from db", metavar="TEXT")
		self.parser.add_option("-n", "--stackname", dest="stackname", default="goodavgs.hed",
			help="Name of the stack to write the averages", metavar="TEXT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location of new class files", metavar="PATH")
		self.parser.add_option("--eotest", dest="eotest", default=False,
			action="store_true", help="make even and odd averages")

	#=====================
	def checkConflicts(self):
		if self.params['reconid'] is None:
			apDisplay.printError("enter a reconstruction ID from the database")
		if self.params['mask'] is None:
			apDisplay.printError("enter a mask radius")
		if self.params['iter'] is None:
			apDisplay.printError("enter an iteration for the final Eulers")
		self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])

	#=====================
	def setOutDir(self):
		reconid = self.params['reconid']
		refinerundata=apdb.direct_query(appionData.ApRefinementRunData, reconid)
		if not refinerundata:
			apDisplay.printError("reconid "+str(reconid)+" does not exist in the database")
		self.params['outdir'] = os.path.join(refinerundata['path']['path'], 'eulers')

	#=====================
	def start(self):
		self.params['outputstack'] = os.path.join(self.params['outdir'], self.params['stackname'])
		particles = getParticleInfo(self.params['reconid'], self.params['iter'])
		stackdata = particles[0]['particle']['stack']
		self.stack = os.path.join(stackdata['path']['path'], stackdata['name'])
		classes,cstats = determineClasses(particles)
		
		rejectlst=[]
		if self.params['sigma'] is not None:
			cutoff=cstats['meanquality']+self.params['sigma']*cstats['stdquality']
			print "Cutoff =",cutoff
			rejectlst = self.removePtclsByQualityFactor(particles, rejectlst, cutoff, self.params)
		if self.params['avgjump'] is not None:
			rejectlst = self.removePtclsByJumps(particles, rejectlst)
		if self.params['rejectlst']:
			rejectlst = removePtclsByLst(rejectlst, self.params)

		classkeys=classes.keys()
		classkeys.sort()
		classnum=0
		totalptcls=0
		
		reject=open('reject.lst','w')
		reject.write('#LST\n')
		print "Processing class"
		#loop through classes
		for key in classkeys:
			classnum+=1
			print classnum
			images=EMAN.EMData()

			#loop through particles in class
			f=open('tmp.lst','w')
			f.write('#LST\n')
			nptcls=0
			for ptcl in classes[key]['particles']:
				if ptcl['mirror']:
					mirror=1
				else:
					mirror=0
				rot=ptcl['inplane_rotation']
				rot=rot*math.pi/180
				if ptcl['particle']['particleNumber'] not in rejectlst:
					f.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
						stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
					totalptcls+=1
					nptcls+=1
				else:
					reject.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
						stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
				#if ptcl['quality_factor']>cstats['meanquality']+3*cstats['stdquality']:
				#	high.write('%d\t%s\t%f,\t%f,%f,%f,%d\n' % (ptcl['particle']['particleNumber']-1,
				#		stack,ptcl['quality_factor'],rot,ptcl['shiftx'],ptcl['shifty'],mirror))
			f.close()
			
			if nptcls<1:
				continue
			
			makeClassAverages('tmp.lst',self.params['outputstack'], classes[key], self.params)
			
			if self.params['eotest']:
				makeEvenOddClasses('tmp.lst',classes[key],self.params)
			os.remove('tmp.lst')
		reject.close()

#=====================
#=====================
if __name__ == '__main__':
	makegood = makeGoodAveragesScript()
	makegood.start()
	makegood.close()
