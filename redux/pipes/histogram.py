import numpy
import redux.pipe

class Histogram(redux.pipe.Pipe):
	'''
	returns result of numpy.histogram
	'''
	required_args = {'histbins': redux.pipe.int_converter}
	def run(self, input, histbins):
		return numpy.histogram(input, histbins)
