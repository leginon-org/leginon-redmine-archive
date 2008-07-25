#python
import re
import numpy
#leginon
import leginondata
#appion
import appionData
import apDB
import apImage
import apDisplay
import apStack
import apTiltTransform

leginondb = apDB.db
appiondb  = apDB.apdb

"""
Denis's query
$q="select "
	."a2.DEF_id, a2.`MRC|image` as filename "
	."from AcquisitionImageData a1 "
	."left join AcquisitionImageData a2 "
	."on (a1.`REF|TiltSeriesData|tilt series`=a2.`REF|TiltSeriesData|tilt series` "
	."and a1.`REF|PresetData|preset`=a2.`REF|PresetData|preset` "
	."and a1.DEF_id<>a2.DEF_id) "
	."where a1.DEF_id=$imageId";
"""

"""
	sessionq = leginondata.SessionData(name=session)
	presetq=leginondata.PresetData(name=preset)
	imgquery = leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = leginondb.query(imgquery, readimages=False)
"""

def getTiltPair(imgdata):
	imageq  = leginondata.AcquisitionImageData()
	imageq['tilt series'] = imgdata['tilt series']
	presetq = leginondata.PresetData()
	presetq['name'] = imgdata['preset']['name']
	imageq['preset'] = presetq
	#if beam changed between tilting, presets would be different
	origid=imgdata.dbid
	alltilts = leginondb.query(imageq, readimages=False)
	tiltpair = None
	if len(alltilts) > 1:
		#could be multiple tiltpairs but we are taking only the most recent
		for tilt in alltilts:
			if tilt.dbid != origid:
				tiltpair = tilt
				break
	return tiltpair

def tiltPickerToDbNames(tiltparams):
	#('image1', leginondata.AcquisitionImageData),
	#('image2', leginondata.AcquisitionImageData),
	#('shiftx', float),
	#('shifty', float),
	#('correlation', float),
	#('scale', float),
	#('tilt', float),
	#('image1_rotation', float),
	#('image2_rotation', float),
	#('rmsd', float),
	newdict = {}
	if 'theta' in tiltparams:
		newdict['tilt_angle'] = tiltparams['theta']
	if 'gamma' in tiltparams:
		newdict['image1_rotation'] = tiltparams['gamma']
	if 'phi' in tiltparams:
		newdict['image2_rotation'] = tiltparams['phi']
	if 'rmsd' in tiltparams:
		newdict['rmsd'] = tiltparams['rmsd']
	if 'scale' in tiltparams:
		newdict['scale_factor'] = tiltparams['scale']
	if 'point1' in tiltparams:
		newdict['image1_x'] = tiltparams['point1'][0]
		newdict['image1_y'] = tiltparams['point1'][1]
	if 'point2' in tiltparams:
		newdict['image2_x'] = tiltparams['point2'][0]
		newdict['image2_y'] = tiltparams['point2'][1]
	if 'overlap' in tiltparams:
		newdict['overlap'] = tiltparams['overlap']
	return newdict

def insertTiltTransform(imgdata1, imgdata2, tiltparams, params):
	#First we need to sort imgdata
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_v01_00016en_00'
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_01_00016en_01'
	#last two digits confer order, but then the transform changes...
	bin = params['bin']

	### first find the runid
	runq = appionData.ApSelectionRunData()
	runq['name'] = params['runid']
	runq['session'] = imgdata1['session']
	runids=appiondb.query(runq, results=1)
	if not runids:
		apDisplay.printError("could not find runid in database")

	### the order is specified by 1,2; so don't change it let makestack figure it out
	for imgdata in (imgdata1, imgdata2):
		for index in ("1","2"):
			transq = appionData.ApImageTiltTransformData()
			transq["image"+index] = imgdata
			transq['tiltrun'] = runids[0]
			transdata = appiondb.query(transq)
			if transdata:
				apDisplay.printWarning("Transform values already in database for "+imgdata['filename'])
				return transdata[0]

	### prepare the insertion
	transq = appionData.ApImageTiltTransformData()
	transq['image1'] = imgdata1
	transq['image2'] = imgdata2
	transq['tiltrun'] = runids[0]
	dbdict = tiltPickerToDbNames(tiltparams)
	if dbdict is None:
		return None
	#Can I do for key in appionData.ApImageTiltTransformData() ro transq???
	for key in ('image1_x','image1_y','image1_rotation','image2_x','image2_y','image2_rotation','scale_factor','tilt_angle', 'overlap'):
		if key not in dbdict:
			apDisplay.printError("Key: "+key+" was not found in transformation data")

	for key,val in dbdict.items():
		if re.match("image[12]_[xy]", key):
			transq[key] = round(val*bin,2)
		else:
			transq[key] = val
		#print i,v


	### this overlap is wrong because the images are binned by 'bin' and now we give it the full image
	"""
	imgShape1 = numpy.asarray(imgdata1['image'].shape, dtype=numpy.int8)/params['bin']
	image1 = numpy.ones(imgShape1)
	imgShape2 = numpy.asarray(imgdata2['image'].shape, dtype=numpy.int8)/params['bin']
	image2 = numpy.ones(imgShape2)
	bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, tiltparams)
	print "image overlaps", bestOverlap, tiltOverlap
	transq['overlap'] = round(bestOverlap,5)
	"""

	apDisplay.printMsg("Inserting transform beteween "+apDisplay.short(imgdata1['filename'])+\
		" and "+apDisplay.short(imgdata2['filename'])+" into database")
	appiondb.insert(transq)
	return transq

def getStackParticleTiltPair(stackid, partnum):
	"""
	takes a stack id and particle number (1+) spider-style
	returns the stack particle number for the tilt pair
	"""
	stackpartdata1 = apStack.getStackParticle(stackid, partnum)
	partdata = stackpartdata1['particle']

	tiltpartq1 = appionData.ApTiltParticlePairData()
	tiltpartq1['particle1'] = partdata
	tiltpartdatas1 = tiltpartq1.query(results=1)

	tiltpartq2 = appionData.ApTiltParticlePairData()
	tiltpartq2['particle2'] = partdata
	tiltpartdatas2 = tiltpartq2.query(results=1)

	if not tiltpartdatas1 and tiltpartdatas2:
		otherpart = tiltpartdatas2[0]['particle1']
	elif tiltpartdatas1 and not tiltpartdatas2:
		otherpart = tiltpartdatas1[0]['particle2']
	else:
		print partdata
		print tiltpartdatas1
		print tiltpartdatas2
		apDisplay.printError("failed to get tilt pair data")

	stackpartq = appionData.ApStackParticlesData()
	stackpartq['stack'] = stackpartdata1['stack']
	stackpartq['particle'] = otherpart
	stackpartdatas2 = stackpartq.query(results=1)
	if not stackpartdatas2:
		#apDisplay.printWarning("particle "+str(partnum)+" has no tilt pair in stackid="+str(stackid))
		return None
	stackpartnum = stackpartdatas2[0]['particleNumber']

	#print partnum,"-->",stackpartnum
	return stackpartnum






