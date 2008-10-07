#Part of the new pyappion

#pythonlib
import os
import re
import sys
import math
import shutil
#appion
import appionData
import apParam
import apDisplay
import apDB
import apDatabase

appiondb = apDB.apdb
leginondb = apDB.db

def commitCtfValueToDatabase(imgdict, matlab, ctfvalue, params):
	imgname = imgdict['filename']
	matfile = imgname+".mrc.mat"
	#matfilepath = os.path.join(params['matdir'], matfile)

	imfile1 = os.path.join(params['tempdir'], "im1.png")
	imfile2 = os.path.join(params['tempdir'], "im2.png")
	#MATLAB NEEDS PATH BUT DATABASE NEEDS FILENAME
	opimfile1 = imgname+".mrc1.png"
	opimfile2 = imgname+".mrc2.png"
	opimfilepath1 = os.path.join(params['opimagedir'],opimfile1)
	opimfilepath2 = os.path.join(params['opimagedir'],opimfile2)

	shutil.copyfile(imfile1, opimfilepath1)
	shutil.copyfile(imfile2, opimfilepath2)
	#pymat.eval(matlab,"im1 = imread('"+imfile1+"');")
	#pymat.eval(matlab,"im2 = imread('"+imfile2+"');")
	#pymat.eval(matlab,"imwrite(im1,'"+opimfilepath1+"');")
	#pymat.eval(matlab,"imwrite(im2,'"+opimfilepath2+"');")

	insertCtfValue(imgdict, params, matfile, ctfvalue, opimfile1, opimfile2)

def printResults(params, nominal, ctfvalue):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfvalue[0]*1e6)
	if (params['stig']==1):
		defoc2 = float(ctfvalue[1]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfvalue[16])
	conf2 = float(ctfvalue[17])

	if(conf1 > 0 and conf2 > 0):
		totconf = math.sqrt(conf1*conf2)
	else:
		totconf = 0.0
	if (params['stig']==0):
		if nom1 != 0: pererror = (nom1-defoc1)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	else:
		avgdefoc = (defoc1+defoc2)/2.0
		if nom1 != 0: pererror = (nom1-avgdefoc)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus1","Defocus2","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,defoc2,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	return


def insertAceParams(imgdata, params):
	# first create an aceparam object
	aceparamq = appionData.ApAceParamsData()
	copyparamlist = ('display','stig','medium','edgethcarbon','edgethice',\
			 'pfcarbon','pfice','overlap','fieldsize','resamplefr','drange',\
			 'reprocess')
	for p in copyparamlist:
		if p in params:
			aceparamq[p] = params[p]
	
	# if nominal df is set, save override df to database, else don't set
	if params['nominal']:
		dfnom=-params['nominal']
		aceparamq['df_override']=dfnom
	
	# create an acerun object
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	
	runq['session']=imgdata['session'];

	# see if acerun already exists in the database
	runids = appiondb.query(runq, results=1)

	if (runids):
		if not (runids[0]['aceparams'] == aceparamq):
			for i in runids[0]['aceparams']:
				if runids[0]['aceparams'][i] != aceparamq[i]:
					apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
			apDisplay.printError("All parameters for a single ACE run must be identical! \n"+\
					     "please check your parameter settings.")
		return False

	#create path
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))

	# if no run entry exists, insert new run entry into db
	runq['aceparams']=aceparamq
	appiondb.insert(runq)

	return True

def insertCtfValue(imgdata, params, matfile, ctfvalue, opimfile1, opimfile2):
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	runq['session']=imgdata['session']

	acerun=appiondb.query(runq,results=1)


	print "Committing ctf parameters for",apDisplay.short(imgdata['filename']), "to database."

	ctfq = appionData.ApCtfData()
	ctfq['acerun']=acerun[0]
	ctfq['image']=imgdata
	ctfq['graph1']=opimfile1
	ctfq['graph2']=opimfile2
	ctfq['mat_file']=matfile
	ctfvaluelist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',\
		'noise1','noise2','noise3','noise4','envelope1','envelope2','envelope3','envelope4',\
		'lowercutoff','uppercutoff','snr','confidence','confidence_d')
	
	# test for failed ACE estimation
	# only set params if ACE was successfull
	if ctfvalue[0] != -1 :
		for i in range(len(ctfvaluelist)):
			ctfq[ ctfvaluelist[i] ] = ctfvalue[i]

	appiondb.insert(ctfq)
	
	return

def mkTempDir(temppath):
	return apParam.createDirectory(temppath)

def getBestDefocusForImage(imgdata, display=False):
	"""
	takes an image and get the best defocus for that image
	"""

	ctfvalue, conf = getBestCtfValueForImage(imgdata)
	if ctfvalue is None:
		apDisplay.printWarning("both confidence values for previous run were 0, using nominal defocus")
		return imgdata['scope']['defocus']

	if ctfvalue['acerun']['aceparams']['stig'] == 1:
		apDisplay.printWarning("astigmatism was estimated for "+apDisplay.short(imgdata['filename'])+\
				       " and average defocus estimate may be incorrect")
		avgdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		return -avgdf

	if display is True:
		print "Best ACE run info: '"+ctfvalue['acerun']['name']+"', confidence="+\
			str(round(conf,4))+", defocus="+str(round(-1.0*abs(ctfvalue['defocus1']*1.0e6),4))+\
			" microns, resamplefr="+str(ctfvalue['acerun']['aceparams']['resamplefr'])

	return -ctfvalue['defocus1']

def getBestCtfValueForImage(imgdata, ctfavg=False):
	"""
	takes an image and get the best ctfvalues for that image
	"""
	### get all ctf values
	ctfq = appionData.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = appiondb.query(ctfq)

	### check if it has values
	if ctfvalues is None:
		return None, None

	### find the best values
	bestconf = 0.0
	bestctfvalue = None
	for ctfvalue in ctfvalues:
		conf1 = ctfvalue['confidence']
		conf2 = ctfvalue['confidence_d']
		if conf1 > 0 and conf2 > 0:
			conf = max(conf1,conf2)
			if ctfavg is True:
				conf = math.sqrt(conf1*conf2)
			if conf > bestconf:
				bestconf = conf
				bestctfvalue = ctfvalue
	return bestctfvalue, bestconf

def getBestTiltCtfValueForImage(imgdata):
	"""
	takes an image and get the tilted ctf parameters for that image
	"""
	### get all ctf values
	ctfq = appionData.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = appiondb.query(ctfq)
	
	bestctftiltvalue = None
	cross_correlation = 0.0
	for ctfvalue in ctfvalues:
		if ctfvalue['ctftiltrun'] is not None:
			if bestctftiltvalue is None:
				cross_correlation = ctfvalue['cross_correlation']
				bestctftiltvalue = ctfvalue
			else:
				if cross_correlation < ctfvalue['cross_correlation']:
					cross_correlation = ctfvalue['cross_correlation']
					bestctftiltvalue = ctfvalue

	return bestctftiltvalue	


def ctfValuesToParams(ctfvalue, params):
	if ctfvalue['acerun'] is not None:
		if ctfvalue['acerun']['aceparams']['stig'] == 1:
			apDisplay.printWarning("astigmatism was estimated for this image"+\
			 " and average defocus estimate may be incorrect")
			params['hasace'] = True
			avgdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
			params['df']     = avgdf*-1.0e6
			params['conf_d'] = ctfvalue['confidence_d']
			params['conf']   = ctfvalue['confidence']
			return -avgdf
		else:
			params['hasace'] = True
			params['df']     = ctfvalue['defocus1']*-1.0e6
			params['conf_d'] = ctfvalue['confidence_d']
			params['conf']   = ctfvalue['confidence']
			return -ctfvalue['defocus1']
	if ctfvalue['ctftiltrun'] is not None:
			params['hasctftilt'] = True
			params['df1'] = ctfvalue['defocus1']*-1.0e6
			params['df2'] = ctfvalue['defocus2']*-1.0e6
			params['dfinit'] = ctfvalue['defocusinit']*-1.0e6
			params['angle_astigmatism'] = ctfvalue['angle_astigmatism']
			params['cross_correlation'] = ctfvalue['cross_correlation']
			params['tilt_angle'] = ctfvalue['tilt_angle']
			params['tilt_axis_angle'] = ctfvalue['tilt_axis_angle']
			params['confidence_d'] = ctfvalue['confidence_d']
			return -ctfvalue['defocus1']	

	return None


def printCtfSummary(params):
	"""
	prints a histogram of the best ctfvalues for the session
	"""
	sys.stderr.write("processing CTF histogram...\n")
	### get all images
	imgtree = apDatabase.getAllImages({}, params)

	### get best ctf values for each image
	ctfhistconf = []
	ctfhistval = []
	for imgdata in imgtree:
		if params['norejects'] is True and apDatabase.getSiblingImgAssessmentStatus(imgdata) is False:
			continue

		ctfq = appionData.ApCtfData()
		ctfq['image'] = imgdata
		ctfvalues = appiondb.query(ctfq)

		### check if it has values
		if ctfvalues is None:
			continue

		### find the best values
		bestconf = 0.0
		bestctfvalue = None
		for ctfvalue in ctfvalues:
			conf1 = ctfvalue['confidence']
			conf2 = ctfvalue['confidence_d']
			if conf1 > 0 and conf2 > 0:
				#conf = max(conf1,conf2)
				conf = math.sqrt(conf1*conf2)
				if conf > bestconf:
					bestconf = conf
					bestctfvalue = ctfvalue
		ctfhistconf.append(bestconf)
		ctfhistval.append(bestctfvalue)

	ctfhistconf.sort()
	confhist = {}
	yspan = 20.0
	minconf = ctfhistconf[0]
	maxconf = ctfhistconf[len(ctfhistconf)-1]
	maxcount = 0
	for conf in ctfhistconf:
		c2 = round(conf*yspan,0)/float(yspan)
		if c2 in confhist:
			confhist[c2] += 1
			if confhist[c2] > maxcount:
				maxcount = confhist[c2]
		else:
			confhist[c2] = 1
	if maxcount > 70:
		scale = 70.0/float(maxcount)
		sys.stderr.write(" * = "+str(round(scale,1))+" images\n")
	else:
		scale = 1.0

	colorstr = {}
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < 0.5:
			colorstr[j] = "red"
		elif j < 0.8:
			colorstr[j] = "yellow"
		else:
			colorstr[j] = "green"

	sys.stderr.write("Confidence histogram:\n")
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < minconf-1.0/yspan:
			continue
		jstr = "%1.2f" % j
		jstr = apDisplay.rightPadString(jstr,5)
		sys.stderr.write(jstr+"> ")
		if j in confhist:
			for k in range(int(confhist[j]*scale)):
				sys.stderr.write(apDisplay.color("*",colorstr[j]))
		sys.stderr.write("\n")
