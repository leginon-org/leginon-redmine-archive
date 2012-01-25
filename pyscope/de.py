import DECameraClientLib
import numpy
import time
import pyami.imagefun
import ccdcamera
import threading

## decorator to put a thread lock around a function
def locked(fun):
	def newfun(*args, **kwargs):
		__deserver_lock.acquire()
		try:
			return fun(*args, **kwargs)
		finally:
			__deserver_lock.release()
	return newfun

# Shared global connection to the DE Server
__deserver = None
__active_camera = None
__deserver_lock = threading.RLock()

##### Begin thread safe functions to operate on DE Server #####

@locked
def de_connect():
	if __deserver:
		return
	__deserver = DECameraClientLib.DECameraClientLib()
	__deserver.connect()

@locked
def de_disconnect():
	if __deserver.connected:
		__deserver.disconnect()

@locked
def de_setActiveCamera(de_name):
	if __active_camera != de_name:
		__deserver.setActiveCamera(de_name)
		__active_camera = de_name

@locked
def de_print_props(de_name):		
	setActiveCamera(de_name)
	camera_properties = __deserver.getActiveCameraProperties()
	for one_property in camera_properties:
		print one_property, __deserver.getProperty(one_property)		

@locked
def de_getProperty(de_name, name):		
	setActiveCamera(de_name)
	value = __deserver.getProperty(name)
	return value

@locked
def de_setProperty(de_name, name, value):		
	setActiveCamera(de_name)
	value = __deserver.setProperty(name, value)
	return value

@locked
def de_getDictProp(de_name, name):		
	setActiveCamera(de_name)
	x = int(__deserver.getProperty(name + ' X'))
	y = int(__deserver.getProperty(name + ' Y'))
	return {'x': x, 'y': y}

@locked
def de_setDictProp(de_name, name, xydict):		
	setActiveCamera(de_name)
	__deserver.setProperty(name + ' X', int(xydict['x']))
	__deserver.setProperty(name + ' Y', int(xydict['y']))		

@locked
def de_getImage(de_name):
	setActiveCamera(de_name)
	image = __deserver.GetImage()
	return image

##### End thread safe functions to operate on DE Server #####


class DECameraBase(ccdcamera.CCDCamera):
	'''
	All DE camera classes should inherit this to allow
	for a shared connection to the DE server.
	Subclasses should define an attribute "de_name"
	to inform this base class how to set the active camera.
	'''
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)

		de_connect()

		## instance specific 
		self.offset = {'x': 0, 'y': 0}
		self.binning = {'x': 1, 'y': 1}
		#update a few essential camera properties to default values
		self.setProperty('Correction Mode', 'Uncorrected Raw')

	def getProperty(self, name):		
		value = de_getProperty(self.name, name)
		return value

	def setProperty(self, name, value):		
		value = de_setProperty(self.name, name, value)
		return value

	def getDictProp(self, name):		
		return de_getDictProp(self.name, name)

	def setDictProp(self, name, xydict):		
		return de_setDictProp(self.name, name, xydict)

	def _getImage(self):
		t0 = time.time()
		image = de_getImage(self.name)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		if not isinstance(image, numpy.ndarray):
			raise ValueError('DE12 GetImage did not return array')
		image = self.finalizeGeometry(image)
		print 'Pausing, otherwise, no frames name when this returns.'
		time.sleep(0.5)
		return image

	def getCameraSize(self):
		return self.getDictProp('Image Size')

	def getExposureTime(self):
		seconds = self.getProperty('Exposure Time (seconds)')
		ms = int(seconds * 1000.0)
		return ms

	def setExposureTime(self, ms):
		seconds = ms / 1000.0
		print 'SETTING EXPTIME', time.time(), seconds
		self.setProperty('Exposure Time (seconds)', seconds)

	def getDimension(self):
		return self.dimension

	def setDimension(self, dimdict):
		self.dimension = dimdict
	
	def getBinning(self):
		return self.binning

	def setBinning(self, bindict):
		self.binning = bindict

	def getOffset(self):
		return self.offset

	def setOffset(self, offdict):
		self.offset = offdict

	def finalizeGeometry(self, image):
		row_start = self.offset['y'] * self.binning['y']
		col_start = self.offset['x'] * self.binning['x']
		nobin_rows = self.dimension['y'] * self.binning['y']
		nobin_cols = self.dimension['x'] * self.binning['x']
		row_end = row_start + nobin_rows
		col_end = col_start + nobin_cols
		nobin_image = image[row_start:row_end, col_start:col_end]
		assert self.binning['x'] == self.binning['y']
		binning = self.binning['x']
		bin_image = pyami.imagefun.bin(nobin_image, binning)
		bin_image = numpy.fliplr(bin_image)
		return bin_image

	def getPixelSize(self):
		psize = 6e-6
		return {'x': psize, 'y': psize}

	def getRetractable(self):
		return True
		
	def setInserted(self, value):
		if value:
			de12value = 'Extended'
			sleeptime = 20
		else:
			de12value = 'Retracted'
			sleeptime = 8
		self.setProperty("Camera Position", de12value)
		time.sleep(sleeptime)
		
	def getInserted(self):
		de12value = self.getProperty('Camera Position Status')
		return de12value == 'Extended'

	def getExposureTypes(self):
		return ['normal','dark']

	def getExposureType(self):
		exposure_type = self.getProperty('Exposure Mode')		
		return exposure_type.lower()
		
	def setExposureType(self, value):		
		self.setProperty('Exposure Mode', value.capitalize()) 

	def getNumberOfFrames(self):
		return self.getProperty('Total Number of Frames')

	def getSaveRawFrames(self):
		'''Save or Discard'''
		value = self.getProperty('Autosave Raw Frames')
		if value == 'Save':
			return True
		elif value == 'Discard':
			return False
		else:
			raise ValueError('unexpected value from Autosave Raw Frames: %s' % (value,))

	def setSaveRawFrames(self, value):
		'''True: save frames,  False: discard frames'''
		if value:
			value_string = 'Save'
		else:
			value_string = 'Discard'
		self.setProperty('Autosave Raw Frames', value_string)

	def getPreviousRawFramesName(self):
		frames_name = self.getProperty('Autosave Frames - Previous Dataset Name')
		return frames_name
        
	def getNumberOfFramesSaved(self):
		nframes = self.getProperty('Autosave Raw Frames - Frames Written in Last Exposure')
		return int(nframes)

	def getUseFrames(self):
		nsum = self.getProperty('Autosave Sum Frames - Sum Count')
		first = self.getProperty('Autosave Sum Frames - Ignored Frames')
		print 'NSUM', nsum
		print 'FIRST', first
		last = first + nsum
		ntotal = self.getNumberOfFrames()
		if last > ntotal:
			last = ntotal
		sumframes = range(first,last)
		return tuple(sumframes)

	def setUseFrames(self, frames):
		total_frames = self.getNumberOfFrames()
		if frames:
			nskip = frames[0]
			last = frames[-1]
		else:
			nskip = 0
			last = total_frames - 1
		nsum = last - nskip + 1
		if nsum > total_frames:
			nsum = total_frames
		nsum = int(nsum)
		print 'NSUM', nsum
		print 'NSKIP', nskip
		self.setProperty('Autosave Sum Frames - Sum Count', nsum)
		self.setProperty('Autosave Sum Frames - Ignored Frames', nskip)

	def getFrameRate(self):
		return self.getProperty('Frames Per Second')

	def getReadoutDelay(self):
		return self.getProperty('Sensor Readout Delay (milliseconds)')

	def setReadoutDelay(self, milliseconds):
		self.setProperty('Sensor Readout Delay (milliseconds)', milliseconds)

#### Classes for specific cameras

class DE12(DECameraBase):
	name = 'DE12'
	def __init__(self):
		DECameraBase.__init__(self)
		self.dimension = {'x': 4096, 'y': 3072}
		self.setProperty('Ignore Number of Frames', 0)
		self.setProperty('Preexposure Time (seconds)', 0.043)		

class DE12Survey(DECameraBase):
	name = 'DE12 Survey'
	def __init__(self):
		DECameraBase.__init__(self)
		self.dimension = {'x': 1024, 'y': 1024}
