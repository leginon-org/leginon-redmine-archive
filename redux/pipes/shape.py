# 3rd party
import scipy.ndimage

# myami
import pyami.imagefun

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter

class Shape(Pipe):
	required_args = {'shape': shape_converter}
	def run(self, input, shape):
		# make sure shape is same dimensions as input image
		# rgb input image would have one extra dimension
		if len(shape) != len(input.shape):
			if len(shape) +1 != len(input.shape):
				raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, shape))
			else:
				is_rgb=True
		else:
			is_rgb=False

		# determine whether to use imagefun.bin or scipy.ndimage.zoom
		binfactor = [input.shape[0] / shape[0], input.shape[1] / shape[1]]
		zoomfactors = []
		for i in range(len(shape)):
			# zoom factor on this axis
			zoomfactors.append(float(shape[i])/float(input.shape[i]))

			# check original shape is divisible by new shape
			if input.shape[i] % shape[i]:
				binfactor[i] = None   # binning will not work
				
		if is_rgb:
			zoomfactors.append(1.0)
			binfactor=None
		if binfactor[0] and binfactor[1]:
			output = pyami.imagefun.bin(input, binfactor[0], binfactor[1])
		else:
			output = scipy.ndimage.zoom(input, zoomfactors)
		return output

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims

