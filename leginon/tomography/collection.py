import math
import time
import numpy

import leginon.leginondata
import leginon.calibrationclient
import tiltcorrelator
import tiltseries
import traceback
import pyscope.simccdcamera2 #.SimCCDCamera as simcam


class Abort(Exception):
	pass

class Fail(Exception):
	pass

class TrackingError(Exception):
	pass

class TrackingImgError(Exception):
	pass

from prediction import PredictionError

class Collection(object):
	def __init__(self):
		self.tilt_series = None
		# Use two correlators to track positive and negative tilts independently
		self.correlator = {}
		self.correlator[0] = None
		self.correlator[1] = None
		self.instrument_state = None
		self.theta = 0.0
		self.reset_tilt = 0.0

	def saveInstrumentState(self):
		self.instrument_state = self.instrument.getData(leginon.leginondata.ScopeEMData)
		a_state = self.instrument_state['stage position']['a']
		if abs(a_state - self.reset_tilt) > math.radians(1):
			self.logger.error('instrument state saved to %.1f degrees, not %.1f. The last tilt did not return properly.' % (math.degrees(a_state), math.degrees(self.reset_tilt)))

	def restoreInstrumentState(self):
		keys = ['stage position', 'defocus', 'image shift', 'magnification']
		if self.instrument_state is None:
			return
		instrument_state = leginon.leginondata.ScopeEMData()
		for key in keys:
			instrument_state[key] = self.instrument_state[key]
		self.logger.info('stage alpha reset to %.1f' % (instrument_state['stage position']['a']*180.0/3.14159,))
		self.instrument.setData(instrument_state)

	def start(self):
		result = self.initialize()

		if not result:
			self.finalize()
			return

		self.checkAbort()

		self.collect()

		self.finalize()

	def runBufferCycle(self):
		try:
			self.logger.info('Running buffer cycle...')
			self.instrument.tem.runBufferCycle()
		except AttributeError:
			self.logger.warning('No buffer cycle for this instrument')
		except Exception, e:
			self.logger.error('Run buffer cycle failed: %s' % e)

	def calcBinning(self, origsize, min_newsize, max_newsize):
		## new size can be bigger than origsize, no binning needed
		if max_newsize >= origsize:
			return 1
		## try to find binning that will make new image size <= newsize
		bin = origsize / max_newsize
		remain = origsize % max_newsize
		while remain:
			bin += 1
			remain = origsize % bin
			newsize = float(origsize) / bin
			if newsize < min_newsize:
				return None
		return bin

	def initialize(self):
		self.logger.info('Initializing...')

		self.logger.info('Calibrations loaded.')

		self.saveInstrumentState()
		self.logger.info('Instrument state saved.')

		self.prediction.fitdata = self.settings['fit data points'], self.settings['fit data points2']
		self.tilt_series = leginon.tomography.tiltseries.TiltSeries(self.node, self.settings,
												 self.session, self.preset,
												 self.target, self.emtarget)
		self.tilt_series.save()

		if self.settings['use lpf']:
			lpf = 1.5
		else:
			lpf = None
		# bin down images for correlation
		imageshape = self.preset['dimension']
		# use minsize since tiltcorrelator needs it square, will crop the image in there.
		minsize = min((imageshape['x'],imageshape['y']))
		if minsize > 512:
			correlation_bin = self.calcBinning(minsize, 256, 512)
		else:
			correlation_bin = 1
		if correlation_bin is None:
			# use a non-dividable number and crop in the correlator
			correlation_bin = int(math.ceil(minsize / 512.0))
		self.correlator[0] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		self.correlator[1] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)

		if self.settings['run buffer cycle']:
			self.runBufferCycle()

		return True

	def collect(self):
		n = len(self.tilts)
		self.node.logger.info('collect %d tilt groups' % n)

		# TODO: move to tomography
		if n != len(self.exposures):
			raise RuntimeError('tilt angles and exposure times do not match')

		for i in range(n):
			if len(self.tilts[i]) != len(self.exposures[i]):
				s = 'tilt angle group #%d and exposure time group do not match'
				s %= i + 1
				raise RuntimeError(s)

		# initialize prediction
		self.prediction.newTiltSeries()
		for g in range(n):
			self.prediction.newTiltGroup()

		# Collect according to tilt_index_sequence.
		if self.tilt_order == 'sequential' and len(self.tilts) == 2:
			self.sequentialLoop()
		else:			
			self.loop(self.tilts, self.exposures, self.tilt_index_sequence)

	def sequentialLoop(self):
		break1 = len(self.tilts[0])
		self.loop(self.tilts, self.exposures, self.tilt_index_sequence[:break1])
		if break1 < len(self.tilt_index_sequence):
			self.initLoop2()
			self.loop(self.tilts, self.exposures, self.tilt_index_sequence[break1:])
		self.finalize()

	def finalize(self):
		self.tilt_series = None

		self.correlator[0].reset()
		self.correlator[1].reset()

		self.restoreInstrumentState()
		self.instrument_state = None

		self.logger.info('Data collection ended.')
		self.setStatus('idle')

		self.viewer.clearImages()

	def initLoop2(self):
		self.restoreInstrumentState()
		self.correlator[1].reset()
		if True:
			self.logger.info('Adjust target for the second tilt group...')
			try:
				self.emtarget, status = self.node.adjusttarget(self.preset['name'], self.target, self.emtarget)
			except Exception, e:
				self.logger.error('Failed to adjust target: %s.' % e)
				self.finalize()
				raise
			if status == 'error':
				self.finalize()
		return

	def loop(self, tilts, exposures, sequence):
		self.logger.info('Starting tilt collection (%d angles)...' % len(sequence))
		self.logger.info('Removing tilt backlash...')
		try:
			self.node.removeStageAlphaBacklash(tilts, sequence, self.preset['name'], self.target, self.emtarget)
		except Exception, e:
			self.logger.error('Failed to remove backlash: %s.' % e)
			self.finalize()
			raise

		self.checkAbort()

		self._loop(tilts, exposures, sequence)
		
		self.logger.info('Collection loop completed.')

	def _loop(self, tilts, exposures, sequence):
		'''
		Loop through sequence
		'''
		# tilts and exposures are grouped
		# sequence is the 2 element tuple used to choose the tilt and the exposure		
		image_pixel_size = self.pixel_size*self.preset['binning']['x']

		seq0 = sequence[0]
		tilt0 = tilts[seq0[0]][seq0[1]]
		position0 = self.node.getPixelPosition('image shift')
		defocus0 = self.node.getDefocus()
		
		m = 'Initial feature position: %g, %g pixels.'
		self.logger.info(m % (position0['x'], position0['y']))
		m = 'Initial defocus: %g meters.'
		self.logger.info(m % defocus0)

		if self.tilt_order in ('alternate','swing') and len(tilts) > 1:
			# duplicate the first tilt to the other tilt group
			other_group = int(not seq0[0])
			self.prediction.setCurrentTiltGroup(other_group)
			self.prediction.addPosition(tilt0, position0)
		
		self.prediction.setCurrentTiltGroup(seq0[0])
		self.prediction.addPosition(tilt0, position0)
		
		position = dict(position0)
		defocus = defocus0

		abort_loop = False
		for seq_index in range(len(sequence)):
			self.checkAbort()
			seq = sequence[seq_index]
			tilt = tilts[seq[0]][seq[1]]

			self.logger.info('Current tilt angle: %g degrees.' % math.degrees(tilt))
			try:
				self.prediction.setCurrentTiltGroup(seq[0])
				predicted_position = self.prediction.predict(tilt)
			except:
				raise
			self.checkAbort()

			predicted_shift = {}
			predicted_shift['x'] = predicted_position['x'] - position['x']
			predicted_shift['y'] = predicted_position['y'] - position['y']

			# undo defocus from last tilt
			predicted_shift['z'] = -defocus

			defocus = defocus0 + predicted_position['z']*image_pixel_size
			self.logger.info('defocus0: %g meters,sintilt: %g' % (defocus0,math.sin(tilt)))
			# apply new defocus
			predicted_shift['z'] += defocus

			try:
				self.node.setPosition('image shift', predicted_position)
			except Exception, e:
				self.logger.error('Calibration error: %s' % e) 
				self.finalize()
				raise Fail

			m = 'Predicted position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (predicted_position['x'],
								  predicted_position['y'],
								  predicted_position['x']*image_pixel_size,
								  predicted_position['y']*image_pixel_size))
			self.logger.info('Predicted defocus: %g meters.' % defocus)

			self.node.setDefocus(defocus)

			if self.settings['measure defocus']:
				defocus_measurement = self.node.measureDefocus()
				measured_defocus = defocus0 - (defocus + defocus_measurement[0])
				measured_fit = defocus_measurement[1]
				self.logger.info('Measured defocus: %g meters.' % measured_defocus)
				self.logger.info('Predicted defocus: %g meters.' % defocus)
			else:
				measured_defocus = None
				measured_fit = None

			self.checkAbort()

			exposure = exposures[seq[0]][seq[1]]
			m = 'Acquiring image (%g second exposure)...' % exposure
			self.logger.info(m)
			self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

			self.checkAbort()

			self.logger.info('Pausing for %.1f seconds before starting acquiring' % self.settings['tilt pause time']) 
			time.sleep(self.settings['tilt pause time'])

			# TODO: error checking
			channel = self.correlator[seq[0]].getChannel()
			image_data = self.node.acquireCorrectedCameraImageData(channel)
			if image_data is None:
				self.finalize()
				raise Fail
			self.logger.info('Image acquired.')

			image_mean = image_data['image'].mean()
			if self.settings['integer']:
				intscale = self.settings['intscale']
				image_data['image'] = numpy.around(image_data['image']*intscale).astype(numpy.int16)
				image_mean *= intscale

			image = image_data['image']

			if image_mean < self.settings['mean threshold']:
				if seq[1] < (self.settings['collection threshold']/100.0)*len(tilts):
					self.logger.error('Image counts below threshold (mean of %.1f, threshold %.1f), aborting series...' % (image_mean, self.settings['mean threshold']))
					self.finalize()
					raise Abort
				else:
					self.logger.warning('Image counts below threshold, aborting loop...')
					self.restoreInstrumentState()
					break

			self.logger.info('Saving image...')
			# notify manager on every image.
			self.node.notifyNodeBusy()
			while True:
				try:
					tilt_series_image_data = self.tilt_series.saveImage(image_data)
					break
				except Exception, e:
					self.logger.warning('Retrying save image: %s.' % (e,))
					raise
				for tick in range(60):
					self.checkAbort()
					time.sleep(1.0)
			filename = tilt_series_image_data['filename']
			self.logger.info('Image saved (filename: \'%s\').' % filename)

			self.checkAbort()

			self.viewer.addImage(image)

			self.checkAbort()

			# Move to next tilt while correlating to allow stage to settle
			try:
				next_tilt = tilts[sequence[seq_index+1][0]][sequence[seq_index+1][1]]
				s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(next_tilt)
				self.logger.info(s)
				stage_position = {'a': next_tilt}
				self.instrument.tem.StagePosition = stage_position
			except IndexError:
				pass

			self.checkAbort()
			
			self.logger.info('Correlating image with previous tilt...')
			self.correlator.setTiltAxis(predicted_position['phi'])
			while True:
				try:
					correlation_image = self.correlator[seq[0]].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
					break
				except Exception, e:
					self.logger.warning('Retrying correlate image: %s.' % (e,))
				for tick in range(15):
					self.checkAbort()
					time.sleep(1.0)

			if seq_index == 0: 
				if self.tilt_order in ('alternate','swing'):
					other_group = int(not seq[0])
					fake_corr_image = self.correlator[other_group].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
		
			phi, optical_axis, z0 = self.prediction.getCurrentParameters()
			phi,offset = self.prediction.convertparams(phi,optical_axis)
			correlation = self.correlator[seq[0]].getShift(False)

			if self.settings['use tilt']:
				correlation = self.correlator[seq[0]].tiltShift(tilt,correlation,phi)

			position = {
				'x': predicted_position['x'] - correlation['x'],
				'y': predicted_position['y'] - correlation['y'],
			}

			self.prediction.addPosition(tilt, position)

			m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (correlation['x'],
								  correlation['y'],
								  correlation['x']*image_pixel_size,
								  correlation['y']*image_pixel_size))

			m = 'Feature position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (position['x'],
								  position['y'],
								  position['x']*image_pixel_size,
								  position['y']*image_pixel_size))
			raw_correlation = self.correlator[seq[0]].getShift(True)
			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC(correlation_image, s)
			if self.settings['use tilt']:
				raw_correlation = self.correlator[seq[0]].tiltShift(tilt,raw_correlation,phi)

			self.checkAbort()

			time.sleep(3.0)

			self.checkAbort()

			args = (
				predicted_position,
				predicted_shift,
				position,
				correlation,
				raw_correlation,
				image_pixel_size,
				tilt_series_image_data,
				seq[0],
				measured_defocus,
				measured_fit,
			)
			self.savePredictionInfo(*args)

			self.checkAbort()

			if abort_loop:
				self.restoreInstrumentState()
				break

		self.viewer.clearImages()

	def savePredictionInfo(self, predicted_position, predicted_shift, position, correlation, raw_correlation, image_pixel_size, image, prediction_tilt_group, measured_defocus=None, measured_fit=None):
		initializer = {
			'session': self.node.session,
			'predicted position': predicted_position,
			'predicted shift': predicted_shift,
			'position': position,
			'correlation': correlation,
			'raw correlation': raw_correlation,
			'pixel size': image_pixel_size,
			'image': image,
			'measured defocus': measured_defocus,
			'measured fit': measured_fit,
			'tilt group': prediction_tilt_group,
		}
		tomo_prediction_data = leginon.leginondata.TomographyPredictionData(initializer=initializer)
					
		self.node.publish(tomo_prediction_data, database=True, dbforce=True)

	def checkAbort(self):
		if self.player.state() == 'pause':
			self.setStatus('user input')
		state = self.player.wait()
		if state in ('stop', 'stopqueue', 'stoptarget'):
			self.finalize()
			raise Abort

class Collection_2(Collection):
	def __init__(self):
		super(Collection_2,self).__init__()
		self.doPredict = None
		self.trackingImg = None
		self.correlator[2] = None			# tracking correlator used in Collection_2
		self.correlator[3] = None

		self.istot = {0:{'x':[],'y':[]},1:{'x':[],'y':[]}} 		# accumulated image shift 	
		self.ntrack = {0:0,1:0}									# number of iterations last tracking image was taken
		self.ntrackmax = 4										# maximum number of iterations before we have to take another tracking image
		self.offset = None
		self.trackpreset = None
		self.fulltrack = False
		
	def initialize(self):
		self.logger.info('Initializing...')

		self.logger.info('Calibrations loaded.')

		self.saveInstrumentState()
		self.logger.info('Instrument state saved.')

		self.prediction.fitdata = self.settings['fit data points'], self.settings['fit data points2']
		self.tilt_series = leginon.tomography.tiltseries.TiltSeries(self.node, self.settings,
												 self.session, self.preset,
												 self.target, self.emtarget)
		self.tilt_series.save()

		if self.settings['use lpf']:
			lpf = 1.5
		else:
			lpf = None
		# bin down images for correlation
		imageshape = self.preset['dimension']
		# use minsize since tiltcorrelator needs it square, will crop the image in there.
		minsize = min((imageshape['x'],imageshape['y']))
		if minsize > 512:
			correlation_bin = self.calcBinning(minsize, 256, 512)
		else:
			correlation_bin = 1
		if correlation_bin is None:
			# use a non-dividable number and crop in the correlator
			correlation_bin = int(math.ceil(minsize / 512.0))
		self.correlation_bin = correlation_bin
		self.correlator[0] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		self.correlator[1] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		self.correlator[2] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		self.correlator[3] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		
		self.trackoffset = None
		
		if self.settings['run buffer cycle']:
			self.runBufferCycle()

		return True
	
	def get_istot(self,seq):
		return self.istot[seq[0]]
	
	def update_istot(self,seq,shift,append=True):
		if append:
			self.istot[seq[0]]['x'].append(shift['x'])
			self.istot[seq[0]]['y'].append(shift['y'])
		else:
			self.istot[seq[0]]['x'][-1] += shift['x']
			self.istot[seq[0]]['y'][-1] += shift['y']
		
	def reset_is(self,seq):
		self.istot[seq[0]]['x'] = []
		self.istot[seq[0]]['y'] = []
		self.reset_ntrack(seq)
	
	def reset_ntrack(self,seq):
		self.ntrack[seq[0]] = 0
	
	def increment_ntrack(self,seq):
		self.ntrack[seq[0]] += 1
	
	def dotrackimg(self,seq):
		if self.ntrack[seq[0]] < self.ntrackmax:
			return False
		else:
			return True
	
	def finalize(self):
		self.tilt_series = None

		self.correlator[0].reset()
		self.correlator[1].reset()
		self.correlator[2].reset()
		self.correlator[3].reset()
		self.reset_is((0,))
		self.reset_is((1,))
		
		self.restoreInstrumentState()
		self.instrument_state = None

		self.logger.info('Data collection ended.')
		self.setStatus('idle')

		self.viewer.clearImages()
	
	def loop(self, tilts, exposures, sequence):
		self.logger.info('Starting tilt collection (%d angles)...' % len(sequence))
		
		self.logger.info('Removing tilt backlash...')
		try:
			self.node.removeStageAlphaBacklash(tilts, sequence, self.preset['name'], self.target, self.emtarget)
		except Exception, e:
			self.logger.error('Failed to remove backlash: %s.' % e)
			self.finalize()
			raise
	
		dim = min(self.preset['dimension'].values())		# get dimension of image at exposure preset. 
		self.prediction.setcutoff(math.sqrt(2)*dim*0.02)	# set prediction threshold at 5% of image size
		self.checkAbort()

		self._loop(tilts, exposures, sequence)
		
		self.logger.info('Collection loop completed.')

		
	def _loop(self, tilts, exposures, sequence):
		'''
		Loop through sequence
		'''		
		img0 = None
		# tilts and exposures are grouped
		# sequence is the 2 element tuple used to choose the tilt and the exposure
		image_pixel_size = self.pixel_size*self.preset['binning']['x']

		seq0 = sequence[0]
		tilt0 = tilts[seq0[0]][seq0[1]]
		position0 = self.node.getPixelPosition('image shift')
		defocus0 = self.node.getDefocus()
		
		m = 'Initial feature position: %g, %g pixels.'
		self.logger.info(m % (position0['x'], position0['y']))
		m = 'Initial defocus: %g meters.'
		self.logger.info(m % defocus0)

		# TODO: figure out the next block of code. 
		#if self.tilt_order in ('alternate','swing') and len(tilts) > 1:		
			# duplicate the first tilt to the other tilt group
		#	other_group = int(not seq0[0])
		#	self.prediction.setCurrentTiltGroup(other_group)
		#	self.prediction.addPosition(tilt0, position0)
		
		self.prediction.setCurrentTiltGroup(seq0[0])		
		position = dict(position0)
		position0 = dict(position0)
		defocus = defocus0
		
		abort_loop = False
		for seq_index in range(len(sequence)):
			self.checkAbort()
			seq = sequence[seq_index]
			tilt = tilts[seq[0]][seq[1]]

			try:
				channel = self.correlator[seq[0]].getChannel()
				self.prediction.setCurrentTiltGroup(seq[0])
				ispredict = self.prediction.ispredict()							# can we rely on prediction? 
					
				if seq_index == 0:	
					self.logger.info('Starting tilt angle: %g degrees.' % math.degrees(tilt))
					self.tilt(tilt)
					predicted_position = position0								# first position
					predicted_position['z'] = 0 								# assumes that eucentric error z0 is 0.  
					self.update_istot(seq0,position0)							
					self.trackingImg = self.getTrackingImg()					# get first tracking image	
					self.reset_ntrack(seq)			
					
					# add first tracking image into correlator buffer
					self.correlator[seq[0]+2].reset()							# clear buffer
					# The next line adds the first tracking image to the correlator and returns None. 
					firstcorrelation_image = self.correlator[seq[0]+2].correlate(self.trackingImg,\
								self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')	
					if seq_index == 0: 
						if self.tilt_order in ('alternate','swing'):
							other_group = int(not seq[0])
							fake_corr_image = self.correlator[other_group+2].correlate(self.trackingImg,\
								self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')	
							self.reset_ntrack((other_group,0))
				elif self.fulltrack or not ispredict:		
					print "****TRACKING****"											 
					# tilt to current tilt angle. 
					self.tilt(tilt)
					# acquire tracking image, correlate with previous tracking image. 		
					tracked_shift = self.track(tilt,seq)						# this is in pixels for exposure mag. 
					#tracked_shift['x'] *= numpy.cos(tilt)
					istot = self.get_istot(seq)								# history of previous shifts
					
					predicted_position = {}
					# tracked_shift has to be corrected by total image shifts applied up to now
					predicted_position['x'] = tracked_shift['x'] + sum(istot['x'])
					predicted_position['y'] = tracked_shift['y'] + sum(istot['y'])
					
					# TODO: actually implement something for z heights
					predicted_position['z'] = tracked_shift['z'] 
					print 'previous x: %f, y: %f' %(position['x'],position['y'])
					print 'tracked x: %f, y: %f' %(predicted_position['x'],predicted_position['y'])
					print 'tracked shift x: %f, y: %f' %(predicted_position['x']-position['x'],predicted_position['y']-position['y'])
					print 
				else:
					# tilt to current tilt angle. 
					print "****PREDICTING****"
					self.tilt(tilt)
					predicted_position = self.prediction.predict(tilt,seq)		# predict shift with linear model.
					if not self.dotrackimg(seq):							
						self.ntrack[seq[0]] += 1
					else:														# we need to take a tracking image every so often
						self.trackingImg = self.getTrackingImg()
						trackingcorrelation_image = self.correlator[seq[0]+2].correlate(self.trackingImg,\
								self.settings['use tilt'], channel=channel, wiener=False, taper=0)	
						self.reset_ntrack(seq)
						
					print 'previous x: %f, y: %f' %(position['x'],position['y'])
					print 'predicted x: %f, y: %f' %(predicted_position['x'],predicted_position['y'])
					print 'predicted shift x: %f, y: %f' %(predicted_position['x']-position['x'], predicted_position['y']-position['y'])
					print 
					
			except TrackingError:
				self.logger.error('Failed to track. Aborting tilt series')
				raise Abort
			except PredictionError:
				self.logger.error('Failed to predict. Aborting tilt series')
				raise Abort
			except Exception:
				print "Caught exception\n"
				traceback.print_exc()
				self.finalize()
				raise Abort	

			self.checkAbort()
			predicted_shift = {}
			predicted_shift['x'] = predicted_position['x'] - position['x']
			predicted_shift['y'] = predicted_position['y'] - position['y']
			
			self.update_istot(seq,predicted_shift)								# add to total image shift
			print "istot_x: %f: istot_y: %f" \
					%(sum(self.get_istot(seq)['x']),sum(self.get_istot(seq)['y']))
			# undo defocus from last tilt
			predicted_shift['z'] = -defocus

			defocus = defocus0 + predicted_position['z']*image_pixel_size		# currently, predicted z is set to initial z0, which is assumed to be 0
			self.logger.info('defocus0: %g meters,sintilt: %g' % (defocus0,math.sin(tilt)))
			# apply new defocus
			predicted_shift['z'] += defocus
			
			try:
				self.node.setPosition('image shift', predicted_position)
			except Exception, e:
				self.logger.error('Calibration error: %s' % e) 
				self.finalize()
				raise Fail

			if ispredict: 
				m = 'Predicted position: %g, %g pixels, %g, %g meters.'
			else: 
				m = 'Tracked position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (predicted_position['x'],
								  predicted_position['y'],
								  predicted_position['x']*image_pixel_size,
								  predicted_position['y']*image_pixel_size))			
			self.logger.info('Predicted defocus: %g meters.' % defocus)

			self.node.setDefocus(defocus)
			
			#TODO: implement defocus measurement 
			if self.settings['measure defocus']:
				defocus_measurement = self.node.measureDefocus()
				measured_defocus = defocus0 - (defocus + defocus_measurement[0])
				measured_fit = defocus_measurement[1]
				self.logger.info('Measured defocus: %g meters.' % measured_defocus)
				self.logger.info('Predicted defocus: %g meters.' % defocus)
			else:
				measured_defocus = None
				measured_fit = None
			
			self.checkAbort()
			
			exposure = exposures[seq[0]][seq[1]]
			m = 'Acquiring image (%g second exposure)...' % exposure
			self.logger.info(m)
			self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

			self.checkAbort()

			self.logger.info('Pausing for %.1f seconds before starting acquiring' % self.settings['tilt pause time']) 
			time.sleep(self.settings['tilt pause time'])

			image_data = self.node.acquireCorrectedCameraImageData(channel)
			if image_data is None:
				self.finalize()
				raise Fail
			self.logger.info('Image acquired.')

			image_mean = image_data['image'].mean()
			if self.settings['integer']:
				intscale = self.settings['intscale']
				image_data['image'] = numpy.around(image_data['image']*intscale).astype(numpy.int16)
				image_mean *= intscale
			
			if image_mean < self.settings['mean threshold']:
				if seq[1] < (self.settings['collection threshold']/100.0)*len(tilts):
					self.logger.error('Image counts below threshold (mean of %.1f, threshold %.1f), aborting series...' % (image_mean, self.settings['mean threshold']))
					self.finalize()
					raise Abort
				else:
					self.logger.warning('Image counts below threshold, aborting loop...')
					self.restoreInstrumentState()
					break
			
			self.logger.info('Saving image...')
			# notify manager on every image.
			self.node.notifyNodeBusy()
			while True:
				try:
					tilt_series_image_data = self.tilt_series.saveImage(image_data)
					break
				except Exception, e:
					self.logger.warning('Retrying save image: %s.' % (e,))
					raise
				for tick in range(60):
					self.checkAbort()
					time.sleep(1.0)
			filename = tilt_series_image_data['filename']
			self.logger.info('Image saved (filename: \'%s\').' % filename)

			self.checkAbort()
			
			image = image_data['image']
			self.viewer.addImage(image)

			self.checkAbort()
			
			self.logger.info('Correlating image with previous tilt...')
			"""
			phi, optical_axis, z0 = self.prediction.getCurrentParameters()
			phi,offset = self.prediction.convertparams(phi,optical_axis)
			"""		
			while True:
				try:
					correlation_image = self.correlator[seq[0]].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
					break
				except Exception, e:
					self.logger.warning('Retrying correlate image: %s.' % (e,))
				for tick in range(15):
					self.checkAbort()
					time.sleep(1.0)

			if seq_index == 0: 
				if self.tilt_order in ('alternate','swing'):
					other_group = int(not seq[0])
					fake_corr_image = self.correlator[other_group].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
		
			raw_correlation = self.correlator[seq[0]].getShift(True)					# get raw correlation
			correlation = self.correlator[seq[0]].getShift(False)						# get raw correlation
			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC(correlation_image, s)
			#if self.settings['use tilt']:
			#	correlation = self.correlator[seq[0]].tiltShift(tilt,correlation,phi)
			measured_position = {														# measured position 
				'x': predicted_position['x'] - (correlation['x']),	
				'y': predicted_position['y'] - (correlation['y']),
			}
			position = {																# current image shift position 
				'x': predicted_position['x'],	
				'y': predicted_position['y'],
			}
			print "****AFTER IMAGE CORRELATION****"
			if ispredict:
				print 'predicted x: %f, y: %f' %(predicted_position['x'],predicted_position['y'])
			else:
				print 'tracked x: %f, y: %f' %(predicted_position['x'],predicted_position['y'])
			print 'correlation x: %f, y: %f' %((correlation['x']),(correlation['y']))
			print 'measured position x: %f, y: %f' %(measured_position['x'],measured_position['y'])
			print
			
			if not ispredict:
				predicted_position = self.prediction.predict(tilt,seq)						# still predict position, just don't rely on it. 				

				print 'predicted x:' 
				print predicted_position['x']
				print 'predicted y:' 
				print predicted_position['y']
				self.prediction.addPosition(tilt, measured_position, predicted_position) 	# Add measured and predicted position. 
				
			else:
				predicted_position = self.prediction.predict(tilt,seq)						# Without adjusting for accumulated correlation shifts.  				
				self.prediction.addPosition(tilt, measured_position, predicted_position)
			
			m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (correlation['x'],
								  correlation['y'],
								  correlation['x']*image_pixel_size,
								  correlation['y']*image_pixel_size))

			m = 'Feature position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (position['x'],
								  position['y'],
								  position['x']*image_pixel_size,
								  position['y']*image_pixel_size))
			
			#if self.settings['use tilt']:
			#	raw_correlation = self.correlator[seq[0]].tiltShift(tilt,raw_correlation,phi)

			self.checkAbort()

			time.sleep(3.0)

			self.checkAbort()

			args = (
				predicted_position,
				predicted_shift,
				position,
				correlation,
				raw_correlation,
				image_pixel_size,
				tilt_series_image_data,
				seq[0],
				measured_defocus,
				measured_fit,
			)
			self.savePredictionInfo(*args)

			self.checkAbort()

			if abort_loop:
				self.restoreInstrumentState()
				break
		
		self.viewer.clearImages()
		self.reset_is(seq)

	def getTrackingImg(self,maxtries=5):
		# (1) Change to tracking preset, taking into acount current position and offset.
		# (2) Take an image.
		isoffset = self.node.getImageShiftOffset()
		try:
			self.logger.info('Acquiring tracking image.')
			self.change2Track()												# (1) 
			imagedata = self.node.acquireCorrectedCameraImageData(0)		# (2)
			self.viewer.addImage(imagedata['image'])
			self.return2Tomo(isoffset)
		except:
			raise TrackingImgError
		return imagedata
	
	def change2Track(self):
		# This function follows the procedure in presets.PresetManager.targetToScope
		# (1) Get current image shift offset relative to tomo preset.
		# (2) Convert to track preset pixels.
		# (3) Convert track offset from parent preset .
		# (4) Combine both is.
		# (5) Send to scope. 
		
		mypreset = self.preset
		parentpreset = self.parentpreset
		trackpreset = self.trackpreset
		#trackpreset_name = self.offset['trackpreset']
		#trackpreset = self.node.presetsclient.getPresetByName(trackpreset_name)
		
		myoffset = self.node.getImageShiftOffset()		# (1)
		
		myscope = leginon.leginondata.ScopeEMData()		
		myscope.friendly_update(mypreset)
		mycam = leginon.leginondata.CameraEMData()
		mycam.friendly_update(mypreset)
		parentscope = leginon.leginondata.ScopeEMData()
		parentscope.friendly_update(parentpreset)
		parentcam = leginon.leginondata.CameraEMData()
		parentcam.friendly_update(parentpreset)
		trackscope = leginon.leginondata.ScopeEMData()
		trackscope.friendly_update(trackpreset)
		trackcam = leginon.leginondata.CameraEMData()
		trackcam.friendly_update(trackpreset)

		my_tem = mypreset['tem']
		my_ccdcamera = mypreset['ccdcamera']
		my_mag = mypreset['magnification']
		parent_tem = parentpreset['tem']
		parent_ccdcamera = parentpreset['ccdcamera']
		parent_mag = parentpreset['magnification']
		track_tem = trackpreset['tem']
		track_ccdcamera = trackpreset['ccdcamera']
		track_mag = trackpreset['magnification']
		ht = self.node.instrument.tem.HighTension
		
		# x,y dict input col, row, dict output, binned
		p1_shift = self.node.calclients['image shift'].itransform(myoffset, myscope, mycam)		# binned
		p1_row = p1_shift['row'] * mypreset['binning']['y']		# unbinned
		p1_col = p1_shift['col'] * mypreset['binning']['x']
		# row, col list or array input, row, col array out
		p1_vec = numpy.array((p1_row, p1_col))
		# image shift coil rotation
		p1_vec = self.node.imageRotationTransform(p1_vec,mypreset,trackpreset,ht)	# unbinned
		# magnification and camera (if camera is different)
		# Transform pixelvect1 at magnification to new magnification according to image-shift matrix
		# include a relative  image rotation and scale addition to the transform
		p2_vec = self.node.calclients['image rotation'].pixelToPixel(my_tem,\
			my_ccdcamera,track_tem, track_ccdcamera, ht,my_mag,track_mag,p1_vec)	# unbinned
		
		p2_shift = {'row':p2_vec[0] / trackpreset['binning']['y'],					# (2)
					'col':p2_vec[1] / trackpreset['binning']['x']}
																							
		p3_shift = self.getTrackOffset() 											# (3) binned at track preset 	
		# offset in binned pixels to be applied once we change to track preset
		isoffset_shift = {'row':p2_shift['row'] + -p3_shift['row'],					
							'col':p2_shift['col'] + -p3_shift['col']}				# (4)

		isoffset = self.node.calclients['image shift'].transform(isoffset_shift, trackscope, trackcam)['image shift']
		self.node.presetsclient.toScope(self.trackpreset['name'])
		self.node.setImageShiftOffset(isoffset)										# (5)	
	
	def getTrackOffset(self):
		# Get is offset to be applied once the scope has been sent to track preset.
		# This is in addition to is offset going from tomo to track. 

		if self.trackoffset:
			return self.trackoffset
		else:
			parentpreset = self.target['preset']
			trackpreset = self.trackpreset
			
			trackoffset = self.offset['trackoffset']		# pixels relative to parent preset
			
			parentscope = leginon.leginondata.ScopeEMData()
			parentscope.friendly_update(parentpreset)
			parentcam = leginon.leginondata.CameraEMData()
			parentcam.friendly_update(parentpreset)
			trackscope = leginon.leginondata.ScopeEMData()
			trackscope.friendly_update(trackpreset)
			trackcam = leginon.leginondata.CameraEMData()
			trackcam.friendly_update(trackpreset)
	
			parent_tem = parentpreset['tem']
			parent_ccdcamera = parentpreset['ccdcamera']
			parent_mag = parentpreset['magnification']
			track_tem = trackpreset['tem']
			track_ccdcamera = trackpreset['ccdcamera']
			track_mag = trackpreset['magnification']
			ht = self.node.instrument.tem.HighTension
			# row, col list or array input, row, col array out
			p1_row = trackoffset[0] * parentpreset['binning']['y']
			p1_col = trackoffset[1] * parentpreset['binning']['x']
			p1_vec = numpy.array([p1_row,p1_col])
			# image shift coil rotation
			p1_vec = self.node.imageRotationTransform(p1_vec,parentpreset,trackpreset,ht)
			# magnification and camera (if camera is different)
			# Transform pixelvect1 at magnification to new magnification according to image-shift matrix
			# include a relative  image rotation and scale addition to the transform
			p2_vec = self.node.calclients['image rotation'].pixelToPixel(parent_tem,
				parent_ccdcamera,track_tem, track_ccdcamera, ht,parent_mag,track_mag,p1_vec)
			p2_shift = {'row':p2_vec[0] / trackpreset['binning']['y'],
					'col':p2_vec[1] / trackpreset['binning']['x']}
			self.trackoffset = p2_shift
			return p2_shift

	def getTomoOffset(self, offset):
		# Get is offset to be applied once the scope has been sent back to tomo preset
		# after tracking. 
		mypreset = self.preset
		trackpreset = self.trackpreset

		track_tem = trackpreset['tem']
		track_ccdcamera = trackpreset['ccdcamera']
		track_mag = trackpreset['magnification']
		
		my_tem = mypreset['tem']
		my_ccdcamera = mypreset['ccdcamera']
		my_mag = mypreset['magnification']
		
		# row, col list or array input, row, col array out
		p1_row = offset[0] * trackpreset['binning']['y']
		p1_col = offset[1] * trackpreset['binning']['x']
		p1_vec = numpy.array([p1_row,p1_col])
		# image shift coil rotation
		p1_vec = self.imageRotationTransform(p1_vec, trackpreset, mypreset)
		# magnification and camera (if camera is different)
		# Transform pixelvect1 at magnification to new magnification according to image-shift matrix
		# include a relative  image rotation and scale addition to the transform
		p2_vec = self.calclients['image rotation'].pixelToPixel(track_tem,
			track_ccdcamera,my_tem, my_ccdcamera, ht,track_mag,my_mag,p1_vec)
		return p2_vec
	
	def track(self,tilt,seq):
		try:
			
			channel = self.correlator[seq[0]].getChannel()
			trackingImg = self.getTrackingImg()
			# Cross correlate with previous tracking image. 
			self.logger.info('Correlating with previous tracking image.')
			assert self.trackingImg is not None		# make sure we have a previous tracking image to compare to. 
			assert self.correlator[seq[0]+2].correlation.buffer[1]['image'] is not None
			
			correlation_image = self.correlator[seq[0]+2].correlate(trackingImg, \
								self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')
				
			phi, optical_axis, z0 = self.prediction.getCurrentParameters()
			phi, offset = self.prediction.convertparams(phi,optical_axis)
			raw_correlation = self.correlator[seq[0]+2].getShift(True)						# get raw correlation
			correlation = self.correlator[seq[0]+2].getShift(False)
			#if self.settings['use tilt']:													# This does not do anything. 
			#	correlation = self.correlator[seq[0]+2].tiltShift(tilt,correlation,phi)		# TODO: unstretch image. 
			self.trackingImg = trackingImg			
			
			# need to convert from tracking coordinates to exposure coordinates. 
			mypreset = self.preset
			trackpreset = self.trackpreset	
			tem1 = trackpreset['tem']
			ccdcamera1 = trackpreset['ccdcamera']
			mag1 = trackpreset['magnification']
			tem2 = mypreset['tem']
			ccdcamera2 = mypreset['ccdcamera']
			mag2 = mypreset['magnification']
			ht = self.instrument.tem.HighTension	
			p1 = [correlation['x'], correlation['y']]
			
			print "CORRELATION x: %f y: %f" %(correlation['x'], correlation['y'])
			#TODO: we need to account for binning on both track and tomo, also rotation. 

			myscope = leginon.leginondata.ScopeEMData()
			myscope.friendly_update(mypreset)
			mycam = leginon.leginondata.CameraEMData()
			mycam.friendly_update(mypreset)

			trackscope = leginon.leginondata.ScopeEMData()
			trackscope.friendly_update(trackpreset)
			trackcam = leginon.leginondata.CameraEMData()
			trackcam.friendly_update(trackpreset)
	
			my_tem = mypreset['tem']
			my_ccdcamera = mypreset['ccdcamera']
			my_mag = mypreset['magnification']

			track_tem = trackpreset['tem']
			track_ccdcamera = trackpreset['ccdcamera']
			track_mag = trackpreset['magnification']
			ht = self.node.instrument.tem.HighTension
			
			# x,y dict input col, row, dict output, binned
			p1_row = correlation['y'] * trackpreset['binning']['y']		# unbinned
			p1_col = correlation['x'] * trackpreset['binning']['x']
			# row, col list or array input, row, col array out
			p1_vec = numpy.array((p1_row, p1_col))
			# image shift coil rotation
			p1_vec = self.node.imageRotationTransform(p1_vec,trackpreset,mypreset,ht)	# unbinned
			# magnification and camera (if camera is different)
			# Transform pixelvect1 at magnification to new magnification according to image-shift matrix
			# include a relative  image rotation and scale addition to the transform
			p2_vec = self.node.calclients['image rotation'].pixelToPixel(track_tem, track_ccdcamera, \
								my_tem, my_ccdcamera, ht, track_mag, my_mag, p1_vec)	# unbinned
			
			p2_shift = {'row':p2_vec[0] / mypreset['binning']['y'],
						'col':p2_vec[1] / mypreset['binning']['x']}
			
			correlation['x'] = p2_shift['col']
			correlation['y'] = p2_shift['row']
			print "CORRELATION after pixelToPixel x: %f y: %f" %(correlation['x'], correlation['y'])
			
			result = {
				'x': -correlation['x'],			# This is in exposure pixels. 
				'y': -correlation['y'],
				'z': 0,		#TODO: need to predict z from eucentric error and optical axis offset and shift during tilt? 
			}
			self.reset_ntrack(seq)
		except Exception as e :
			if e.__class__.__name__ == 'TrackingImageError':
				raise TrackingImageError
			else:
				raise TrackingError
		return result		
	
	def tilt(self, ang):
		try:
			s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(ang)
			self.logger.info(s)
			stage_position = {'a': ang}
			self.instrument.tem.StagePosition = stage_position
		except IndexError:
			pass

		self.checkAbort()
					
	def return2Tomo(self,isoffset):
		# return to tomography preset
		self.node.presetsclient.toScope(self.preset['name'])
		self.node.setImageShiftOffset(isoffset)				# apply image shift to instrument. 
	
	
	
	
	
	
