#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import data
import time
#import mem
import apLoop
import apParam
from selexonFunctions import *
from selexonFunctions2 import *
from crudFinderFunctions2 import *

data.holdImages(False)

imagesskipped=False

if __name__ == '__main__':

	# record command line
	writeSelexLog(sys.argv)

	print " ... checking parameters"
	# create params dictionary & set defaults
	params=apParam.createDefaults()

	# parse command line input
	parseSelexonInput(sys.argv,params)

	# if shiftonly is specified, make defocpair true
	if params['shiftonly']:
		params['defocpair']=True

	# check to make sure that incompatible parameters are not set
	apParam.checkParamConflicts(params)
	
	# get list of input images, since wildcards are supported
	print " ... getting images"
	if params['dbimages']==True:
		images=getImagesFromDB(params['sessionname'],params['preset'])
		params['session']=images[0]['session']
	elif params['alldbimages']:
		images=getAllImagesFromDB(params['sessionname'])
		params['session']=images[0]['session']
	else:
		if not params['mrcfileroot']:
			print "\nERROR: no files specified\n"
			sys.exit(1)
		imglist=params["mrcfileroot"]
		images=[]
		for img in imglist:
			imageq=data.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult
		params['session']=images[0]['session']
	params['imagecount']=len(images)

	getOutDirs(params)

	# if templateIds specified, create temporary template files in this directory & rescale
	print " ... getting templates"
	if params['templateIds']:
		# get the first image's pixel size:
		params['apix']=getPixelSize(images[0])
		params['template']='originalTemporaryTemplate'
		# move to run directory
		os.chdir(params['rundir'])
		# get the templates from the database
		getDBTemplates(params)
		# scale them to the appropriate pixel size
		rescaleTemplates(images[0],params)
		# set the template name to the copied file names
		params['template']='scaledTemporaryTemplate'
		
	# find the number of template files
	if params["crudonly"]==False:
		checkTemplates(params)
		# go through the template mrc files and downsize & filter them
		for tmplt in params['templatelist']:
			dwnsizeTemplate(params,tmplt)
		print " ... downsize & filtered "+str(len(params['templatelist']))+ \
			" file(s) with root \""+params["template"]+"\""
			
	# unpickle dictionary of previously processed images
	donedict=apLoop.readDoneDict(params)

	if (params["crud"]==True or params['method'] == "classic"):
		createImageLinks(images)
	
	# check to see if user only wants to run the crud finder
	if (params["crudonly"]==True):
		if (params["crud"]==True and params["cdiam"]==0):
			print "\nERROR: both \"crud\" and \"crudonly\" are set, choose one or the other.\n"
			sys.exit(1)
		if (params["diam"]==0): # diameter must be set
			print "\nERROR: please input the diameter of your particle\n\n"
			sys.exit(1)
		# create directory to contain the 'crud' files
		if not (os.path.exists("crudfiles")):
			os.mkdir("crudfiles")
		for img in images:
			imgname=img['filename']
			tstart=time.time()
			#findCrud(params,imgname)
			findCrud2(params,imgname)
			tend=time.time()
			print "CRUD FINDING TIME",tend-tstart
		sys.exit(1)
        
	# check to see if user only wants to find shifts
	if params['shiftonly']:
		for img in images:
			sibling=getDefocusPair(img)
			if sibling:
				peak=getShift(img,sibling)
				recordShift(params,img,sibling,peak)
				if params['commit']:
					insertShift(img,sibling,peak)
		sys.exit()	
	
	# create directory to contain the 'pik' files
	if not (os.path.exists("pikfiles")):
		os.mkdir("pikfiles")

	#Write log to rundir
	writeSelexLog(sys.argv,file="selexon.log")

	# run selexon
	notdone=True
	twhole=time.time()
	count  = 1
	skipcount = 1
	lastcount = 0
	#startmem = mem.used()
	peaksum = 0
	peaksumsq = 0
	timesum = 0
	timesumsq = 0
	params['waittime'] = 0
	params['lastimageskipped'] = False
	while notdone:
		while images:
			img = images.pop(0)
			imgname=img['filename']
			if(apLoop.startLoop(img,donedict,params) ==False):
				continue

			# run FindEM
			if params['method'] == "experimental":
				#Finds peaks as well:
				numpeaks = runCrossCorr(params,imgname)
				peaksum = peaksum + numpeaks
				peaksumsq = peaksumsq + numpeaks**2
			else:
#				tmpRemoveCrud(params,imgname)
				dwnsizeImg(params,imgname)
#				runFindEM(params,imgname)
				threadFindEM(params,imgname)

			if params['method'] == "classic":
				findPeaks(params,imgname)
				numpeaks = 0
			elif params['method'] == "experimental":
				print "skipping findpeaks..."
			else:
				numpeaks = findPeaks2(params,imgname)
				peaksum = peaksum + numpeaks
				peaksumsq = peaksumsq + numpeaks**2

			# if no particles were found, skip rest and go to next image
			if not (os.path.exists("pikfiles/"+imgname+".a.pik")):
				print "no particles found in \'"+imgname+".mrc\'"
				# write results to dictionary
				donedict[imgname]=True
				writeDoneDict(donedict,params)
				continue

			# run the crud finder on selected particles if specified
			if (params["crud"]==True):
				if not (os.path.exists("crudfiles")):
					os.mkdir("crudfiles")
					t1=time.time()
					findCrud(params,imgname)
					tfindCrud= "%.2f" % float(time.time()-t1)
				# if crudfinder removes all the particles, go to next image
				if not (os.path.exists("pikfiles/"+imgname+".a.pik.nocrud")):
					print "no particles left after crudfinder in \'"+imgname+".mrc\'"
 					# write results to dictionary
					donedict[imgname]=True
					writeDoneDict(donedict)
					continue

			# create jpg of selected particles if not created by crudfinder
			if (params["crud"]==False):
				if params['method'] == "classic":
					createJPG(params,imgname)
				else:
					createJPG2(params,imgname)

			# convert resulting pik file to eman box file
			if (params["box"]>0):
				pik2Box(params,imgname)
		
			# find defocus pair if defocpair is specified
			if params['defocpair']:
				sibling=getDefocusPair(img)
				if sibling:
					peak=getShift(img,sibling)
					recordShift(params,img,sibling,peak)
					if params['commit']:
						insertShift(img,sibling,peak)
			
			if params['commit']:
				insertParticlePicks(params,img,expid)

			# write results to dictionary
 			donedict[imgname]=True
			apLoop.writeDoneDict(donedict,params)

			if(params["continue"]==False or tdiff > 0.3):
				apLoop.printSummary(params)

		if params["dbimages"]==True:
			notdone=True
			if(params['skipcount'] > 0):
				print ""
				print " !!! Images already processed and were therefore skipped (total",skipcount,"skipped)."
				print " !!! to them process again, remove \'continue\' option and run selexon again."
				params['skipcount'] = 0
			print "\nAll images processed. Waiting ten minutes for new images (waited",\
				params['waittime'],"min so far)."
			time.sleep(600)
			params['waittime'] = params['waittime'] + 10
			images=getImagesFromDB(params['session']['name'],params['preset'])
			if (params["crud"]==True or params['method'] == "classic"):
				createImageLinks(images)
			if(params['waittime'] > 120):
				print "Waited longer than two hours, so I am quitting"
				notdone=False
		else:
			notdone=False

	# remove temporary templates if getting images from db
	if params['templateIds']:
		i=1
		for tmplt in params['ogTmpltInfo']:
			ogname="originalTemporaryTemplate"+str(i)+".mrc"
			scname="scaledTemporaryTemplate"+str(i)+".mrc"
			scdwnname="scaledTemporaryTemplate"+str(i)+".dwn.mrc"
			os.remove(ogname)
			os.remove(scname)
			os.remove(scdwnname)
			i=i+1
			
	ttotal= "%.2f" % float(time.time()-twhole)
	print "COMPLETE LOOP:\t",ttotal,"seconds for",count-1,"images"
	print "end run"
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print ""

