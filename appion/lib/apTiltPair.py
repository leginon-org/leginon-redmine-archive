import numpy
try:
#sinedon
	import sinedon.data as data
#pyami
	import pyami.peakfinder as peakfinder
	import pyami.correlator as correlator
#leginon
	import leginondata
except:
	import data
	import data as leginondata
	import peakfinder
	import correlator
	print "sinedon/pyami not available"

#appion
import appionData
import apDB
import apImage
import apDisplay
import pprint

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
	#queries
	#tiltq   = leginondata.TiltSeriesData()
	#presetq = leginondata.PresetData()
	imageq  = leginondata.AcquisitionImageData()
	#tiltq = imgdata['tilt series']
	pprint.pprint(imgdata['tilt series'])
	pprint.pprint(imgdata['preset'])
	imageq['tilt series'] = imgdata['tilt series']
	imageq['preset'] = imgdata['preset']
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






