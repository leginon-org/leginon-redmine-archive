#!/usr/bin/env python
import node
import Numeric
import cameraimage
import data, event
import cPickle
import string
import threading
import Mrc
import camerafuncs
import dbdatakeeper
import os
import copy
import uidata

False = 0
True = 1

class DataHandler(node.DataHandler):
	def query(self, id):
		self.lock.acquire()
		if id == ('corrected image data',):
			result = self.node.acquireCorrectedImageData()
			self.lock.release()
			return result
		else:
			self.lock.release()
			return node.DataHandler.query(self, id)

class Corrector(node.Node):
	'''
	Manages dark/bright images and does other corrections
	Basic Instructions:
	  Create a corrector plan for every camera configuration that
	  requires correction.  Right now, camera configuration means:
	   dimension, binning, offset, (future: dose).
	  To create a plan, set the camera configuration in 'Preferences', 
	  set other plan options in 'Plan' and then 'Set Plan Params'.
	  This creates a plan file in the corrections directory.  Acquire
	  a dark and bright image for this plan.  These are stored as MRC
	  in the corrections directory.
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)
		self.addEventOutput(event.DarkImagePublishEvent)
		self.addEventOutput(event.BrightImagePublishEvent)
		self.addEventOutput(event.ListPublishEvent)

		ids = [('corrected image data',)]
		e = event.ListPublishEvent(self.ID(), idlist=ids)
		self.outputEvent(e)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		darkmethod = uidata.UIMethod('Acquire Dark', self.uiAcquireDark)
		brightmethod = uidata.UIMethod('Acquire Bright', self.uiAcquireBright)
		correctedmethod = uidata.UIMethod('Acquire Corrected',
																			self.uiAcquireCorrected)

		acquirecontainer = uidata.UIContainer('Image Acquisition')
		acquirecontainer.addUIObjects((darkmethod, brightmethod, correctedmethod))
		self.ui_image = uidata.UIImage('Image', None, 'rw')

		self.uiframestoaverage = uidata.UIInteger('Frames to Average', 3, 'rw')
		self.uifakeflag = uidata.UIBoolean('Fake Image', False, 'rw')
		cameraconfigure = self.cam.configUIData()
#			self.registerUIData('clip limits', 'array', default=()),
#			self.registerUIData('bad rows', 'array', default=()),
#			self.registerUIData('bad cols', 'array', default=())
		self.cliplimits = uidata.UIArray('Clip Limits', (), 'rw')
		self.badrows = uidata.UIArray('Bad Rows', (), 'rw')
		self.badcols = uidata.UIArray('Bad Cols', (), 'rw')
#		setplan = self.registerUIMethod(self.uiSetPlanParams, 'Set Plan Params',
		setplan = uidata.UIMethod('Set Plan', self.uiSetPlanParams)

		preferencescontainer = uidata.UIContainer('Preferences')
		preferencescontainer.addUIObjects((self.uiframestoaverage, self.uifakeflag, cameraconfigure, self.cliplimits, self.badrows, self.badcols, setplan))
		container = uidata.UIMediumContainer('Corrector')
		container.addUIObjects((acquirecontainer, self.ui_image,
														preferencescontainer))
		self.uiserver.addUIObject(container)

#																																			argspec)
#
#		ret = self.registerUIData('Current Plan', 'struct')
#		getplan = self.registerUIMethod(self.uiGetPlanParams, 'Get Plan Params',
#																													(), returnspec=ret)
#		plan = self.registerUISpec('Plan', (getplan, setplan))
#
#		myspec = self.registerUISpec('Corrector', (plan, acquirecontainer, prefs))
#		myspec += nodespec
#		return myspec

#	def uiSetPlanParams(self, cliplimits, badrows, badcols):
	def uiSetPlanParams(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		plandata = self.newPlan(camstate)
		plandata['clip_limits'] = self.cliplimits.get()
		plandata['bad_rows'] = self.badrows.get()
		plandata['bad_cols'] = self.badcols.get()
		self.storePlan(plandata)

	def uiGetPlanParams(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		plandata = self.retrievePlan(camstate)
		print 'plandata', plandata
		return dict(plandata)

	def uiAcquireDark(self):
		imagedata = self.acquireReference(dark=True)
		print 'Dark Stats: %s' % (self.stats(imagedata),)
		self.ui_image.set(imagedata)
		return ''

	def uiAcquireBright(self):
		imagedata = self.acquireReference(dark=False)
		print 'Bright Stats: %s' % (self.stats(imagedata),)
		self.ui_image.set(imagedata)
		return ''

	def uiAcquireCorrected(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		camdata = data.CameraEMData(('camera',), initializer=camstate)
		self.cam.currentCameraEMData(camdata)
		imagedata = self.acquireCorrectedArray()
		print 'Corrected Stats: %s' % (self.stats(imagedata),)
		self.ui_image.set(imagedata)
		return ''

	def newPlan(self, camstate):
		camdata = self.camstateToCamdata(camstate)
		plan = data.CorrectorPlanData(self.ID(), camstate=camdata)
		return plan

	def retrievePlan(self, camstate):
		newcamstate = copy.deepcopy(camstate)
		newcamstate['exposure time'] = None
		plandatalist = self.research(dataclass=data.CorrectorPlanData, camstate=newcamstate)
		if not plandatalist:
			self.printerror('cannot find plan data for camera state')
			return None
		plandata = plandatalist[0]
		return plandata

	def storePlan(self, plandata):
		self.publish(plandata, database=True)
		#self.publish(plandata, database=False)

	def acquireSeries(self, n, camdata):
		series = []
		for i in range(n):
			print 'acquiring %s of %s' % (i+1, n)
			imagedata = self.cam.acquireCameraImageData(camdata=camdata, correction=False)
			numimage = imagedata['image']
			camdata = imagedata['camera']
			scopedata = imagedata['scope']
			series.append(numimage)
		return {'image series': series, 'scope': scopedata, 'camera':camdata}

	def acquireReference(self, dark=False):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		camdata = data.CameraEMData(('camera',), initializer=camstate)
		if dark:
			camdata['exposure time'] = 0
			typekey = 'dark'
		else:
			typekey = 'bright'

		self.cam.currentCameraEMData(camdata)

		navg = self.uiframestoaverage.get()

		seriesinfo = self.acquireSeries(navg, camdata=camdata)
		series = seriesinfo['image series']
		for im in series:
			print im.shape, im.typecode()
		seriescam = seriesinfo['camera']
		seriesscope = seriesinfo['scope']

		print 'averaging series'
		ref = cameraimage.averageSeries(series)
		self.storeRef(typekey, ref, camdata)

		print 'got ref, calcnorm'
		self.calc_norm(camdata)
		print 'returning ref'
		return ref

	def retrieveRef(self, camstate, type):
		print 'TYPE', type
		camdata = self.camstateToCamdata(camstate)
		if type == 'dark':
			imagetemp = data.DarkImageData(('temp',))
		elif type == 'bright':
			imagetemp = data.BrightImageData(('temp',))
		elif type == 'norm':
			imagetemp = data.NormImageData(('temp',))
		else:
			return None

		imagetemp['id'] = None
		imagetemp['camstate'] = camdata
		print 'IMAGETEMP'
		print imagetemp
		refs = self.research(datainstance=imagetemp)
		if refs:
			ref = refs[0]
			image = ref['image']
		else:
			image = None
		return image

	def camstateToCamdata(self, camstate):
		'''
		create a proper CameraEMData object from a camstate
		(bad hack, should be better way)
		'''
		camdata = data.CameraEMData(('camera',), initializer=camstate)
		for key in ('id', 'session', 'system time', 'camera size', 'exposure time'):
			camdata[key] = None
		return camdata

	def storeRef(self, type, numdata, camstate):
		newcamstate = copy.deepcopy(camstate)

		camdata = self.camstateToCamdata(camstate)

		if type == 'dark':
			imagetemp = data.DarkImageData(self.ID())
		elif type == 'bright':
			imagetemp = data.BrightImageData(self.ID())
		elif type == 'norm':
			imagetemp = data.NormImageData(self.ID())
		imagetemp['image'] = numdata
		imagetemp['camstate'] = camdata
		print 'publishing'
		self.publish(imagetemp, pubevent=True, database=True)

	def calc_norm(self, camstate):
		dark = self.retrieveRef(camstate, 'dark')
		bright = self.retrieveRef(camstate, 'bright')
		if bright is None:
			print 'NO BRIGHT'
			return
		if dark is None:
			print 'NO DARK'
			return

		print 'norm 1'

		norm = bright - dark

		## there may be a better normavg than this
		print 'normavg'
		normavg = cameraimage.mean(norm)

		# division may result infinity or zero division
		# so make sure there are no zeros in norm
		print 'norm 2'
		norm = Numeric.clip(norm, 1.0, cameraimage.inf)
		print 'norm 3'
		norm = normavg / norm
		print 'saving'
		self.storeRef('norm', norm, camstate)

	def acquireCorrectedArray(self):
		imagedata = self.acquireCorrectedImageData()
		return imagedata['image']

	def acquireCorrectedImageData(self):
		if self.uifakeflag.get():
			camconfig = self.cam.config()
			camstate = camconfig['state']
			numimage = Mrc.mrc_to_numeric('fake.mrc')
			corrected = self.correct(numimage, camstate)
			return data.ImageData(self.ID, image=corrected)
		else:
			imagedata = self.cam.acquireCameraImageData(correction=0)
			numimage = imagedata['image']
			camstate = imagedata['camera']
			corrected = self.correct(numimage, camstate)
			imagedata['image'] = corrected
			return imagedata

	def correct(self, original, camstate):
		'''
		this puts an image through a pipeline of corrections
		'''
#		print 'normalize'
		normalized = self.normalize(original, camstate)
		plandata = self.retrievePlan(camstate)
		if plandata is not None:
#			print 'touchup'
			touchedup = self.removeBadPixels(normalized, plandata)
#			print 'clip'
			clipped = self.clip(touchedup, plandata)
#			print 'done'
			return clipped
		else:
			return normalized

	def removeBadPixels(self, image, plandata):
		badrows = plandata['bad_rows']
		badcols = plandata['bad_cols']

		shape = image.shape

		goodrow = None
		for row in range(shape[0]):
			if row not in badrows:
				goodrow = row
				break
		cameraimage.fakeRows(image, badrows, goodrow)

		goodcol = None
		for col in range(shape[1]):
			if col not in badcols:
				goodcol = col
				break
		cameraimage.fakeCols(image, badcols, goodcol)

		return image

	def clip(self, image, plandata):
		cliplimits = plandata['clip_limits']
		if len(cliplimits) == 0:
			return image
		minclip,maxclip = cliplimits
		return Numeric.clip(image, minclip, maxclip)

	def normalize(self, raw, camstate):
		dark = self.retrieveRef(camstate, 'dark')
		norm = self.retrieveRef(camstate, 'norm')
		if dark is not None and norm is not None:
			diff = raw - dark
			## this may result in some infinity values
			r = diff * norm
			return r
		else:
			return raw

	def stats(self, im):
		mean = cameraimage.mean(im)
		stdev = cameraimage.stdev(im)
		mn = cameraimage.min(im)
		mx = cameraimage.max(im)
		return {'mean':mean,'stdev':stdev,'min':mn,'max':mx}


if __name__ == '__main__':
	from Numeric import *
	import Mrc
	from ImageViewer import ImageViewer

	print 'reading darks'
	dark1 = Mrc.mrc_to_numeric('/home/pulokas/test_images/dark1.mrc')
	dark2 = Mrc.mrc_to_numeric('/home/pulokas/test_images/dark2.mrc')
	print 'averaging darks'
	dark = numeric_series_average( (dark1,dark2) )
	print 'reading brights'
	bright1 = Mrc.mrc_to_numeric('/home/pulokas/test_images/bright1.mrc')
	bright2 = Mrc.mrc_to_numeric('/home/pulokas/test_images/bright2.mrc')
	print 'averaging brights'
	bright = numeric_series_average( (bright1,bright2) )
	print 'reading raw'
	raw = Mrc.mrc_to_numeric('/home/pulokas/test_images/raw4.mrc')

	print 'setting up corrector'
	corrector = FlatCorrector()
	corrector.set_dark(dark)
	corrector.set_bright(bright)
	print 'correcting'
	good = corrector.normalize(raw)

	#print 'dark', dark
	#print 'bright', bright
	#print 'norm', corrector.norm
	#print 'good', good


	print 'prparing raw-dark'
	rawmdark = raw - dark
	print 'finding averages of raw-dark and good'
	rawmdarkavg = numeric_mean(rawmdark)
	goodavg = numeric_mean(good)
	print 'rawmdarkavg', rawmdarkavg
	print 'goodavg', goodavg

	print 'darkstdev', numeric_stdev(dark)
	goodstdev = numeric_stdev(good)
	print 'goodstdev', goodstdev

	from Tkinter import *
	root = Tk()
	jim = ImageViewer(root, bg='#488')
	jim.pack()
	jim.import_numeric(good)

	clip = (goodavg - 3 * goodstdev,   goodavg + 3 * goodstdev)
	jim.transform['clip'] = clip
	#jim.transform['output_size'] = (400,400)
	jim.update_image()

	root.mainloop()
