#! /usr/bin/env python
# Upload pik or box files to the database

import os, re, sys
import data
import time
from selexonFunctions import *

if __name__ == '__main__':
	# record command line
	writeSelexLog(sys.argv)

	# create params dictionary & set defaults
	params=createDefaults()
	params['runid']="manual1"

	# parse command line input
	parsePrtlUploadInput(sys.argv,params)

	# check to make sure that incompatible parameters are not set
	if (params["diam"]==0):
		print "\nERROR: please input the diameter of your particle (for display purposes only)\n\n"
		sys.exit(1)
	
	# get list of input images, since wildcards are supported
	if not params['imgs']:
		print "\nERROR: enter picked particle files\n"
		sys.exit()
	imglist=params["imgs"]
	images=[]

	print "getting image data from database:"
	totimgs=len(imglist)
	i=1
	for img in imglist:
		print "image",i,"of",totimgs,":",img
		imageq=data.AcquisitionImageData(filename=img)
		imageresult=db.query(imageq, readimages=False)
		images=images+imageresult
		i+=1
	params['session']=images[0]['session']['name']

	# upload Particles
	while images:
		img = images.pop(0)

		# insert selexon params into dbparticledata.selectionParams table
		expid=int(img['session'].dbid)
		insertManualParams(params,expid)
		insertParticlePicks(params,img,expid,manual=True)
			

