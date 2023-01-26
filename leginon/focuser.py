#!/usr/bin/env python
from leginon import acquisition, singlefocuser, manualfocuschecker
import gui.wx.Focuser
from leginon import leginondata
from leginon import node, targetwatcher, distancefun
import math
import numpy

class FocusResult(object):
	def __init__(self, focus_result_data, mosaic_image_target_list):
		self.grid_mosaic_id = mosaic_image_target_list.dbid #ImageTargetListData
		self.grid_label = mosaic_image_target_list['label']
		self.id = focus_result_data.dbid
		self.position = focus_result_data['scope']['stage position']
		self.preset_defocus = focus_result_data['preset']['defocus']
		self.correction_type = focus_result_data['defocus correction']
		if self.correction_type == 'Defocus':
			self.correction = self.preset_defocus + focus_result_data['defocus']
			self.focus = focus_result_data['scope']['focus']  #This where defocus is reset to.
		elif self.correction_type == 'Stage Z':
			self.correction = focus_result_data['defocus']
			self.focus = focus_result_data['scope']['stage position']['z']
		else:
			# manual focus nothing to do
			self.correction = 0.0
			self.focus = focus_result_data['scope']['focus']  #This where defocus is reset to.

class Focuser(singlefocuser.SingleFocuser):
	panelclass = gui.wx.Focuser.Panel
	settingsclass = leginondata.FocuserSettingsData
	defaultsettings = dict(singlefocuser.SingleFocuser.defaultsettings)

	eventinputs = singlefocuser.SingleFocuser.eventinputs
	eventoutputs = singlefocuser.SingleFocuser.eventoutputs

	current_target = None
	current_focus_sequence_step = 0
	corrected_focus = []
	corrected_stagez = []
	delayed_targets = []

	def newSimulatedTarget(self, preset=None,grid=None):
		target = super(Focuser,self).newSimulatedTarget(preset,grid)
		self.current_target = target
		return target


	def simulateTarget(self):
		self.good_enough = False
		self.setStatus('processing')
		# no need to pause longer for simulateTarget
		self.is_firstimage = False
		# current preset is used to create a target for this node.
		currentpreset = self.presetsclient.getCurrentPreset()
		if currentpreset is None:
			# self.validatePresets() exception is caught by parent class of this.
			# it is not useful in this case.
			try:
				currentpreset = self.useFirstPresetOrderPreset()
			except acquisition.InvalidPresetsSequence:
				self.logger.error('Configure a valid preset in the settings to allow initialization')
				self.setStatus('idle')
				return
		targetdata = self.newSimulatedTarget(preset=currentpreset,grid=self.grid)
		self.publish(targetdata, database=True)
		## change to 'processing' just like targetwatcher does
		proctargetdata = self.reportTargetStatus(targetdata, 'processing')
		try:
			ret = self.processGoodTargets([proctargetdata,])
		except Exception, e:
			raise
			self.logger.error('processing simulated target failed: %s' %e)
			ret = 'aborted'
		self.reportTargetStatus(proctargetdata, 'done')
		self.logger.info('Done with simulated target, status: %s (repeat will not be honored)' % (ret,))
		self.setStatus('idle')

	def researchFocusResultsOnGrid(self, targetdata):
		'''
		Gather successful autofocus results from the same node name and same grid atlas.
		Excluding those from the input targetdata. Results from simulated target focus
		are ignored.
		'''
		def get_grid_atlas(r):
			if r['list'] and r['list']['mosaic']:
				return r['list']
			if r['image']:
				if r['image']['target']:
					return get_grid_atlas(r['image']['target'])
			else:
				# simulated
				return
		this_grid_list = get_grid_atlas(targetdata)
		if not this_grid_list:
			return []
		#TODO ok FocuserResultData does not include those set to eucentric focus when failing
		# fit limit.  Is this going to be a problem ?
		q = leginondata.FocuserResultData(session=self.session, status='ok')
		q['node name']=self.name
		ok_results = q.query()
		# make a list of all valid result instance that is the last focus step performed.
		foc_results = []
		target_ids_with_result = [targetdata.dbid,] # avoid earlier results from the same target
		for r in ok_results:
			target = r['target']
			grid_target_list = get_grid_atlas(target)
			# each target only keep the most recent result.
			if grid_target_list and grid_target_list.dbid == this_grid_list.dbid and target.dbid not in target_ids_with_result:
				foc_results.append(FocusResult(r, grid_target_list))
				target_ids_with_result.append(target.dbid)
		self.grid_target_list = this_grid_list
		return foc_results

	def _setCorrectedFocus(self, foc_results):
		correction_type = 'Defocus'
		valid_results = list(filter((lambda x: x.correction_type==correction_type), foc_results))
		self.corrected_focus = list(map((lambda x: x.focus), valid_results))

	def _setCorrectedStageZ(self, foc_results):
		correction_type = 'Stage Z'
		valid_results = list(filter((lambda x: x.correction_type==correction_type), foc_results))
		self.corrected_stagez = list(map((lambda x: x.focus), valid_results))

	def _getCorrectedAttr(self, correction_type):
		if correction_type == 'Stage Z':
			return self.corrected_stagez
		elif correction_type == 'Defocus':
			return self.corrected_focus
		else:
			# not corrected
			return []

	def processFocusResultsInRange(self, targetdata):
		'''
		Apply correction according to focus results saved previously within a user
		defined radius.  This will do both stagez and defocus if both are in the steps.
		The FocuserResultData of these inferred corrections are not saved.
		'''
		scopedata=targetdata['scope']
		# TODO: can add only the last focus result to self.foc_results if is on the same grid atlas
		rlist = self.researchFocusResultsOnGrid(targetdata)
		if not rlist:
			return 'continue'
		# make a list of FocusResult objects that are within bypass distance of targetdata
		# scope state.
		d = self.settings['bypass distance']
		centers = numpy.array(list(map((lambda x: (x.position['x'],x.position['y'])), rlist)))
		self.foc_results = rlist
		center = numpy.array(((scopedata['stage position']['x'], scopedata['stage position']['y'])))
		in_range_indices = distancefun.withinDistance(center, centers, d)
		if not in_range_indices.shape[0]:
			return 'continue'
		in_range_rlist = numpy.array(rlist)[in_range_indices].tolist()
		# set these corrected values as corrected_focus and corrected_stagez for later average.
		self._setCorrectedFocus(in_range_rlist)
		self._setCorrectedStageZ(in_range_rlist)
		#
		used_correction_types = []
		for j, setting in enumerate(self.focus_sequence):
			# only work on the steps that are switched on
			if not setting['switch']:
				continue
			# if focus_steps use the same correction type, only do once.
			if setting['correction type'] in used_correction_types:
				continue
			used_correction_types.append(setting['correction type'])
			# empty correction should not go to the next part which changes preset.
			correction_count = len(self._getCorrectedAttr(setting['correction type']))
			if correction_count == 0:
				continue
			self.logger.info('Applying correction as in focus step %s from average of %d measurements' % (setting['name'], correction_count))
			presetname = setting['preset name']
			# use None as emtarget to send to scope
			self.presetsclient.toScope(presetname, None)
			self.applyAverageCorrection(setting)
		# acquire final to confirm success if needed.
		if self.settings['acquire final']:
			# this z will be after correction
			z = self.instrument.tem.StagePosition['z']
			# calculate emtarget for acquiring final 
			emtarget = self.targetToEMTargetData(targetdata, z)
			presetdata = self.useFirstPresetOrderPreset()
			self.acquireFinal(presetdata, emtarget)
		return 'bypass'
		# end of focus sequence loop

	def processGoodTargets(self, goodtargets):
		"""
		This overwrites TargetWatcher.processGoodTargets.
		It loops through goodtargets before looping focus sequence.
		The correction result are kept and at the end of target loop
		an average of the correction is applied.
		"""
		if goodtargets:
			# scopedata is always recorded with targets, including simulated ones
			first_targetdata = goodtargets[0]
			status = self.processFocusResultsInRange(first_targetdata)
			if status == 'bypass':
				return
		else:
			return
		if self.getIsResetTiltInList() and goodtargets:
			# ? Do we need to reset on every target ?
			self.logger.info('Tilting to %.2f degrees on first good target.' % (self.targetlist_reset_tilt*180.0/math.pi))
			self.instrument.tem.setDirectStagePosition({'a':self.targetlist_reset_tilt})
		# initialize
		self.current_target = None
		self.current_focus_sequence_step = 0
		self.delayed_targets = []
		self.is_last_target_and_focus_step = False
		self.good_enough = False

		for j, setting in enumerate(self.focus_sequence):
			self.corrected_focus = []
			self.corrected_stagez = []
			self.current_focus_sequence_step = j
			if self.good_enough == True:
				break
			for i, target in enumerate(goodtargets):
				self.logger.debug('Step %d of target %d' % (j,i))
				if j == len(self.focus_sequence)-1 and i == len(goodtargets)-1:
					self.is_last_target_and_focus_step = True
				self.goodnumber = i
				self.logger.debug('target %s status %s' % (i, target['status'],))
				# ...
				if self.player.state() == 'pause':
					self.setStatus('user input')
				state = self.clearBeamPath()
				self.setStatus('processing')
				# abort
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborting current target list')
					targetliststatus = 'aborted'
					self.reportTargetStatus(target, 'aborted')
					## continue so that remaining targets are marked as done also
					continue

				# if this target is done, skip it
				if target['status'] in ('done', 'aborted'):
					self.logger.info('Target has been done, processing next target')
					continue

				adjustedtarget = self.reportTargetStatus(target, 'processing')

				# this while loop allows target to repeat
				process_status = 'repeat'
				attempt = 0
				while process_status == 'repeat':
					attempt += 1

					# now have processTargetData work on it
					self.startTimer('processTargetData')
					try:
						process_status = self.processTargetData(adjustedtarget, attempt=attempt)
					except targetwatcher.PauseRepeatException, e:
						self.player.pause()
						self.logger.error(str(e) + '... Fix it, then press play to repeat target')
						self.beep()
						process_status = 'repeat'
					except node.PublishError, e:
						self.player.pause()
						self.logger.exception('Saving image failed: %s' % e)
						process_status = 'repeat'
					except Exception, e:
						self.logger.exception('Process target failed: %s' % e)
						process_status = 'exception'
						
					self.stopTimer('processTargetData')

					if process_status != 'exception':
						self.delayReportTargetStatusDone(adjustedtarget)
					else:
						# set targetlist status to abort if exception not user fixable
						targetliststatus = 'aborted'
						self.reportTargetStatus(adjustedtarget, 'aborted')

					# pause check after a good target processing
					state =  self.pauseCheck('paused after processTargetData')
					self.setStatus('processing')
					if state in ('stop', 'stopqueue'):
						self.logger.info('Aborted')
						break
					# end of target repeat loop
				# next target is not a first-image
				self.is_firstimage = False
				# end of target loop
	
			self.applyAverageCorrection(setting)
			if self.good_enough and not self.is_last_target_and_focus_step:
				self.logger.info('Skipping the rest of focus sequence. Defocus accuracy better than %.2f um.' % (self.settings['accuracy limit']*1e6,))
				if self.settings['acquire final']:
					presetdata = self.useFirstPresetOrderPreset()
					self.acquireFinal(presetdata, self.last_emtarget)
			# end of focus sequence loop

	def applyAverageCorrection(self, setting):
		if not setting['switch']:
			return
		# average the results for current
		if setting['correction type'] == 'Defocus' and len(self.corrected_focus) > 0:
			defocus0 = self.instrument.tem.Defocus
			avg_focus = sum(self.corrected_focus) / len(self.corrected_focus)
			self.instrument.tem.Focus = avg_focus
			defocus1 = self.instrument.tem.Defocus
			delta = defocus1 - defocus0
			# individual may be good enough but not collectively.
			if delta > abs(self.settings['accuracy limit']):
				self.good_enough = False
			self.logger.info('Corrected defocus to target average by %.3e' % (delta,))
			self.resetDefocus()
		elif setting['correction type'] == 'Stage Z' and len(self.corrected_stagez) > 0:
			stage0 = self.instrument.tem.StagePosition
			avg_stagez = sum(self.corrected_stagez) / len(self.corrected_stagez)
			self.instrument.tem.StagePosition = {'z':avg_stagez}
			delta = avg_stagez - stage0['z']
			if abs(delta) > abs(self.settings['accuracy limit']):
				self.good_enough = False
			self.logger.info('Corrected stage z to target average by %.3e' % (delta,))
		self.reportDelayedTargetStatusToDone()

	def avoidTargetAdjustment(self,target_to_adjust,recent_target):
		if self.current_focus_sequence_step > 0 or not self.is_firstimage:
			return True
		else:
			return super(Focuser,self).avoidTargetAdjustment(target_to_adjust,recent_target)

	def delayReportTargetStatusDone(self, target):
		self.delayed_targets.append(target)

	def reportDelayedTargetStatusToDone(self):
		for target in self.delayed_targets:
			self.reportTargetStatus(target, 'done')
		self.delayed_targets = []

	def getFocusBeamTilt(self):
		for setting in self.focus_sequence:
			if setting['switch'] and setting['focus method']=='Beam Tilt':
				return setting['tilt']
		return 0.0

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
		'''
		this replaces singlefocuser.Focuser.acquire()
		Instead of doing all sequence of autofocus, we do the one set by
		self.current_focus_sequence_step each time this is called.
		'''
		self.new_acquire = True

		## sometimes have to apply or un-apply deltaz if image shifted on
		## tilted specimen
		if emtarget is None:
			self.deltaz = 0
		else:
			self.deltaz = emtarget['delta z']

		# melt only on the first focus sequence
		if self.current_focus_sequence_step == 0:
			self.setEMtargetAndMeltIce(emtarget, attempt)

		status = 'unknown'

		self.last_emtarget = emtarget
		if self.good_enough:
			message = 'Skipping the rest because it is good enough in focuser.acquire'
			self.logger.info(message)
			self.current_focus_sequence_step = len(self.focus_sequence)
			status = 'ok'
		if self.current_focus_sequence_step in range(len(self.focus_sequence)):
			setting = self.focus_sequence[self.current_focus_sequence_step]
			if not setting['switch']:
				message = 'Skipping focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				status = 'ok'
			else:
				message = 'Processing focus setting \'%s\'...' % setting['name']
				self.logger.info(message)
				self.startTimer('processFocusSetting')
				self.clearBeamPath()
				status = self.processFocusSetting(setting, emtarget=emtarget)
				self.stopTimer('processFocusSetting')
				#Focuser loops every targets for each focus_step
				# Therefore, needs reset after each time processFocusSetting is done.
				is_failed = self.resetComaCorrection()
				## TEST ME
				## repeat status means give up and do the what over ???


		# aquire and save the focus image
		# only done at the last target
		if status != 'repeat' and self.settings['acquire final'] and self.is_last_target_and_focus_step:
			# if autofocus is good enough before reaching last focus_step,
			# this part is not reached.
			self.acquireFinal(presetdata, emtarget)
		return status

	def acquireFinal(self, presetdata, emtarget):
		self.clearBeamPath()
		manualfocuschecker.ManualFocusChecker.acquire(self, presetdata, emtarget)

	def processFocusSetting(self, setting, emtarget=None):
		"""
		Go through one Focus Setting on one emtarget
		"""
		resultdata = leginondata.FocuserResultData(session=self.session)
		resultdata['target'] = emtarget['target']
		resultdata['preset'] = emtarget['preset']
		resultdata['method'] = setting['focus method']
		resultdata['node name'] = self.name
		status = 'unknown'
		# measuremrnt
		try:
			measuretype = setting['focus method']
			meth = self.focus_methods[measuretype]
		except (IndexError, KeyError):
			self.logger.warning('No method selected for correcting defocus')
		else:
			self.startTimer(measuretype)
			status = meth(setting, emtarget, resultdata)
			self.stopTimer(measuretype)
		if status == 'ok' and measuretype != 'Manual':
			# validation
			status = self.validateMeasurementResult(setting, resultdata)
			if status == 'ok':
				# correction of the measure defocus
				self.defocusCorrection(setting, resultdata)
		resultdata['status'] = status
		scopedata = self.instrument.getData(leginondata.ScopeEMData)
		scopedata.insert(force=True)
		resultdata['scope'] = scopedata
		self.publish(resultdata, database=True, dbforce=True)
		stagenow = self.instrument.tem.StagePosition
		self.logger.debug('z after step %s %.2f um' % (setting['name'], stagenow['z']*1e6))
		# record the result for averaging
		correcttype = setting['correction type']
		if correcttype == 'Defocus':
				self.corrected_focus.append(scopedata['focus'])
		if correcttype == 'Stage Z':
				self.corrected_stagez.append(scopedata['stage position']['z'])

		return status

	def defocusCorrection(self,setting, resultdata):
		""" 
		Correct measured defocus. Method of correction depends
		on the correction type.
		"""
		try:
			correcttype = setting['correction type']
			correctmethod = self.correction_types[correcttype]
		except (IndexError, KeyError):
			self.logger.warning('No method selected for correcting defocus')
		else:
			correctmethod(setting, resultdata)
