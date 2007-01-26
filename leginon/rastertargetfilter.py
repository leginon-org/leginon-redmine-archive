import targetfilter
import data
import gui.wx.RasterTargetFilter
import presets
import calibrationclient
import raster
import instrument

class RasterTargetFilter(targetfilter.TargetFilter):
	'''
	Example of a TargetFilter subclass
	'''
	panelclass = gui.wx.RasterTargetFilter.Panel
	settingsclass = data.RasterTargetFilterSettingsData
	defaultsettings = {
		'raster spacing': 50.0,
		'raster angle': 0.0,
		'raster movetype': None,
		'raster width': 0.0,
		'raster overlap': 0.0,
		'raster preset': None,
	}

	def __init__(self, *args, **kwargs):
		targetfilter.TargetFilter.__init__(self, *args, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.presetsclient = presets.PresetsClient(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}

		if self.__class__ == RasterTargetFilter:
			self.start()

	def autoSpacingAngle(self, targetdata):
		imageref = targetdata.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		imagedata = self.researchDBID(data.AcquisitionImageData, imageid, readimages=False)

		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		ht = imagedata['scope']['high tension']

		# transforming from target mag
		targetpresetname = self.settings['raster preset']
		targetpreset = self.presetsclient.getPresetByName(targetpresetname)
		mag1 = targetpreset['magnification']
		dim1 = targetpreset['dimension']['x']
		bin1 = targetpreset['binning']['x']
		fulldim = dim1 * bin1
		p1 = (0,fulldim)

		# transforming into mag of atlas
		mag2 = imagedata['scope']['magnification']
		bin2 = imagedata['camera']['binning']['x']

		movetype = self.settings['raster movetype']
		p2 = self.calclients[movetype].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# atlas scaling
		atlasscale = self.mosaic.scale
		p2 = atlasscale*p2[0], atlasscale*p2[1]
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
		spacing = numarray.hypot(*p2)
		angle = numarray.arctan2(*p2)
		angle = math.degrees(angle)
		return spacing,angle

	def makeRaster(self):
		spacing = self.settings['raster spacing']
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		limit = self.settings['raster width']
		rasterpoints = raster.createRaster2(spacing, anglerad, limit)
		return rasterpoints

	def filterTargets(self, targetlist):
		self.logger.info('filtering target list:  use center %d targets' %limit)
		newlist = []
		distlist = []
		targetdistances = {}
		for target in targetlist:
			oldtarget = data.AcquisitionImageTargetData(initializer=target)
			rasterpoints = self.makeRaster()
			for rp in rasterpoints:
				newtarget = data.AcquisitionImageTargetData(initializer=target)
				newtarget['delta row'] += rp[0]
				newtarget['delta column'] += rp[1]
				newlist.append(newtarget)
		return newlist
