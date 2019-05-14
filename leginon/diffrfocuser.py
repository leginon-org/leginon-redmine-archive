#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import math
import time
import threading
import singlefocuser
import acquisition
import leginondata
import gui.wx.DiffrFocuser

class DiffrFocuser(singlefocuser.SingleFocuser):
	panelclass = gui.wx.DiffrFocuser.Panel
	settingsclass = leginondata.DiffrFocuserSettingsData
	defaultsettings = dict(singlefocuser.SingleFocuser.defaultsettings)
	defaultsettings.update({
		'tilt start': -57.0,
		'tilt speed': 1.0,
		'tilt range': 114.0,
	})

	eventinputs = singlefocuser.SingleFocuser.eventinputs
	eventoutputs = singlefocuser.SingleFocuser.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		singlefocuser.SingleFocuser.__init__(self, id, session, managerlocation, **kwargs)

	def getParentTilt(self,targetdata):
		if targetdata['image']:
			parent_tilt = targetdata['image']['scope']['stage position']['a']
		else:
			parent_tilt = 0.0
		return parent_tilt

	def acquirePublishDisplayWait(self, presetdata, emtarget, channel):
		try:
			self.tiltAndWait(emtarget)
		except:
			self.logger.info('Return to %.1f deg tilt' % (math.degrees(self.tilt0)))
			self.returnToOriginalTilt()
			raise

	def returnToOriginalTilt(self):
		self.instrument.tem.BeamstopPosition = 'out'
		self.instrument.tem.StageSpeed = 1.0
		self.instrument.tem.StagePosition={'a':self.tilt0}

	def tiltAndWait(self, emtarget):
		position0 = self.instrument.tem.StagePosition
		self.tilt0 = position0['a']

		self.start_radian = math.radians(self.settings['tilt start'])
		self.end_radian = math.radians(self.settings['tilt range']+self.settings['tilt start'])
		limits = self.instrument.tem.StageLimits
		print limits, self.start_radian
		#if self.end_radian > limits['a'][1] or self.start_radian < limits['a'][0]:
		#	raise acquisition.BadImageStatsPause('Tilt angle out of range')

		tilt_time = self.settings['tilt speed']*self.settings['tilt range']
		if tilt_time >= 3*60:
			raise acquisition.BadImageStatsPause('Tilt time too long')
		# go to start
		self.logger.info('Tilting to %s degrees to start' % self.settings['tilt start'])
		self.instrument.tem.StagePosition={'a':self.start_radian}
		self.logger.info('Start tilting')
		t= threading.Thread(target=self.tiltWithSpeed)
		t.daemen = True
		t.start()
		filename = self.getTiltMovieFilename(emtarget)
		self.instrument.tem.BeamstopPosition = 'in'
		self.startMovieCollection(filename)
		t.join()
		self.logger.info('End tilting')
		self.stopMovieCollection(filename)
		self.logger.info('Return to %.1f deg tilt' % (math.degrees(self.tilt0)))
		self.returnToOriginalTilt()
		self.pauseForUser()

	def getTiltMovieFilename(self, emtarget):
		parent_id = emtarget['target']['image'].dbid
		tiltstr = '%d' % (int(round(self.settings['tilt start'])))
		if tiltstr.startswith('-'):
			tiltstr = tiltstr.replace('-','m')
		filename = '%d_%s.bin' % (parent_id, tiltstr)
		self.logger.info('tilt movie should be named: %s' % filename)
		return filename

	def tiltWithSpeed(self):
		time.sleep(0.5)
		self.instrument.tem.StageSpeed = self.settings['tilt speed']*0.1
		self.instrument.tem.StagePosition = {'a':self.end_radian}

	def startMovieCollection(self, filename):
		self.logger.info('Start movie collection')
		self.instrument.ccdcamera.startMovie(filename)

	def stopMovieCollection(self, filename):
		self.logger.info('Stop movie collection')
		self.instrument.ccdcamera.stopMovie(filename)

	def pauseForUser(self):
		# just need to set player. Status will follow it in TargetWatcher.pauseCheck
		self.player.pause()