#!/usr/bin/env python

import os
import sys
import math
import numpy
from pyami import mrc
from pyami import mem
from pyami import imagic
from pyami import imagefun
from appionlib import apFile
from appionlib import apDisplay
from appionlib import basicScript
from appionlib import apImagicFile
from appionlib.apImage import imagenorm
from appionlib.apImage import imagefilter

# Scott: not inheriting Appion base classes because options are unique and stand alone
# Neil: basicScript is designed for this

class ApProc2d(basicScript.BasicScript):
	#=====================
	#=====================
	def setupParserOptions(self):
		self.normoptions = ('none', 'boxnorm', 'edgenorm', 'rampnorm', 'parabolic') #normalizemethod

		self.parser.add_option('--in', dest='infile', metavar='FILE', help='Input image/stack')
		self.parser.add_option('--out', dest='outfile', metavar='FILE', help='Output image/stack')
		self.parser.add_option('--lp', '--lowpass', dest='lowpass', type=float,
			metavar='FLOAT', help='Low pass filter to provided resolution. In Angstroms. ')
		self.parser.add_option('--hp', '--highpass', dest='highpass', type=float,
			metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		self.parser.add_option("--pixlimit", dest="pixlimit", type="float",
			help="Limit pixel values to within <pixlimit> standard deviations", metavar="FLOAT")
		self.parser.add_option('--apix', dest='apix', type=float,
			metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		self.parser.add_option('--bin', dest='bin', type=int,
			metavar='INT', help="Decimate/bin by a certain factor")
		self.parser.add_option('--invert', dest='inverted', help="Invert contrast",
			action='store_true', default=False, )
		self.parser.add_option('--first', dest='first', type=int, default=0, metavar='INT',
			help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		self.parser.add_option('--last', dest='last', type=int, metavar='INT',
			help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		self.parser.add_option('--no-append', dest='append', default=None,
			action='store_false', help="Overwrite pre-existing output stack (will guess if not defined)")
		self.parser.add_option('--append', dest='append', default=None,
			action='store_true', help="Append to pre-existing output stack (will guess if not defined)")
		self.parser.add_option('--debug', dest='debug', help="Show extra debugging messages",
			action='store_true', default=False, )
		self.parser.add_option("--norm", "--normalize-method", dest="normalizemethod",
			help="Normalization method (default: none)", metavar="TYPE",
			type="choice", choices=self.normoptions, default="none", )
		self.parser.add_option('--edgenorm', dest='normalizemethod',
			help="Set normalization method to edgenorm",
			action='store_const', const='edgenorm', )
		self.parser.add_option('--rampnorm', dest='normalizemethod',
			help="Set normalization method to rampnorm",
			action='store_const', const='rampnorm', )

	#=====================
	#=====================
	def checkConflicts(self):
		self.headercache = {}
		self.particlesWritten = 0

		if self.params['infile'] is None:
			apDisplay.printError("Please provide an input file, e.g., --in=file.hed")
		if self.params['outfile'] is None:
			apDisplay.printError("Please provide an input file, e.g., --out=file.mrc")

		### Read input file
		self.inheader = self.readFileHeader(self.params['infile'])
		self.inputNumParticles = self.inheader['nz']

		if self.params['apix'] is None:
			self.params['apix'] = self.getPixelSize(self.params['infile'])
		if self.params['apix'] is None:
			apDisplay.printWarning("Assuming apix is 1.0 A/pixel")
			self.params['apix'] = 1.0

		return

	#=====================
	#=====================
	# probably should move this to a more general location
	def getPixelSize(self, filename):
		#header = self.readFileHeader(filename)
		if filename.endswith('.mrc'):
			pixeldict = mrc.readFilePixelSize(filename)
			print pixeldict
			if pixeldict['x'] == pixeldict['y'] and pixeldict['x'] == pixeldict['z']:
				return pixeldict['x']
			else:
				apDisplay.printError("Image has unknown pixel size")
		elif filename.endswith('.hed') or filename.endswith('.img'):
			return None
		elif filename.endswith('.spi'):
			### to be implemented
			return None
		elif filename.endswith('.hdf'):
			### to be implemented
			return None
		else:
			return None

	#=====================
	#=====================
	# probably should move this to a more general location
	def readFileHeader(self, filename):
		"""
		reads header information for any type of image or stack file
		"""
		try:
			return self.headercache[filename]
		except KeyError:
			pass
		if not os.path.exists(filename):
			return None
		#Determine extension
		if filename.endswith('.mrc'):
			header = mrc.readHeaderFromFile(filename)
		elif filename.endswith('.hed') or filename.endswith('.img'):
			header = imagic.readImagicHeader(filename)
		elif filename.endswith('.spi'):
			### to be implemented
			apDisplay.printError("SPIDER is not implemented yet")
		elif filename.endswith('.hdf'):
			### to be implemented
			apDisplay.printError("HDF is not implemented yet")
		else:
			apDisplay.printError("unknown stack type")
		self.headercache[filename] = header
		return header

	#=====================
	#=====================
	# probably should move this to a more general location
	def readFileData(self, filename):
		"""
		takes any file type and returns a list of 2D arrays
		use memory mapping (mmap) to prevent memory overloads
		"""
		#Determine extension
		if filename.endswith('.mrc'):
			data = mrc.mmap(filename)
			if len(data.shape) == 2:
				#convert to 3D
				self.single = True
				data.resize((1, data.shape[0], data.shape[1], ))
		elif filename.endswith('.hed') or filename.endswith('.img'):
			data = imagic.read(filename)
		elif filename.endswith('.spi'):
			### to be implemented
			apDisplay.printError("SPIDER is not implemented yet")
		elif filename.endswith('.hdf'):
			### to be implemented
			apDisplay.printError("HDF is not implemented yet")
		else:
			apDisplay.printError("unknown stack type")
		return data

	#=====================
	#=====================
	# probably should move this to a more general location
	def appendParticleListToStackFile(self, partlist, filename):
		"""
		takes any file type and adds a list of particles
		use memory mapping (mmap) to prevent memory overloads
		"""
		if self.particlesWritten < 1 and os.path.exists(filename) and self.params['append'] is False:
			if filename.endswith('.hed') or filename.endswith('.img'):
				root = os.path.splitext(filename)[0]
				headerfile = root+".hed"
				datafile = root+".img"
				os.remove(headerfile)
				os.remove(datafile)
			else:
				os.remove(filename)

		#Determine extension
		if filename.endswith('.mrc'):
			if os.path.exists(filename):
				partarray = numpy.array(partlist)
				mrc.append(partarray, filename)
			else:
				f = open(filename, "wb+")
				partarray = numpy.array(partlist)
				mrc.write(partarray, f)
				f.close()
				apix = self.params['apix']
				pixeldict = {'x': apix, 'y': apix, 'z': apix, }
				mrc.updateFilePixelSize(filename, pixeldict)

		elif filename.endswith('.hed') or filename.endswith('.img'):
			apImagicFile.appendParticleListToStackFile(partlist, filename,
				msg=self.params['debug'])

		elif filename.endswith('.spi'):
			### to be implemented
			apDisplay.printError("SPIDER is not implemented yet")

		elif filename.endswith('.hdf'):
			### to be implemented
			apDisplay.printError("HDF is not implemented yet")

		else:
			apDisplay.printError("unknown stack type")
		self.particlesWritten += len(partlist)
		return True

	#=====================
	#=====================
	def outFileStatus(self):
		if not os.path.exists(self.params['outfile']):
			self.params['append'] = False
			return 0

		### out file exists
		try:
			existheader = self.readFileHeader(self.params['outfile'])
			existNumParticles = existheader['nz']
		except KeyError:
			existNumParticles = 0
		if self.params['append'] is None:
			if existNumParticles > 1:
				## output file is a stack, append
				self.params['append'] = True
			else:
				## output file is not a stack, overwrite
				self.params['append'] = False

		### display message
		if self.params['append'] is False:
			apDisplay.printWarning("Overwriting existing file, %s"%(self.params['outfile']))
			return 0

		self.message("Appending to existing file, %s"%(self.params['outfile']))
		## dimensions for new particles must be the same as the old
		if self.inheader['nx'] != existheader['nx'] or self.inheader['ny'] != existheader['ny']:
			apDisplay.printError("Dims for existing stack (%dx%d) is different from input stack (%dx%d)"
				%(self.inheader['nx'], self.inheader['ny'], existheader['nx'], existheader['ny']))

		return existNumParticles

	#===============
	def message(self, msg):
		if self.params['debug'] is True:
			apDisplay.printMsg("apProc2d: "+msg)

	#=====================
	#=====================
	def getParticlesPerCycle(self, stackfile):
		### amount of free memory on machine (converted to bytes)
		freememory = mem.free()*1024
		self.message("Free memory: %s"%(apDisplay.bytes(freememory)))
		### box size of particle
		boxsize = apFile.getBoxSize(stackfile)[0]
		self.message("Box size: %d"%(boxsize))
		### amount of memory used per particles (4 bytes per pixel)
		memperpart = boxsize**2 * 4.0
		self.message("Memory used per part: %s"%(apDisplay.bytes(memperpart)))
		### maximum number particles that fit into memory
		maxpartinmem = freememory/memperpart
		self.message("Max particles in memory: %d"%(maxpartinmem))
		### number particles to fit into memory
		partallowed = int(maxpartinmem/20.0)
		self.message("Particles allowed in memory: %d"%(partallowed))
		### number particles in stack
		numpart = self.params['last']
		if numpart > partallowed:
			numcycles = math.ceil(numpart/float(partallowed))
			stepsize = int(numpart/numcycles)
		else:
			numcycles = 1
			stepsize = numpart
		self.message("Particle loop num cycles: %d"%(numcycles))
		self.message("Particle loop step size: %d"%(stepsize))
		return stepsize


	#=====================
	#=====================
	def start(self):

		### Works
		# read from MRC image
		# read from HED/IMG stack
		# write to MRC image
		# write to HED/IMG stack
		# append to HED/IMG stack
		# filter images
		# implement binning
		# write to MRC stack
		# append to MRC stack
		# implement normalization

		### needs more testing
		# write pixelsize to new MRC file
		# get apix from MRC header

		### TODO
		# read from SPIDER stack
		# read from EMAN/HDF stack
		# read from SPIDER image
		# write to SPIDER image
		# write to SPIDER stack
		# write to EMAN/HDF stack
		# get apix from HED/IMG header
		# implement proc2d --list feature
		# implement proc2d --rotavg
		# implement proc2d --clip

		# determine numParticles to add
		if self.params['last'] is None:
			self.params['last'] = self.inputNumParticles - 1 #stacks start at 0
		elif self.params['last'] > self.inputNumParticles:
			apDisplay.printWarning("Last particle requested (%d) is larger than available particles (%d)"
				%(self.params['last'], self.inputNumParticles))
			self.params['last'] = self.inputNumParticles - 1 #stacks start at 0
		addNumParticles = self.params['last'] - self.params['first'] + 1

		### prepare for an existing file
		existNumParticles = self.outFileStatus()
		self.totalParticles = existNumParticles + addNumParticles

		indata = self.readFileData(self.params['infile'])

		#it more efficient to process X particles and write them to disk rather than
		# write each particle to disk each time.
		#particles are read using a memory map (numpy.memmap), so we can pretend to
		# continuously read all into memory
		# FIXME: measure memory available and compute based on size of particle box
		particlesPerCycle = 100
		self.getParticlesPerCycle(self.params['infile'])

		processedParticles = []
		for partnum in range(self.params['first'], self.params['first']+addNumParticles):
			particle = indata[partnum]
			if self.params['debug'] is True:
				print "---------"
				print "Particle Number: %d of %d"%(partnum, addNumParticles)
			if self.params['pixlimit']:
				self.message("pixlimit: %s"%(self.params['pixlimit']))
				particle = imagefilter.pixelLimitFilter(particle, self.params['pixlimit'])
			if self.params['lowpass']:
				self.message("lowpass: %s"%(self.params['lowpass']))
				particle = imagefilter.lowPassFilter(particle, apix=self.params['apix'], radius=self.params['lowpass'])
			if self.params['highpass']:
				self.message("highpass: %s"%(self.params['highpass']))
				particle = imagefilter.highPassFilter2(particle, self.params['highpass'], apix=self.params['apix'])
			### unless specified, invert the images
			if self.params['inverted'] is True:
				self.message("inverted: %s"%(self.params['inverted']))
				particle = -1.0 * particle
			### clipping
			"""
			if particle.shape != boxshape:
				if boxsize <= particle.shape[0] and boxsize <= particle.shape[1]:
					particle = imagefilter.frame_cut(particle, boxshape)
				else:
					apDisplay.printError("particle shape (%dx%d) is smaller than boxsize (%d)"
						%(particle.shape[0], particle.shape[1], boxsize))
			"""

			### step 3: normalize particles
			#self.normoptions = ('none', 'boxnorm', 'edgenorm', 'rampnorm', 'parabolic') #normalizemethod
			self.message("normalize method: %s"%(self.params['normalizemethod']))
			if self.params['normalizemethod'] == 'boxnorm':
				particle = imagenorm.normStdev(particle)
			elif self.params['normalizemethod'] == 'edgenorm':
				particle = imagenorm.edgeNorm(particle)
			elif self.params['normalizemethod'] == 'rampnorm':
				particle = imagenorm.rampNorm(particle)
			elif self.params['normalizemethod'] == 'parabolic':
				particle = imagenorm.parabolicNorm(particle)

			### step 4: decimate/bin particles if specified
			### binning is last, so we maintain most detail and do not have to deal with binned apix
			if self.params['bin'] > 1:
				particle = imagefun.bin2(particle, self.params['bin'])

			### working above this line
			processedParticles.append(particle)

			if len(processedParticles) == particlesPerCycle:
				### step 5: merge particle list with larger stack
				self.appendParticleListToStackFile(processedParticles, self.params['outfile'])
				processedParticles = []
		if len(processedParticles) > 0:
			self.appendParticleListToStackFile(processedParticles, self.params['outfile'])
		print "Wrote %d particles to file "%(self.particlesWritten)

if __name__ == '__main__':
	approc2d = ApProc2d(quiet=True)
	approc2d.start()
	approc2d.close()
