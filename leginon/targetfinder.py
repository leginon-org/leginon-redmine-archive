#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import data
import event
import imagewatcher
import mosaic
import Mrc
import threading
import uidata
import node

class TargetFinder(imagewatcher.ImageWatcher):
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [
																							event.ImageTargetListPublishEvent]
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [
																							event.TargetListDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.targetlist = []
		self.targetlistevents = {}
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations,
																				**kwargs)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

	def researchImageTargets(self, imagedata):
		'''
		Get a list of all targets that have this image as their parent.
		only want most recent versions of each
		'''
		targetquery = data.AcquisitionImageTargetData(image=imagedata)
		## need these, so use empty instances
		targetquery['session'] = data.SessionData()
		targetquery['scope'] = data.ScopeEMData()
		targetquery['camera'] = data.CameraEMData()
		targetquery['preset'] = data.PresetData()
		targets = self.research(datainstance=targetquery, fill=False)

		## now filter out only the latest versions
		# map target id to latest version
		# assuming query result is ordered by timestamp, this works
		have = {}
		for target in targets:
			targetid = target['id']
			if targetid not in have:
				have[targetid] = target
		havelist = have.values()
		havelist.sort(self.compareTargetNumber)
		if havelist:
			print 'found %s targets for image %s' % (len(havelist), imagedata['id'])

		return havelist

	def compareTargetNumber(self, first, second):
		return cmp(first['number'], second['number'])

	def lastTargetNumber(self, imagedata):
		'''
		Returns the number of the last target associated with the given image data.
		'''
		targets = self.researchImageTargets(imagedata)
		maxnumber = 0
		for target in targets:
			if target['number'] > maxnumber:
				maxnumber = target['number']
		return maxnumber

	def findTargets(self, imdata):
		'''
		Virtual function, inheritting classes implement building self.targetlist,
		a list of ImageTargetData items.
		'''
		raise NotImplementedError()

	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return
		for imagedataid in imagelistdata['images']:
			imagedata = self.researchPublishedDataByID(imagedataid)
			if imagedata is None:
				continue
			self.findTargets(imagedata)
		self.publishTargetList()

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.ignore_images.get():
			return
		self.findTargets(imagedata)
		self.publishTargetList()

	def publishTargetList(self):
		'''
		Updates and publishes the target list self.targetlist. Waits for target
		to be "done" if specified.
		'''

		self.unNotifyUserSubmit()

		## map image id to max target number in DB
		## so we don't have to query DB every iteration of the loop
		targetnumbers = {}

		## add a 'number' to the target and then publish it
		for target in self.targetlist:
			# target may have number if it was previously published
			if target['number'] is None:
				parentimage = target['image']
				## would rather do away with id and use dbid, which
				## is more unique
				parentid = parentimage['id']
				if parentid in targetnumbers:
					last_targetnumber = targetnumbers[parentid]
				else:
					last_targetnumber = self.lastTargetNumber(parentimage)
					targetnumbers[parentid] = last_targetnumber

				## increment target number
				targetnumbers[parentid] += 1
				target['number'] = targetnumbers[parentid]

			self.publish(target, database=True)

#		if self.targetlist:
		targetlistdata = data.ImageTargetListData(id=self.ID(),
																							targets=self.targetlist)

		self.makeTargetListEvent(targetlistdata)

		self.publish(targetlistdata, pubevent=True)

		self.targetlist = []
		# wait for target list to be processed by other node
		if self.wait_for_done.get():
			self.waitForTargetListDone()


	def makeTargetListEvent(self, targetlistdata):
		'''
		Creates a threading event to be waited on for target list data.
		'''
		self.targetlistevents[targetlistdata['id']] = {}
		self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['stats'] = 'waiting'

	def waitForTargetListDone(self):
		'''
		Waits until theading events of all target list data are cleared.
		'''
		for tid, teventinfo in self.targetlistevents.items():
			print '%s WAITING for %s' % (self.id,tid,)
			teventinfo['received'].wait()
			print '%s DONE WAITING for %s' % (self.id,tid,)
		self.targetlistevents.clear()
		print '%s DONE WAITING' % (self.id,)

	def passTargets(self, targetlistdata):
		'''
		???
		'''
		self.makeTargetListEvent(targetlistdata)
		self.publish(targetlistdata, pubevent=True)

	def notifyUserSubmit(self):
		myname = self.id[-1]
		message = 'waiting for you to submit targets'
		self.usersubmitmessage = self.messagelog.information(message)
		node.beep()

	def unNotifyUserSubmit(self):
		try:
			self.usersubmitmessage.clear()
		except:
			pass

	def handleTargetListDone(self, targetlistdoneevent):
		'''
		Receives a target list done event and sets the threading event.
		'''
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		print 'got targetlistdone event, setting threading event', targetlistid
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def newTargetData(self, imagedata, type, drow, dcol):
		'''
		returns a new target data object with data filled in from the image data
		'''
		imagearray = imagedata['image']
		targetdata = data.AcquisitionImageTargetData(id=self.ID(), type=type, version=0, status='new')
		targetdata['image'] = imagedata
		targetdata['scope'] = imagedata['scope']
		targetdata['camera'] = imagedata['camera']
		targetdata['preset'] = imagedata['preset']
		targetdata['type'] = type
		targetdata['delta row'] = drow
		targetdata['delta column'] = dcol
		return targetdata

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Messages')

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.wait_for_done = uidata.Boolean('Wait for another node to process targets before declaring image process done', True, 'rw', persist=True)
		self.ignore_images = uidata.Boolean('Ignore Images', False, 'rw', persist=True)

		container = uidata.LargeContainer('Target Finder')
		container.addObjects((self.messagelog, self.wait_for_done,self.ignore_images))

		self.uicontainer.addObject(container)

class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		TargetFinder.__init__(self, id, session, nodelocations, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def findTargets(self, imdata):
		## check if targets already found on this image
		previous = self.researchImageTargets(imdata)
		if previous:
			print 'there are %s existing targets for this image' % (len(previous),)
			self.targetlist = previous
			if self.preventrepeat.get():
				print 'you are not allowed to submit targets again'
				return

		# display image
		self.clickimage.setTargets([])
		self.clickimage.setImage(imdata['image'])
		self.clickimage.imagedata = imdata

		# user now clicks on targets
		self.notifyUserSubmit()
		self.userpause.clear()
		print 'waiting for user to select targets'
		self.userpause.wait()
		print 'done waiting'
		self.targetlist += self.getTargetDataList('focus')
		self.targetlist += self.getTargetDataList('acquisition')

	def submitTargets(self):
		self.userpause.set()

	def getTargetDataList(self, typename):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			imagedata = self.clickimage.imagedata
			imagearray = imagedata['image']
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
		return targetlist

	def defineUserInterface(self):
		TargetFinder.defineUserInterface(self)

		self.clickimage = uidata.TargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('acquisition', [], (0,255,0))
		self.clickimage.addTargetType('focus', [], (0,0,255))
		self.clickimage.addTargetType('done', [], (255,0,0))
		self.clickimage.addTargetType('position', [], (255,255,0))

		submitmethod = uidata.Method('Submit Targets', self.submitTargets)
		self.preventrepeat = uidata.Boolean('Do not allow submit if already submitted on this image', True, 'rw', persist=True)

		container = uidata.LargeContainer('Click Target Finder')
		container.addObjects((self.clickimage, submitmethod, self.preventrepeat))

		self.uicontainer.addObject(container)

class MosaicClickTargetFinder(ClickTargetFinder):
	eventoutputs = ClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		self.mosaicselectionmapping = {}
		ClickTargetFinder.__init__(self, id, session, nodelocations, **kwargs)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.mosaic = mosaic.EMMosaic(self.calclients)
		self.mosaicdata = None
		self.mosaicimage = None
		self.mosaicdata = None
		self.mosaicimagescale = None

		self.existing_targets = {}
		self.clearTiles()

		if self.__class__ == MosaicClickTargetFinder:
			self.defineUserInterface()
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.setStatusMessage('Target list done')
		self.tileListToDatabase()
		self.clearTiles()
		self.outputEvent(event.MosaicDoneEvent())
		self.setStatusMessage('Mosaic is done, notification sent')

	def submitTargets(self):
		self.setStatusMessage('Sumbiting targets')
		targetlist = self.getTargetDataList('acquisition')
		self.targetlist.extend(targetlist)
		self.publishTargetList()
		self.setStatusMessage('Targets submitted')

	def clearTiles(self):
		self.idlist = []
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		if hasattr(self, 'autocreate') and self.autocreate.get():
			self.clearMosaicImage()

	def addTile(self, imagedata):
		id = imagedata['id']
		if id in self.tilemap:
			self.setStatusMessage('Image already in mosaic')
			return

		self.setStatusMessage('Adding image to mosaic')
		self.idlist.append(id)
		newtile = self.mosaic.addTile(imagedata)
		self.tilemap[id] = newtile
		self.imagemap[id] = imagedata
		targets = self.researchImageTargets(imagedata)
		self.targetmap[id] = targets
		self.setStatusMessage('Image added to mosaic')

		## generate new MosaicData
		initializer = {'id': self.ID(), 'data IDs': list(self.idlist)}
		self.mosaicdata = data.MosaicData(initializer=initializer)

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			targets = self.researchImageTargets(imagedata)
			self.targetmap[id] = targets

	def displayCurrentPosition(self):
		try:
			image = self.imagemap.values()[0]
		except:
			print 'need tiles and mosaic image'
			return
		scope = image['scope'].toDict()
		camera = image['camera'].toDict()

		#s = self.researchByDataID(('stage position',))
		#stagepos = s['stage position']
		stagepos = {'x': 0, 'y': 0}
		scope['stage position'] = {'x': 0, 'y': 0}
		print 'stage', scope['stage position']

		mosaicstate = {'scope': scope, 'camera': camera}
		pos = self.mosaic.positionByCalibration(mosaicstate)
		print 'POS', pos

	def displayDatabaseTargets(self):
		self.setStatusMessage('getting targets from database')
		self.targetsFromDatabase()
		self.displayTargets()

	def displayTargets(self):
		if self.mosaicimage is None:
			self.setStatusMessage('create mosaic image before displaying targets')
			return
		self.setStatusMessage('displaying targets')
		targets = []
		donetargets = []
		self.displayedtargetdata = {}
		for id, targetlist in self.targetmap.items():
			for targetdata in targetlist:
				tile = self.tilemap[id]
				tilepos = self.mosaic.getTilePosition(tile)
				t = self.targetToMosaicCoord(tilepos, targetdata)
				if t not in self.displayedtargetdata:
					self.displayedtargetdata[t] = []
				self.displayedtargetdata[t].append(targetdata)
				if targetdata['status'] in ('done', 'aborted'):
					donetargets.append(t)
				else:
					targets.append(t)
		self.clickimage.setTargetType('acquisition', targets)
		self.clickimage.setTargetType('done', donetargets)
		n = len(targets)
		ndone = len(donetargets)
		self.setStatusMessage('displayed %s targets (%s done)' % (n+ndone, ndone))

	def processImageData(self, imagedata):
		'''
		different from ClickTargetFinder because findTargets is
		not per image, instead we have submitTargets.
		'''
		self.setStatusMessage('Processing inbound image data')
		self.addTile(imagedata)
		if self.autocreate.get():
			self.createMosaicImage()
		self.setStatusMessage('Image data processed')

	def tileListToDatabase(self):
		if not self.idlist:
			self.setStatusMessage('Mosaic is empty')
			return
		self.setStatusMessage('Publishing mosaic data')
		self.publish(self.mosaicdata, database=True)

	def publishMosaicImage(self):
		if None in (self.mosaicdata, self.mosaicimage, self.mosaicimagescale):
			self.setStatusMessage('generate a mosaic image before publishing')
			return
		self.setStatusMessage('Publishing mosaic image data')
		mosaicimagedata = data.MosaicImageData()
		mosaicimagedata['id'] = self.ID()
		mosaicimagedata['mosaic'] = self.mosaicdata
		mosaicimagedata['image'] = self.mosaicimage
		mosaicimagedata['scale'] = self.mosaicimagescale
		self.publish(mosaicimagedata, database=True)
		self.setStatusMessage('Mosaic published')

	def updateMosaicSelection(self):
		self.setStatusMessage('Updating mosaic selection')
		instance = data.MosaicData(session=self.session)
		self.setStatusMessage('Finding mosaics')
		mosaics = self.research(datainstance=instance)
		self.mosaicselectionmapping = {}
		for mosaic in mosaics:
			key = str(mosaic['session']['name']) + ' ' + str(mosaic['id'])
			self.mosaicselectionmapping[key] = mosaic
		self.mosaicselection.set(self.mosaicselectionmapping.keys(), 0)
		self.setStatusMessage('Mosaic selection updated')

	def mosaicTilesFromDatabase(self):
		self.setStatusMessage('Loading mosaic')
		key = self.mosaicselection.getSelectedValue()
		try:
			self.mosaicdata = self.mosaicselectionmapping[key]
		except KeyError:
			self.setStatusMessage('Invalid mosaic selected')
			return
		self.setStatusMessage('Clearing mosaic')
		self.clearTiles()
		mosaicsession = self.mosaicdata['session']
		self.setStatusMessage('Finding mosaic images and data')
		ntotal = len(self.mosaicdata['data IDs'])
		for i, dataid in enumerate(self.mosaicdata['data IDs']):
			# create an instance model to query
			inst = data.AcquisitionImageData()
			# these are known:
			inst['id'] = dataid
			inst['session'] = mosaicsession
			# this are unknown, but we need them:
			inst['scope'] = data.ScopeEMData()
			inst['camera'] = data.CameraEMData()
			inst['preset'] = data.PresetData()
			self.setStatusMessage('Finding image %i of %i' % (i + 1, ntotal))
			imagedatalist = self.research(datainstance=inst, fill=False)
			try:
				imagedata = imagedatalist[0]
			except IndexError:
				self.setStatusMessage('Cannot find image data referenced by mosaic')
			else:
				self.addTile(imagedata)
		self.setStatusMessage('Mosaic loaded (%i of %i images loaded successfully)' % (i+1, ntotal))
		if self.autocreate.get():
			self.createMosaicImage()

	def targetToMosaicCoord(self, tilepos, targetdata):
		timage = targetdata['image']
		### trow, tcol is coord of target on component image
		trow = targetdata['delta row'] + timage['image'].shape[0] / 2
		tcol = targetdata['delta column'] + timage['image'].shape[1] / 2

		bbox = self.mosaic.getMosaicImageBoundaries()
		scale = self.mosaic.scale
		## this is in image viewer coords (x,y = col,row)
		r = tilepos[0] - bbox['min'][0] + trow
		c = tilepos[1] - bbox['min'][1] + tcol

		## scale
		r = scale * r
		c = scale * c
		return c,r

	def createMosaicImage(self):
		if self.mosaicdata is None:
			self.setStatusMessage('need tiles to create mosaic image')
			return

		self.setStatusMessage('creating mosaic image')

		if self.scaleimage.get():
			maxdim = self.maxdimension.get()
		else:
			maxdim = None
		self.mosaicimagescale = maxdim
		self.mosaicimage = self.mosaic.getMosaicImage(maxdim)

		self.setStatusMessage('Displaying mosaic image')
		self.clickimage.setImage(self.mosaicimage)
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		node.beep()

	def clearMosaicImage(self):
		self.clickimage.setImage(None)
		self.mosaicimage = None
		self.mosaicimagescale = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def getTargetDataList(self, typename):
		targetlist = []
		displayedtargetdata = {}
		targetsfromimage = self.clickimage.getTargetType(typename)
		for t in targetsfromimage:
			## if displayed previously (not clicked)...
			if t in self.displayedtargetdata and self.displayedtargetdata[t]:
				targetdata = self.displayedtargetdata[t].pop()
			else:
				scale = self.mosaic.scale
				newt = t[0]/scale, t[1]/scale
				targetinfo = self.mosaic.getTargetInfo(*newt)
				imagedata = targetinfo['imagedata']
				drow = targetinfo['delta row']
				dcol = targetinfo['delta column']
				targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
			if t not in displayedtargetdata:
				displayedtargetdata[t] = []
			displayedtargetdata[t].append(targetdata)
		self.displayedtargetdata = displayedtargetdata
		return targetlist

	def uiSetCalibrationParameter(self, value):
		if not hasattr(self, 'uicalibrationparameter'):
			return value
		parameter = self.uicalibrationparameter.getSelectedValue(value)
		try:
			self.mosaic.setCalibrationParameter(parameter)
		except ValueError:
			self.statusmessage.set('invalid calibration parameter specified',
															thread=True)
		return value

	def setStatusMessage(self, message):
		self.statusmessage.set(message)

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)

		self.wait_for_done.set(False)

		self.statusmessage = uidata.String('Current status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		### tiles management
		tilescontainer = uidata.Container('Mosaic Tiles')

		clearmethod = uidata.Method('Reset Tile List', self.clearTiles)
		publishtilelist = uidata.Method('Publish Tile List', self.tileListToDatabase)

		# load tiles from db
		loadcontainer = uidata.Container('Tile Lists Published in This Session')
		self.mosaicselection = uidata.SingleSelectFromList('Mosaic', [], 0)
		self.updateMosaicSelection()

		refreshmethod = uidata.Method('Refresh', self.updateMosaicSelection)
		loadmethod = uidata.Method('Load', self.mosaicTilesFromDatabase)
		loadcontainer.addObjects((refreshmethod, self.mosaicselection, loadmethod))

		tilescontainer.addObjects((clearmethod, publishtilelist, loadcontainer))


		### Mosaic Image Management
		mosaicimagecont = uidata.Container('Mosaic Image')

		parameters = self.mosaic.getCalibrationParameters()
		parameter = parameters.index(self.mosaic.getCalibrationParameter())
		self.uicalibrationparameter = uidata.SingleSelectFromList( 'Calibration Parameter', parameters, parameter, callback=self.uiSetCalibrationParameter, persist=True)
		self.scaleimage = uidata.Boolean('Scale Image', True, 'rw', persist=True)
		self.maxdimension = uidata.Integer('Maximum Dimension', 512, 'rw', persist=True)
		createmethod = uidata.Method('Create Mosaic Image From Tile List', self.createMosaicImage)
		pubmethod = uidata.Method('Publish Current Mosaic Image', self.uiPublishMosaicImage)
		self.autocreate = uidata.Boolean('Create mosaic image whenever tile list changes', True, 'rw')

		mosaicimagecont.addObjects((self.uicalibrationparameter, self.scaleimage, self.maxdimension, createmethod, self.autocreate, pubmethod))

		### Targets
		targetcont = uidata.Container('Targeting')
		refreshtargets = uidata.Method('Refresh Targets', self.displayDatabaseTargets)
		refreshposition = uidata.Method('Refresh Current Position', self.displayCurrentPosition)
		targetcont.addObjects((refreshtargets, refreshposition))

		container = uidata.LargeContainer('Mosaic Click Target Finder')
		container.addObjects((statuscontainer, tilescontainer, mosaicimagecont, targetcont))
		self.uicontainer.addObject(container)

