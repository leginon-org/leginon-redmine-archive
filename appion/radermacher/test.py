#!/usr/bin/python -O

import numpy
import radermacher
import sys
from pyami import mem

if (__name__ == "__main__"):
	#a = numpy.array(((0,1),(1,1),(2,0),(1,0),(1,3),(3,1)))
	#b = numpy.array(((0,2),(1,2),(2,0),(1,0),(1,6),(3,2)))
	untilt = numpy.array((
		(585,444),(603,473),(573,525),(676,1032),(613,963),
		(897,905),(972,936),(1044,876),(370,1319),(505,1121),
		(533,1103),(109,353),(149,321),(199,283),(265,314),
		(76,335),(298,390),(391,437),(52,647),(85,639),
		(15,653),(295,477),(310,447),(139,1052),(176,1091),
		(231,1110),(210,670),(265,680),(316,679),
	))
	tilt = numpy.array((
		(483,180),(492,208),(469,261),(524,761),(480,694),
		(750,647),(697,619),(801,583),(286,1064),(391,856),
		(415,840),(134,122),(166,87),(205,43),(253,72),
		(106,103),(272,146),(337,185),(78,414),(102,405),
		(52,425),(267,234),(277,202),(122,817),(150,850),
		(193,864),(196,428),(236,439),(273,430),
	))

	#print "untilt=",untilt
	#print "tilt=  ",tilt
	u = mem.used()
	for i in range(1):
		#sys.stderr.write(".")
		e = radermacher.tiltang(untilt,tilt,1.0)
		print e
		f = radermacher.willsq(untilt,tilt,e['wtheta'],0.0,0.0)
		print f
	print "mem=",mem.used()-u,"\n"
	print "done"
	#sys.exit(1)

