
import threading
import time
from leginon import leginondata
import calibrationclient
import event
import instrument
import reference
import gui.wx.ReferenceCounter
import gui.wx.AlignZLP

class ReferenceCounter(reference.Reference):
	panelclass = gui.wx.ReferenceCounter.ReferenceCounterPanel
	settingsclass = leginondata.ReferenceCounterSettingsData
	eventinputs = reference.Reference.eventinputs + [event.AcquisitionImagePublishEvent]
	eventoutputs = reference.Reference.eventoutputs

	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update (
		{'interval count': 1}
	)
	requestdata = None

	def __init__(self, *args, **kwargs):
		super(ReferenceCounter,self).__init__(*args, **kwargs)
		# a count of acquisition image published to here
		self.last_processed = 0

		if self.__class__ == ReferenceCounter:
			self.start()

	def addWatchFor(self,kwargs):
		watch = super(ReferenceCounter,self).addWatchFor(kwargs)
		return watch + [event.AcquisitionImagePublishEvent]

	def _processData(self, incoming_data):
		super(ReferenceCounter,self)._processData(incoming_data)
		if isinstance(incoming_data, leginondata.AcquisitionImageData):
			self.processAcquisitionImagePublishEvent(incoming_data)

	def processAcquisitionImagePublishEvent(self, imgdata):
			'''
			Count AcquisitionImageData published.
			'''
			self.last_processed += 1
			self.logger.info('image count %d' % self.last_processed)

	def _processRequest(self, request_data):
		interval_count = self.settings['interval count']
		if interval_count is not None and self.last_processed is not None:
			interval = self.last_processed
			if interval < interval_count:
				message = '%d counts since last execution, ignoring request'
				self.logger.info(message % interval)
				return
		self.moveAndExecute(request_data)
		self.last_processed = 0

	def onTest(self, request_data=None):
		super(ReferenceCounter,self).onTest(request_data)
		self.logger.info('Reset Request Process Counter')
		self.last_processed = 0

	def uiResetCounter(self):
		# reset counter, not timer
		self.logger.info('Reset Request Process Counter')
		self.last_processed = 0


