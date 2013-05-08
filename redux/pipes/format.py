# standard lib
import cStringIO

# 3rd party
import numpy
import scipy.misc
import Image
import ImageDraw

# myami
import pyami.mrc

# local
import redux.pipe
import redux.utility

class Format(redux.pipe.Pipe):
	required_args = {'oformat': str}
	optional_args = {'rgb': redux.pipe.bool_converter, 'overlay': str, 'overlaycolor': redux.pipe.shape_converter}
	optional_defaults = {'rgb': False, 'overlay': '', 'overlaycolor': None}
	file_formats = {
		'JPEG': '.jpg',
		'GIF': '.gif',
		'TIFF': '.tif',
		'PNG': '.png',
		'MRC': '.mrc',
		'JSON': '.json',
	}
	def run(self, input, oformat, rgb, overlay, overlaycolor):
		if oformat not in self.file_formats:
			raise ValueError('oformat: %s' % (oformat,))

		if oformat == 'MRC':
			s = self.run_mrc(input)
		elif oformat == 'JSON':
			s = self.run_json(input)
		else:
			s = self.run_pil(input, oformat, rgb, overlay, overlaycolor)

		return s

	def run_mrc(self, input):
		file_object = cStringIO.StringIO()
		pyami.mrc.write(input, file_object)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def run_json(self, input):
		outstring = redux.utility.json_encode(input)
		return outstring

	def overlay_mask(self, image, mask, color):
		size = image.size
		mode = image.mode
		# read mask, resize it to image size
		# and make sure they are the same mode for the blend function
		maskim = Image.open(mask)
		maskim = maskim.resize(size)
		maskim = maskim.convert(mode)
		if color is None:
			overlay=maskim
		else:
			overlay=color
		# Use PIL Image blend with alpha value between 0.0 and 1.0
		# TODO: this way does not make use of a color. remove color
		image = Image.blend(image, maskim, .3)
		return image

	def run_pil(self, input, oformat, rgb, overlay, overlaycolor):
		pil_image = scipy.misc.toimage(input, cmin=0, cmax=255)
		if rgb:
			pil_image = pil_image.convert('RGBA')
		if overlay:
			pil_image = self.overlay_mask(pil_image, overlay, overlaycolor)
		file_object = cStringIO.StringIO()
		pil_image.save(file_object, oformat)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def make_dirname(self):
		self._dirname = None

	def make_resultname(self):
		format = self.kwargs['oformat']
		self._resultname = 'result' + self.file_formats[format]

	def put_result(self, f, result):
		f.write(result)

	def get_result(self, f):
		return f.read()

