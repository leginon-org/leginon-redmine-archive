import leginondata
import pyscope.remote
import socket

class InstrumentError(Exception):
	pass

class NotAvailableError(InstrumentError):
	pass

class RemoteInstrument(object):
	def __init__(self, remoteclient, name):
		object.__setattr__(self, '_remoteclient', remoteclient)
		object.__setattr__(self, '_name', name)
		object.__setattr__(self, 'attrs_get', {})
		object.__setattr__(self, 'attrs_set', {})
		object.__setattr__(self, 'attrs_call', {})

		caps = remoteclient.getCapabilities()
		caps = caps[self._name]
		self.instrumentclass = caps['class']
		for cap in caps['caps']:
			name = cap['name']
			implemented = cap['implemented']
			if 'get' in implemented:
				self.attrs_get[name] = None
			if 'set' in implemented:
				self.attrs_set[name] = None
			if 'call' in implemented:
				self.attrs_call[name] = None

	def __getattribute__(self, name):
		remoteclient = object.__getattribute__(self, '_remoteclient')
		remotename = object.__getattribute__(self, '_name')
		## search caps for property or method, then get or call
		if name in object.__getattribute__(self, 'attrs_get'):
			return remoteclient.get(remotename, [name])[name]
		elif name in object.__getattribute__(self, 'attrs_call'):
			def func(*args, **kwargs):
				return remoteclient.call(remotename, name, *args, **kwargs)
			return func
		else:
			return object.__getattribute__(self, name)

	def __setattr__(self, name, value):
		## search caps for property, then set
		if name in self.attrs_set:
			return self._remoteclient.set(self._name, {name: value})
		else:
			object.__setattr__(self, name, value)

	def getMany(self, names):
		remoteclient = object.__getattribute__(self, '_remoteclient')
		remotename = object.__getattribute__(self, '_name')
		return remoteclient.get(remotename, names)

	def setMany(self, valuedict):
		remoteclient = object.__getattribute__(self, '_remoteclient')
		remotename = object.__getattribute__(self, '_name')
		return remoteclient.set(remotename, valuedict)

class Instruments(object):
	def __init__(self):
		self.clients = {}
		self.instruments = {}
		self.caps = {}
		self.all = {}
		self.tems = {}
		self.cameras = {}
		self.camerasizes = {}

	def connect(self, hostname, login, status):
		## connect to server
		if hostname == 'localhost':
			hostname = socket.gethostname()
		clientkey = hostname
		if clientkey in self.clients:
			return
		client = pyscope.remote.Client(hostname, login, status)
		self.clients[clientkey] = client

		# store Server info to Leginon DB
		port = client.port  # get default port that was connected to
		server = leginondata.PyscopeServer(hostname=hostname, port=port)
		server.insert()

		allcaps = client.getCapabilities()
		for instrumentname,instrumentcaps in allcaps.items():

			## store instrument info into Leginon DB
			# XXX TEMPORARY:
			instrumentdata = leginondata.InstrumentData()
			instrumentdata['name'] = instrumentname
			instrumentdata['hostname'] = hostname
			# XXX FUTURE:
			'''
			instrumentdata = leginondata.PyscopeInstrument()
			instrumentdata['server'] = server
			instrumentdata['name'] = instrumentname
			instrumentdata['class'] = instrumentcaps['class']
			'''
			instrumentdata.insert()

			remoteinstrument = RemoteInstrument(client, instrumentname)

			## specific TEM/Camera info
			instrumentkey = "%s: %s" % (hostname, instrumentname)
			if instrumentdata['class'] == 'TEM':
				subinstrument = leginondata.TEM(instrument=instrumentdata)
				self.tems[instrumentkey] = remoteinstrument
			elif instrumentdata['class'] == 'Camera':
				subinstrument = leginondata.Camera(instrument=instrumentdata)
				self.cameras[instrumentkey] = remoteinstrument
				self.camerasizes[instrumentkey] = remoteinstrument.CameraSize
			subinstrument.insert()

instruments = Instruments()

class Proxy(object):
	def __init__(self, session=None):
		self.tems = instruments.tems
		self.ccdcameras = instruments.cameras
		self.camerasizes = instruments.camerasizes

		first_tem_name = self.tems.keys()[0]
		first_camera_name = self.ccdcameras.keys()[0]
		try:
			self.tem = self.tems[first_tem_name]
		except:
			self.tem = None
		try:
			self.ccdcamera = self.ccdcameras[first_camera_name]
			self.camerasize = self.camerasizes[first_camera_name]
		except:
			self.ccdcamera = None
			self.camerasize = None

		self.session = session

	def getTEMName(self):
		return self.tem._name

	def getCCDCameraName(self):
		return self.ccdcamera._name

	## USED BY presets.py and internally
	def getTEMNames(self):
		tems = self.tems.keys()
		tems.sort()
		return tems

	## USED BY presets.py and internally
	def getCCDCameraNames(self):
		cameras = self.ccdcameras.keys()
		cameras.sort()
		return cameras

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

		remotenames = []
		for instancekey in instance.keys():
			if instancekey in leginon_to_pyscope:
				pyscope_name = leginon_to_pyscope[instancekey]
				if pyscope_name in proxy.attrs_get:
					remotenames.append(pyscope_name)

		results = proxy.getMany(remotenames)

		for remotename, remotevalue in results.items():
			if isinstance(remotevalue, Exception):
				raise remotevalue
			instancekey = pyscope_to_leginon[remotename]
			instance[instancekey] = remotevalue

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
	('nframes', 'NumberOfFrames'),
)

## dicts to map in either direction
leginon_to_pyscope = dict(parametermapping)
pyscope_to_leginon = dict([(x[1],x[0]) for x in parametermapping])
