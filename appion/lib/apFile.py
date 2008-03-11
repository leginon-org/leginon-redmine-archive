import md5
import os
import sys
import apDisplay

def md5sumfile(fname):
	"""
	Returns an md5 hash for file fname
	"""
	if not os.path.isfile(fname):
		apDisplay.printError("MD5SUM, file not found: "+fname)
	f = file(fname, 'rb')
	m = md5.new()
	while True:
		d = f.read(8096)
		if not d:
			break
		m.update(d)
	f.close()
	return m.hexdigest()


def numImagesInStack(imgfile):
	"""
	Find the number of images in an 
	IMAGIC stack based on the filesize
	"""
	if imgfile[-4:] == '.hed':
		numimg = int('%d' % (os.stat(imgfile)[6]/1024))
	elif imgfile[-4:] == '.img':
		numimg = int('%d' % (os.stat(imgfile)[6]/102400))
	elif os.path.isfile(imgfile+'.hed'):
		numimg = int('%d' % (os.stat(imgfile+'.hed')[6]/1024))
	else:
		apDisplay.printError("numImagesInStack requires an IMAGIC stack")
	return numimg
