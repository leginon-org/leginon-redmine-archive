import math
from leginon import leginondata, reference, calibrationclient, cameraclient
import event
import gui.wx.PhasePlateAligner
from pyami import arraystats

class PhasePlateAligner(reference.Reference):
	# relay measure does events
	settingsclass = leginondata.PhasePlateAlignerSettingsData
	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update({
		'charge time': 2.0,
		'phase plate number': 1,
		'initial position': 1,
	})
	eventinputs = reference.Reference.eventinputs + [event.PhasePlatePublishEvent]
	eventoutputs = reference.Reference.eventoutputs + [event.PhasePlateUsagePublishEvent]
	panelclass = gui.wx.PhasePlateAligner.PhasePlateAlignerPanel
	requestdata = leginondata.PhasePlateData
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.PhasePlatePublishEvent]
		reference.Reference.__init__(self, *args, **kwargs)
		self.current_position = 1 # base 1
		self.start()

	def uiSetSettings(self):
		self.current_position = self.settings['initial position']
		self.logPhasePlateUsage()

	def onTest(self):
		self.player.play()

	def execute(self, request_data=None):
		self.setStatus('processing')
		self.logger.info('handle request')
		self.nextPhasePlate()		
		self.logger.info('done')
		self.setStatus('idle')
		return True

	def nextPhasePlate(self):
		self.setStatus('processing')
		while True:
			self.logger.info('Waiting for scope to advance PP')
			self.instrument.tem.nextPhasePlate()
			self.current_position += 1
			if self.current_position > self.getTotalPositions():
				self.current_position -= self.getTotalPositions()
			if not self.getPatchState(self.settings['phase plate number'], self.current_position):
				self.logger.info('Arrived at good Position %d' % self.current_position)
				break
			self.logger.info('Position %d is bad. Try next one' % self.current_position)
		# log phase plate patch in use
		self.logPhasePlateUsage()
		if self.settings['charge time']:
			self.presets_client.toScope(self.preset_name)
			self.logger.info('expose for %.1f second' % self.settings['charge time'])
			self.instrument.tem.exposeSpecimenNotCamera(self.settings['charge time'])

	def logPhasePlateUsage(self):
		tem = self.instrument.getTEMData()
		q = leginondata.PhasePlateUsageData(session=self.session, tem=tem)
		q['phase plate number'] = self.settings['phase plate number']
		# position counts from 1
		self.logger.info('Use Position %d' % self.current_position)
		q['patch position'] = self.current_position
		# might be reused
		self.publish(q, database=True, dbforce=True, pubevent=True)

	def researchPatchState(self, phase_plate_number, position):
		tem = self.instrument.getTEMData()
		q = leginondata.PhasePlatePatchStateData(tem=tem)
		q['phase plate number'] = phase_plate_number
		# position counts from 1
		q['patch position'] = position
		r = q.query(results=1)
		if r:
			return r[0]
		else:
			return q

	def getPatchState(self, phase_plate_number, position):
		# position counts from 1
		r = self.researchPatchState(phase_plate_number, position)
		return bool(r['bad'])

	def setPatchState(self, phase_plate_number, position, is_bad):
		# position counts from 1
		r = self.researchPatchState(phase_plate_number, position)
		if r['bad'] == is_bad:
			return
		newq = leginondata.PhasePlatePatchStateData(initializer = r)
		newq['session'] = self.session
		newq['bad'] = is_bad
		# might be reused
		newq.insert(force=True)

	def guiGetPatchStates(self,state=False):
		wxgrid_format = self.getGridFormat()
		cols = wxgrid_format['cols']
		rows = wxgrid_format['rows']
		registry = {}
		for c in range(cols):
			for r in range(rows):
				state = self.getPatchState(self.settings['phase plate number'],c*rows+r+1)
				if state:
					registry[(r,c)] = '1'
				else:
					# empty string means unchecked
					registry[(r,c)] = ''
		return registry

	def getGridFormat(self):
		return {'rows':19,'cols':4}

	def getTotalPositions(self):
		patch_format = self.getGridFormat()
		return patch_format['rows']*patch_format['cols']

	def guiSetPatchStates(self, registry):
		wxgrid_format = self.getGridFormat()
		cols = wxgrid_format['cols']
		rows = wxgrid_format['rows']
		for c in range(cols):
			for r in range(rows):
				state = bool(registry[(r, c)])
				# patch position counts from 1
				self.setPatchState(self.settings['phase plate number'],c*rows+r+1, state)

	def setAllPatchStates(self,state):
		for p in range(self.getTotalPositions()):
			# patch position counts from 1
			self.setPatchState(self.settings['phase plate number'],p+1, state)
