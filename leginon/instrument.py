import leginondata
import pyscope.remote
import socket

class InstrumentError(Exception):
	pass

class NotAvailableError(InstrumentError):
	pass

class RemoteInstrument(object):
	def __init__(self, remoteclient, name):
		self.remoteclient = remoteclient
		self.name = name
		caps = remoteclient.getCapabilities()
		self.instrumentclass = caps['class']
		self.caps = caps['caps']

	def __getattr__(self, name):
		## search caps for property or method, then get or call
		self.caps
		return self.remoteclient.get(self.name, [name])

	def __setattr__(self, name, value):
		## search caps for property, then set
		return self.remoteclient.set(self.name, {name: value})

class Connections(object):
	def __init__(self):
		self.clients = {}
		self.instruments = {}
		self.caps = {}
		self.all = {}
		self.tems = {}
		self.cameras = {}

	def connect(self, hostname, login, status):
		if hostname == 'localhost':
			hostname = socket.gethostname()
		client = pyscope.remote.Client(hostname, login, status)
		port = client.port  # get default port that was connected to
		server = leginondata.PyscopeServer(hostname=hostname, port=port)
		server.insert()

		allcaps = client.getCapabilities()
		for name,instrumentcaps in allcaps.items():
			instrument = leginondata.PyscopeInstrument()
			instrument['server'] = server
			instrument['name'] = name
			instrument['class'] = instrumentcaps['class']
			caps = instrumentcaps['caps']
			instrument.insert()

			key = hostname, name
			if instrument['class'] == 'TEM':
				subinstrument = leginondata.TEM(instrument=instrument)
				self.tems[key] = client
			elif instrument['class'] == 'Camera':
				subinstrument = leginondata.Camera(instrument=instrument)
				self.cameras[key] = client
			subinstrument.insert()

connections = Connections()

class Proxy(object):
	def __init__(self, session=None):
		self.tems = {}
		self.ccdcameras = {}
		self.tem = None
		self.ccdcamera = None
		self.camerasize = None
		self.camerasizes = {}
		self.session = session

	## USED BY presets.py and internally
	def getTEMNames(self):
		tems = self.tems.keys()
		tems.sort()
		return tems

	## USED BY presets.py and internally
	def getCCDCameraNames(self):
		ccdcameras = self.ccdcameras.keys()
		ccdcameras.sort()
		return ccdcameras

	## USED BY many modules.  name arg only used by presets.py and internally
	def getTEMData(self, name=None):
		'''
		Return InstrumentData instance by name, or currently selected
		'''
		if name is None:
			if self.tem is None:
				return None
			else:
				name = self.tem._name
				#dbtype = self.tem.DatabaseType
		else:
			if name not in self.tems:
				raise RuntimeError('no TEM \'%s\' available' % name)
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		#instrumentdata['type'] = dbtype
		#print dbtype
		try:
			instrumentdata['hostname'] = self.tems[name].Hostname
		except:
			raise RuntimeError('unable to get TEM hostname')
		instrumentdata = instrumentdata.query(results=1)[0]
		return instrumentdata

	## USED BY many modules.  name arg only used by presets.py and internally
	## name arg used by presets.py, corrector.py, correctorclient.py
	def getCCDCameraData(self, name=None):
		if name is None:
			if self.ccdcamera is None:
				return None
			else:
				name = self.ccdcamera._name
				#dbtype = self.ccdcamera.DatabaseType
		else:
			if name not in self.ccdcameras:
				raise RuntimeError('no CCD camera \'%s\' available' % name)
		instrumentdata = leginondata.InstrumentData()
		instrumentdata['name'] = name
		#instrumentdata['type'] = dbtype
		#print dbtype
		try:
			instrumentdata['hostname'] = self.ccdcameras[name].Hostname
		except:
			raise RuntimeError('unable to get TEM hostname')
		instrumentdata = instrumentdata.query(results=1)[0]
		return instrumentdata

	## USED BY many nodes to select which TEM to use
	def setTEM(self, name):
		if name is None:
			self.tem = None
		else:
			try:
				self.tem = self.tems[name]
			except KeyError:
				raise NotAvailableError('TEM \'%s\' not available' % name)

	## USED BY many nodes to select which CCD to use
	def setCCDCamera(self, name):
		if name is None:
			self.ccdcamera = None
			self.camerasize = None
		else:
			try:
				self.ccdcamera = self.ccdcameras[name]
				self.camerasize = self.camerasizes[name]
			except KeyError:
				raise NotAvailableError('CCD camera \'%s\' not available' % name)

	## USED BY presets.py and internally
	def getTEMParameter(self, temname, name):
		for parameter, attr_name in parametermapping:
			if parameter == name:
				return getattr(self.tems[temname], attr_name)
		raise ValueError

	## USED BY presets.py and internally
	def getCCDCameraParameter(self, ccdcameraname, name):
		for parameter, attr_name in parametermapping:
			if parameter == name:
				return getattr(self.ccdcameras[ccdcameraname], attr_name)
		raise ValueError

	def getData(self, dataclass, temname=None, ccdcameraname=None):
		if issubclass(dataclass, leginondata.ScopeEMData):
			if temname is None:
				proxy = self.tem
			else:
				try:
					proxy = self.tems[temname]
				except KeyError:
					raise NotAvailableError('TEM \'%s\' not available' % temname)
		elif issubclass(dataclass, leginondata.CameraEMData):
			if ccdcameraname is None:
				proxy = self.ccdcamera
			else:
				try:
					proxy = self.ccdcameras[ccdcameraname]
				except KeyError:
					raise NotAvailableError('CCD Camera \'%s\' not available' % ccdcameraname)
		if proxy is None:
			raise ValueError('no proxy selected for this data class')
		instance = dataclass()
		keys = []
		attributes = []
		types = []
		for key, attribute in parametermapping:
			if key not in instance:
				continue
			attributetypes = proxy.getAttributeTypes(attribute)
			if not attributetypes:
				continue
			if 'r' in attributetypes:
				keys.append(key)
				attributes.append(attribute)
				types.append('r')
		results = proxy.multiCall(attributes, types)
		for i, key in enumerate(keys):
			try:
				if isinstance(results[i], Exception):
					raise results[i]
			except AttributeError:
				continue
			instance[key] = results[i]
		if 'session' in instance:
			instance['session'] = self.session
		if 'tem' in instance:
			instance['tem'] = self.getTEMData(name=temname)
		if 'ccdcamera' in instance:
			instance['ccdcamera'] = self.getCCDCameraData(name=ccdcameraname)
		return instance

	def setData(self, instance, temname=None, ccdcameraname=None):
		if isinstance(instance, leginondata.ScopeEMData):
			if temname is None:
				proxy = self.tem
			else:
				try:
					proxy = self.tems[temname]
				except KeyError:
					raise NotAvailableError('TEM \'%s\' not available' % temname)
		elif isinstance(instance, leginondata.CameraEMData):
			if ccdcameraname is None:
				proxy = self.ccdcamera
			else:
				try:
					proxy = self.ccdcameras[ccdcameraname]
				except KeyError:
					raise NotAvailableError('CCD Camera \'%s\' not available' % ccdcameraname)
		elif isinstance(instance, leginondata.CameraImageData):
			instance = dataclass()
			self.setData(instance['scope'], temname=temname)
			self.setData(instance['camera'], ccdcameraname=ccdcameraname)
			return
		if proxy is None:
			raise ValueError('no proxy selected for this data instance')
		keys = []
		attributes = []
		types = []
		args = []
		for key, attribute in parametermapping:
			if key not in instance or instance[key] is None:
				continue
			attributetypes = proxy.getAttributeTypes(attribute)
			if not attributetypes:
				continue
			if 'w' in attributetypes:
				types.append('w')
			elif 'method' in attributetypes:
				types.append('method')
			else:
				continue
			keys.append(key)
			attributes.append(attribute)
			args.append((instance[key],))
		results = proxy.multiCall(attributes, types, args)
		for result in results:
			try:
				if isinstance(result, Exception):
					raise result
			except AttributeError:
				pass

parametermapping = (
	# ScopeEM
	('system time', 'SystemTime'),
	('magnification', 'Magnification'),
	('spot size', 'SpotSize'),
	('image shift', 'ImageShift'),
	('beam shift', 'BeamShift'),
	('focus', 'Focus'),
	('defocus', 'Defocus'),
	('reset defocus', 'resetDefocus'),
	('intensity', 'Intensity'),
	('screen current', 'ScreenCurrent'),
	('stigmator', 'Stigmator'),
	('beam tilt', 'BeamTilt'),
	('corrected stage position', 'CorrectedStagePosition'),
	('stage position', 'StagePosition'),
	('column pressure', 'ColumnPressure'),
	('high tension', 'HighTension'),
	('main screen position', 'MainScreenPosition'),
	('main screen magnification', 'MainScreenMagnification'),
	('small screen position', 'SmallScreenPosition'),
	('film stock', 'FilmStock'),
	('film exposure number', 'FilmExposureNumber'),
	('pre film exposure', 'preFilmExposure'),
	('post film exposure', 'postFilmExposure'),
	('film exposure type', 'FilmExposureType'),
	('film exposure time', 'FilmExposureTime'),
	('film manual exposure time', 'FilmManualExposureTime'),
	('film automatic exposure time', 'FilmAutomaticExposureTime'),
	('film text', 'FilmText'),
	('film user code', 'FilmUserCode'),
	('film date type', 'FilmDateType'),
	('objective current', 'ObjectiveCurrent'),
	# not used
	#('beam blank', 'BeamBlank'),
	#('film exposure', 'filmExposure'),
	#('low dose', 'LowDose'),
	#('low dose mode', 'LowDoseMode'),
	#('turbo pump', 'TurboPump'),
	#('holder type', 'HolderType'),
	#('holder status', 'HolderStatus'),
	#('stage status', 'StageStatus'),
	#('vacuum status', 'VacuumStatus'),
	#('column valves', 'ColumnValvePosition'),

	# CameraEM
	('dimension', 'Dimension'),
	('binning', 'Binning'),
	('offset', 'Offset'),
	('exposure time', 'ExposureTime'),
	('exposure type', 'ExposureType'),
	('inserted', 'Inserted'),
	('pixel size', 'PixelSize'),
	('energy filtered', 'EnergyFiltered'),
	('energy filter', 'EnergyFilter'),
	('energy filter width', 'EnergyFilterWidth'),
)

