# standard lib
import os

# myami
import pyami.mrc
import pyami.numpil
import pyami.imagic

# local
from redux.pipe import Pipe

class Read(Pipe):
	cache_file = False
	required_args = {'filename': os.path.abspath}
	optional_args = {'frame': int, 'info': bool}
	optional_defaults = {'info': False}

	def make_dirname(self):
		abs = os.path.abspath(self.kwargs['filename'])
		drive,tail = os.path.splitdrive(self.kwargs['filename'])
		self._dirname = tail[1:]

	def run(self, input, filename, info, frame=None):
		## input ignored
		### determine input format
		if filename.endswith('mrc') or filename.endswith('MRC'):
			## use MRC module to read
			input_format = 'mrc'
		elif filename[-3:].lower() in ('img', 'hed'):
			input_format = 'imagic'
		else:
			## use PIL to read
			input_format = 'PIL'

		### Read image file
		if input_format == 'mrc':
			# use mrc
			if info:
				result = pyami.mrc.readHeaderFromFile(filename)
			else:
				result = pyami.mrc.read(filename, frame)
		elif input_format == 'imagic':
			if info:
				result = pyami.imagic.readImagicHeader(filename)
			else:
				result = pyami.imagic.read(filename, frame)
		elif input_format == 'PIL':
			# use PIL
			if info:
				result = pyami.numpil.readInfo(filename)
			else:
				result = pyami.numpil.read(filename)
		return result

