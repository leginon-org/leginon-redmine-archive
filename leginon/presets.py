#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import data
import event
import dbdatakeeper
import cPickle
import copy
import uidata
import camerafuncs
import strictdict
import threading
import time
import unique

class PresetsClient(object):
	'''
	client functions for nodes to access PresetsManager
	'''
	def __init__(self, node):
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.pchanged = {}

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
		self.pchanged[presetname] = threading.Event()
		evt = event.ChangePresetEvent()
		evt['name'] = presetname
		evt['emtarget'] = emtarget
		timeout = 40
		try:
			self.node.outputEvent(evt, wait=True, timeout=timeout)
		except node.ConfirmationTimeout:
			print 'no response from PresetsManager after % s, be sure this node is bound to PresetsManager' % (timeout,)

	def presetchanged(self, ievent):
		name = ievent['name']
		if name in self.pchanged:
			self.pchanged[name].set()
		self.node.confirmEvent(ievent)

	def getPresets(self):
		try:
			seqdata = self.node.researchByDataID(('presets',))
		except node.ResearchError:
			return []
		if seqdata is None:
			return []
		else:
			return seqdata['sequence']

	def getCurrentPreset(self):
		pdata = self.node.researchByDataID(('current preset',))
		return pdata

	def getPresetByName(self, pname):
		ps = self.getPresets()
		for p in ps:
			if p['name'] == pname:
				return p

	def uiPresetSelector(self):
		getpresets = uidata.Method('Get Names', self.uiGetPresetNames)
		self.uiselectpreset = uidata.SingleSelectFromList('Select Preset', [], 0, persist=True)
		container = uidata.Container('Preset Selection')
		container.addObjects((getpresets, self.uiselectpreset))
		return container

	def uiGetPresetNames(self):
		presetlist = self.getPresets()
		pnames = [p['name'] for p in presetlist]
		self.uiselectpreset.set(pnames, 0) 

	def uiGetSelectedName(self):
		presetname = self.uiselectpreset.getSelectedValue()
		return presetname


class DataHandler(node.DataHandler):
	def query(self, id):
		if id == ('presets',):
			result = data.PresetSequenceData()
			result['sequence'] = self.node.presets
		elif id == ('current preset',):
			result = self.node.currentpreset
		else:
			result = node.DataHandler.query(self, id)
		return result


class PresetsManager(node.Node):

	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent]
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent, event.ListPublishEvent]

	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.addEventInput(event.ChangePresetEvent, self.changePreset)

		ids = [('presets',), ('current preset',)]
		e = event.ListPublishEvent(idlist=ids)
		self.outputEvent(e)

		self.cam = camerafuncs.CameraFuncs(self)
		self.currentselection = None
		self.currentpreset = None
		self.presets = []
		self.getPresetsFromDB()

		self.defineUserInterface()
		self.start()

	def changePreset(self, ievent):
		'''
		callback for received PresetChangeEvent from client
		'''
		pname = ievent['name']
		emtarget = ievent['emtarget']
		if emtarget is None:
			print 'ToScope'
			self.toScopeFollowCycle(pname)
		else:
			print 'targetToScope'
			self.targetToScope(pname, emtarget)
		self.confirmEvent(ievent)
		print 'Preset changed to %s' % (pname,)

	def getPresetsFromDB(self, session=None):
		'''
		get list of presets for this session from DB
		and use them to create self.presets list
		'''
		if session is None:
			session = self.session
			diffsession = False
		else:
			## importing another sessions presets
			diffsession = True

		### get presets from database
		pdata = data.PresetData(session=session)
		presets = self.research(datainstance=pdata)

		### only want most recent of each name
		mostrecent = []
		names = []
		for preset in presets:
			if preset['name'] not in names:
				names.append(preset['name'])
				if preset['removed'] != 1:
					if preset['session'] is not self.session:
						preset['session'] = self.session
					mostrecent.append(preset)
		self.presets[:] = mostrecent

		### if using another session's presets, now save them
		### as this sessions presets
		if diffsession:
			## since this is a new session, we don't trust
			## previously acquired references (plus they won't
			## be linked to these new presets anyway)
			for p in self.presets:
				p['hasref'] = False
			self.presetToDB()

	def presetToDB(self, presetdata=None):
		'''
		stores a preset in the DB under the current session name
		if no preset is specified, store all self.presets
		'''
		if presetdata is None:
			tostore = self.presets
		else:
			tostore = [presetdata]
		for p in tostore:
			pdata = copy.copy(p)
			pdata['session'] = self.session
			self.publish(pdata, database=True, dbforce=True)

	def presetByName(self, name):
		for p in self.presets:
			if p['name'] == name:
				return p
		return None

	def indexByName(self, name):
		i = 0
		for p in self.presets:
			if p['name'] == name:
				return i
			i += 1
		return None

	def indexByPreset(self, preset):
		return self.presets.index(preset)

	def insertPreset(self, p, newpreset):
		'''
		insert new preset into my set of managed presets
		p is either the index or item to insert at
		'''
		if type(p) is int:
			i = p
		else:
			i = self.index(p)
		self.presets.insert(i, newpreset)

	def removePreset(self, p):
		'''
		remove a preset by index or reference
		p is either a preset, or index of the preset
		'''
		premove = None
		if type(p) is int:
			premove = self.presets[p]
			del self.presets[p]
		elif type(p) is str:
			pcopy = list(self.presets)
			for preset in pcopy:
				if preset['name'] == p:
					premove = preset
					self.presets.remove(preset)
		else:
			premove = p
			self.presets.remove(p)
		if premove is not None:
			premove['removed'] = 1
			self.presetToDB(premove)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)

	def toScope(self, p):
		'''
		p is either index, preset, or name
		'''
		presetdata = None
		if type(p) is int:
			presetdata = self.presets[p]
		elif type(p) is str:
			for preset in self.presets:
				if p == preset['name']:
					presetdata = preset
					break
		elif isinstance(p, data.PresetData):
			presetdata = p
		else:
			print 'Bad arg for toScope'
			return

		if presetdata is None:
			print 'no such preset'
			return

		name = presetdata['name']
		print 'changing to preset %s' % (name,)

		## should switch to using AllEMData
		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()
		scopedata.friendly_update(presetdata)
		cameradata.friendly_update(presetdata)
		scopedata['id'] = ('scope',)
		cameradata['id'] = ('camera',)
		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		else:
			pause = self.changepause.get()
			time.sleep(pause)
			self.currentpreset = presetdata
			print 'preset changed to %s' % (name,)
			self.outputEvent(event.PresetChangedEvent(name=name))

	def fromScope(self, name):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''
		scopedata = self.researchByDataID(('scope',))
		cameradata = self.researchByDataID(('camera no image data',))
		newpreset = data.PresetData()
		newpreset.friendly_update(scopedata)
		newpreset.friendly_update(cameradata)
		newpreset['id'] = None
		newpreset['session'] = self.session
		newpreset['name'] = name

		for p in self.presets:
			if p['name'] == name:
				self.presets.remove(p)
				break
		self.presets.append(newpreset)

		self.presetToDB(newpreset)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, len(pnames)-1)
		return newpreset

	def presetNames(self):
		names = [p['name'] for p in self.presets]
		return names

	def uiGetPresetsFromDB(self):
		othersessionname = self.othersession.getSelectedValue()
		initializer = {'name': othersessionname}
		othersessiondata = data.SessionData(initializer=initializer)
		sessions = self.research(datainstance=othersessiondata)
		try:
			othersession = sessions[0]
		except (TypeError, IndexError):
			print 'cannot find session:', othersessionname
			return
		self.getPresetsFromDB(othersession)
		names = self.presetNames()
		self.uiselectpreset.set(names, 0)

	def uiToScope(self):
		new = self.uiselectpreset.getSelectedValue()
		self.toScopeFollowCycle(new)

	def toScopeFollowCycle(self, new):
		usecycle = self.usecycle.get()
		if usecycle:
			order = self.orderlist.get()
			print 'NEW', new
			if self.currentpreset is None:
				current = order[0]
			else:
				current = self.currentpreset['name']
			print 'CURRENT', current

			## if cycle creation works, then 
			try:
				cycle = self.createCycleList(current, new)
			except RuntimeError:
				cycle = []
			print 'CYCLE', cycle

			if cycle:
				print 'following cycle to %s' % (new,)
				# remove first and last from list
				try:
					del cycle[0]
					del cycle[-1]
				except IndexError:
					pass
				for p in cycle:
					print 'toScope(%s)' % (p,)
					self.toScope(p)
		print 'toScope(%s)' % (new,)
		self.toScope(new)

	def createCycleList(self, first, last, order=None):
		if order is None:
			order = self.orderlist.get()
		if not order:
			print 'no order list specified'
			raise RuntimeError('no order list specified')
		print 'ORDER', order
		if last not in order:
			print 'last not in order list'
			raise RuntimeError('last not in order')
		if first not in order:
			first = last
		cycle = []
		on = False
		done = False
		while True:
			for pname in order:
				if on:
					if pname == last:
						done = True
					cycle.append(pname)
				else:
					if pname == first:
						on = True
						cycle.append(pname)
				if done:
					break
			if done:
				break
		return cycle

	def uiCycleToScope(self):
		print 'Cycling Presets...'
		for name in self.orderlist.get():
			p = self.presetByName(name)
			if p is None:
				self.printerror('%s not in presets' % (name,))
			else:
				self.toScope(p)
		print 'Cycle Done'

	def uiSelectedFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		newpreset = self.fromScope(sel)

	def uiSelectedRemove(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.removePreset(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
			d = newpreset.toDict(noNone=True)
			del d['session']
			self.presetparams.set(d, callback=False)
		else:
			print 'Enter a preset name!'

	def uiSelectCallback(self, index):
		try:
			self.currentselection = self.presets[index]
		except IndexError:
			self.currentselection = None
		else:
			d = self.currentselection.toDict(noNone=True)
			try:
				del d['session']
			except KeyError:
				pass
			self.presetparams.set(d, callback=False)
		return index

	def uiParamsCallback(self, value):
		if (self.currentselection is None) or (not value):
			return {}
		else:
			if self.autosquare.get():
				for autokey in ('dimension','binning','offset'):
					self.square(value[autokey])
			for key in value:
				self.currentselection[key] = value[key]
			self.presetToDB(self.currentselection)
			d = self.currentselection.toDict(noNone=True)
			del d['session']
		return d

	def square(self, xydict):
		xydict['y'] = xydict['x']

	def getSessionNameList(self):
		'''
		get list of session names from this instrument
		'''
		querysession = data.SessionData()
		querysession['instrument'] = self.session['instrument']
		sessionlist = self.research(datainstance=querysession, fill=False)
		sessionnamelist = [x['name'] for x in sessionlist]
		return sessionnamelist

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		sessionnamelist = self.getSessionNameList()
		self.othersession = uidata.SingleSelectFromList('Session', sessionnamelist, 0)
		fromdb = uidata.Method('Import', self.uiGetPresetsFromDB)
		importcont = uidata.Container('Import')
		importcont.addObjects((self.othersession, fromdb))

		## create preset
		self.enteredname = uidata.String('New Name', '', 'rw')
		newfromscopemethod = uidata.Method('New From Scope', self.uiNewFromScope)
		createcont = uidata.Container('Preset Creation')
		createcont.addObjects((self.enteredname, newfromscopemethod))

		## selection
		self.autosquare = uidata.Boolean('Auto Square', True, 'rw')
		self.presetparams = uidata.Struct('Parameters', {}, 'rw', self.uiParamsCallback)
		self.uiselectpreset = uidata.SingleSelectFromList('Preset', [], 0, callback=self.uiSelectCallback)
		toscopemethod = uidata.Method('To Scope', self.uiToScope)
		self.changepause = uidata.Float('Pause', 1.0, 'rw', persist=True)
		cyclemethod = uidata.Method('Cycle To Scope', self.uiCycleToScope)
		self.usecycle = uidata.Boolean('Always Follow Cycle', True, 'rw', persist=True)
		fromscopemethod = uidata.Method('From Scope', self.uiSelectedFromScope)
		removemethod = uidata.Method('Remove', self.uiSelectedRemove)
		self.orderlist = uidata.Array('Cycle Order', [], 'rw', persist=True)

		selectcont = uidata.Container('Selection')
		selectcont.addObjects((self.uiselectpreset,toscopemethod,fromscopemethod,removemethod,self.changepause,cyclemethod,self.usecycle,self.orderlist,self.autosquare,self.presetparams))

		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)
		self.orderlist.set(pnames)

		## acquisition
		cameraconfigure = self.cam.configUIData()
		acqmeth = uidata.Method('Acquire', self.uiAcquire)

		#self.statrows = uidata.Array('Stats Row Range', [], 'rw', persist=True)
		#self.statcols = uidata.Array('Stats Column Range', [], 'rw', persist=True)
		#statsmeth = uidata.Method('Get Stats', self.uiGetStats)


		self.ui_image = uidata.Image('Image', None, 'r')


		imagecont = uidata.Container('Acquisition')
		imagecont.addObjects((cameraconfigure, acqmeth, self.ui_image,))


		## main container
		container = uidata.LargeContainer('Presets Manager')
		container.addObjects((importcont,createcont,selectcont,imagecont))
		self.uiserver.addObject(container)

		return

	def uiAcquire(self):
		print 'acquiring image'
		imagedata = self.cam.acquireCameraImageData(camconfig='UI', correction=True)
		if imagedata is None:
			return
		
		## store the CameraImageData as a PresetReferenceImageData
		ref = data.PresetReferenceImageData(id=self.ID())
		ref.update(imagedata)
		if not self.currentpreset['hasref']:
			self.currentpreset['hasref'] = True
		ref['preset'] = self.currentpreset
		self.publish(ref, database=True)
		print 'published new reference image for %s' % (self.currentpreset['name'],)

		## display
		self.ui_image.set(imagedata['image'])

	def targetToScope(self, newpresetname, emtargetdata):
		'''
		This is like toScope, but this one is mainly called
		by client nodes which request that presets and targets
		be tightly coupled.
		'''
		## first cycle through presets before sending the final one
		if self.usecycle.get():
			order = self.orderlist.get()
			if self.currentpreset is None:
				currentname = order[0]
			else:
				currentname = self.currentpreset['name']
			previousname = order[order.index(newpresetname)-1]
			print 'PREV', previousname
			print 'CUR', currentname
			print 'NEW', newpresetname
			if currentname not in (newpresetname, previousname):
				print 'now cycling to %s' % (previousname,)
				self.toScopeFollowCycle(previousname)

		## XXX this might be dangerous:  I'm taking the original target
		## preset and using it's name to get the PresetManager's preset
		## by that same name
		oldpreset = self.presetByName(emtargetdata['preset']['name'])
		newpreset = self.presetByName(newpresetname)
		emdata = emtargetdata['scope']
		scopedata = data.ScopeEMData(id=('scope',), initializer=emdata)

		## figure out how to transform the target image shift
		## ???
		## for now, assume that image shift targets are not passed
		## across mag mode ranges, so newishift is straight from 
		## newpreset
		## Within the same mag mode, use target - oldpreset + newpreset

		if oldpreset['magnification'] < 1500:
			oldmag = 'LM'
		else:
			oldmag = 'SA'
		if newpreset['magnification'] < 1500:
			newmag = 'LM'
		else:
			newmag = 'SA'

		newishift = {}
		if oldmag == newmag:
			print 'SAME MAG MODE'
			newishift['x'] = scopedata['image shift']['x']
			newishift['x'] -= oldpreset['image shift']['x']
			newishift['x'] += newpreset['image shift']['x']

			newishift['y'] = scopedata['image shift']['y']
			newishift['y'] -= oldpreset['image shift']['y']
			newishift['y'] += newpreset['image shift']['y']
		else:
			print 'DIFFERENT MAG MODE'
			newishift['x'] = newpreset['image shift']['x']
			newishift['y'] = newpreset['image shift']['y']

		## should use AllEMData, but that is not working yet
		scopedata.friendly_update(newpreset)
		scopedata['image shift'] = newishift
		cameradata = data.CameraEMData()
		cameradata.friendly_update(newpreset)

		cameradata['id'] = ('camera',)
		scopedata['id'] = ('scope',)

		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			print '** Maybe EM is not running?'
		except:
			self.printException()
		else:
			pause = self.changepause.get()
			time.sleep(pause)
			name = newpreset['name']
			self.currentpreset = newpreset
			print 'preset changed to %s' % (name,)
			self.outputEvent(event.PresetChangedEvent(name=name))
