import data
import Numeric
import LinearAlgebra

class CalibrationClient(object):
	'''
	this is a component of a node that needs to use calibrations
	'''
	def __init__(self, node):
		self.node = node

	def getCalibration(self, key):
		cal = self.node.researchByDataID('calibrations')
		return cal.content[key]

	def setCalibration(self, key, calibration):
		newdict = {key: calibration}
		dat = data.CalibrationData('calibrations', newdict)
		self.node.publishRemote(dat)

	def magCalibrationKey(self, magnification, caltype):
		'''
		this determines the key in the main calibrations dict
		where a magnification dependent calibration is located
		'''
		return str(int(magnification)) + caltype

	def transform(self, pixelshift, scope, camera):
		'''
		pixelshift is a shift from the center of an image acquired
		under the conditions specified in scope and camera
		Implementation should return a modified scope state that induces the desired pixelshift
		'''
		raise NotImplementedError()

class MatrixCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def parameter(self):
		'''
		returns a scope key for the calibrated parameter
		'''
		raise NotImplementedError()

	def setCalibration(self, key, matrix, angle, pixelsize):
		calibration = {}
		CalibrationClient.setCalibration(self, key, calibration)

	def transform(self, pixelshift, scope, camera):
		'''
		Calculate a new scope state from the given pixelshift
		The input scope and camera state should refer to the image
		from which the pixelshift originates
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = (pixrow, pixcol)

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		change = Numeric.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		new = {}
		new[par] = dict(scope[par])
		new[par]['x'] += changex
		new[par]['y'] += changey

		return new

	def itransform(self, shift, scope, camera):
		'''
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		vect = (shift['x'], shift['y'])

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		matrix = LinearAlgebra.inverse(matrix)

		pixvect = Numeric.matrixmultiply(matrix, vect)
		pixvect *= (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}


class ImageShiftCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'image shift'


class StageCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'stage position'


import gonmodel
class ModeledStageCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def transform(deltapixels, scope, camera):
		curstage = scope['stage position']
		newstage = dict(curstage)

		## do modifications to newstage here

		return newstage

	def pixtix(self, xmodfile, ymodfile, magfile, gonx, gony, pixx, pixy):
		xmod = gonmodel.GonModel()
		ymod = gonmodel.GonModel()
		maginfo = gonmodel.MagInfo(magfile)
	
		xmod.read_gonshelve(xmodfile)
		ymod.read_gonshelve(ymodfile)
	
		modavgx = maginfo.get('modavgx')
		modavgy = maginfo.get('modavgy')
	
		gonx1 = xmod.rotate(maginfo, pixx, pixy)
		gony1 = ymod.rotate(maginfo, pixx, pixy)
	
		gonx1 = gonx1 * modavgx
		gony1 = gony1 * modavgy
	
		gonx1 = xmod.predict(gonx,gonx1)
		gony1 = ymod.predict(gony,gony1)
	
		return {'x':gonx1, 'y':gony1}
	
	def pixelShift(self, ievent):
		mag = ievent.content['magnification']
		delta_row = ievent.content['row']
		delta_col = ievent.content['column']

		current = self.getStagePosition()
		print 'current before delta', current
		curx = current['stage position']['x']
		cury = current['stage position']['y']

		xmodfile = self.modfilename('x')
		ymodfile = self.modfilename('y')
		magfile = self.magfilename(mag)

		deltagon = self.pixtix(xmodfile,ymodfile,magfile,curx,cury,delta_col,delta_row)

		current['stage position']['x'] += deltagon['x']
		current['stage position']['y'] += deltagon['y']
		print 'current after delta', current

		stagedata = data.EMData('scope', current)
		self.publishRemote(stagedata)
