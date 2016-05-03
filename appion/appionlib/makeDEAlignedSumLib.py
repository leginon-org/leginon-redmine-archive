#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
import time
#pyami
from pyami import fileutil
#leginon
from leginon import ddinfo
#appion
from appionlib import appionPBS
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata
from appionlib import apBoxer
from appionlib import proc2dLib
import deProcessFrames
import glob
from pyami import mrc
from appionlib import apDBImage

class MakeAlignedSumLoop(appionPBS.AppionPBS):
	#=====================
	def setupParserOptions(self):
		configuration_options = deProcessFrames.ConfigurationOptions()
		options_list = configuration_options.get_options_list()
		sections = options_list.keys()
		for section in sections:
			for option in options_list[section]:
				if section == 'gainreference' or section == 'darkreference':
					if option['name'] in ('filename', 'framecount'):
						continue
				if section == 'boxes':
					if option['name'] in ('fromlist', 'fromonefile', 'fromfiles', 'boxsize', 'minimum'):
						continue
				if section == 'input' and option['name'] == 'framecount':
					continue
				if section == 'radiationdamage':
					if option['name'] in ('voltage'):
						continue
				if option['type'] == str:
					metavar = 'STR'
				elif option['type'] == int:
					metavar = 'INT'
				elif option['type'] == float:
					metavar = 'FLOAT'
				self.parser.add_option('--%s_%s' % (section, option['name']), type=option['type'], metavar=metavar, help=option['help'], default=option['default'])

		self.parser.add_option('--alignlabel', dest='alignlabel', default='a', help='label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed', metavar='CHAR')
		self.parser.add_option("--refimgid", dest="refimgid", type="int", help="Specify a corrected image to do gain/dark correction with", metavar="INT")
		self.parser.add_option('--border', dest='border', type='int', default=0, help='Clip border specified border pixels and pad back out with mean value')
		self.parser.add_option('--hackcopy', dest='hackcopy', action='store_true', default=False, help='Copy corrected image to session directory and overwrite the original image, saving the orignal with a new extension ".orig.mrc"')
		self.parser.add_option('--skipgain', dest='skipgain', action='store_true', default=False, help='Skip flatfield correction')
		self.parser.add_option('--siblingframes', dest='siblingframes', action='store_true', default=False, help='Use frames from sibling image', metavar='INT')
		self.parser.add_option("--output_rotation", dest="output_rotation", type='int', default=0, help="Rotate output particles by the specified angle", metavar="INT")

	#=======================
	def checkConflicts(self):
		#if override-dark or bright selected, should check for override-darkframes
		pass

	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if sessiondata['frame path']:
			# 3.0+
			return ddinfo.getRawFrameType(sessiondata['frame path'])
		else:
			# pre-3.0
			return ddinfo.getRawFrameType(sessiondata['image path'])

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'], self.params['wait'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setRawFrameType(self.getFrameType())
		self.dd.setDoseFDriftCorrOptions(self.params)
		self.exposurerate_is_default = self.params['radiationdamage_exposurerate'] == 1.0
		self.imageids = []
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)
		self.params['output_fileformat'] = 'mrc'
		if self.params['stackid'] is not None:
			self.imgtree = []
			stackdata = apStack.getStackParticlesFromId(self.params['stackid'])
			stackrundata = apStack.getOnlyStackData(self.params['stackid'])
			imagedict = {}
			masterlist = []
			apDisplay.printMsg('Collating particles from stack id %s' % self.params['stackid'])
			for particle in stackdata:
				parentimage = particle['particle']['image']['filename']
				if parentimage in imagedict.keys():
					imagedict[parentimage].append(particle['particle'])
				else:
					imagedict[parentimage] = []
					imagedict[parentimage].append(particle['particle'])
				index = len(imagedict[parentimage]) - 1
				masterlist.append({'particle': particle,
				 'key': parentimage,
				 'index': index})
				if particle['particle']['image'] not in self.imgtree:
					self.imgtree.append(particle['particle']['image'])

			self.stackmasterlist = masterlist
			self.stackimagedict = imagedict
			self.boxsize = stackdata[0]['stackRun']['stackParams']['boxSize']
			self.stats['imagecount'] = len(self.imgtree)
		
	def rejectImage(self, imgdata):
		'''
		Skip images without frame saved.
		'''
		is_reject = not imgdata['camera']['save frames']
		if is_reject:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
		return is_reject

	def getTargets(self, imgdata, scratchdir = '', handlefiles = 'direct'):
		targetdict = {}
		if self.params['refimgid']:
			self.refdata = apDatabase.getImageDataFromSpecificImageId(self.params['refimgid'])
			apDisplay.printWarning("Reference is based on %s" % self.refdata['filename'])
		else:
			self.refdata = imgdata
		try: 
			brightrefpath=self.refdata['bright']['session']['image path']
			brightrefname=self.refdata['bright']['filename']+'.mrc'
			brightref=os.path.join(brightrefpath,brightrefname)
		except:
			apDisplay.printWarning("Warning, bright reference not found. Frames will not be gain corrected.")
			brightrefname=None
			brightref=None
			
		try:
			darkrefpath=self.refdata['dark']['session']['image path']
			darkrefname=self.refdata['dark']['filename']+'.mrc'
			darkref=os.path.join(darkrefpath,darkrefname)
		except:
			apDisplay.printWarning("Warning, dark reference not found. Frames will not be gain corrected.")
			darkrefname=None
			darkref=None
			
		apDisplay.printMsg('Finding frames for %s' % imgdata['filename'])
		framespath = imgdata['session']['frame path']
		
		framepattern = os.path.join(framespath, (imgdata['filename']+'*'))
		filelist = glob.glob(framepattern)
		# frames might be ready even though the image is saved in the database
		if self.params['wait']:
			t00 = time.time()
			t0 = time.time()
			while len(filelist) == 0:
				if time.time() -t0 > 60:
					apDisplay.printMsg('Waiting for frames....')
					t0 = time.time()
				if time.time() - t00 > 20 * 60:
					break
				time.sleep(10)
				filelist = glob.glob(framepattern)
		if len(filelist) < 1:
			apDisplay.printError('frames not found with %s' % framepattern)

		#this is super hacky. Should get name from sibling name
		if self.params['siblingframes'] is True:
			imgrootname = imgdata['filename'].split('-')[0]
		else:
			imgrootname = imgdata['filename']
		print os.path.join(framespath, imgrootname + '*')
		framesroot, framesextension = os.path.splitext(glob.glob(os.path.join(framespath, imgrootname + '*'))[0])
		framespathname = framesroot + framesextension
		framesname = os.path.split(framespathname)[-1]
		if framesextension == '.frames':
			self.params['input_type'] = 'directories'
		elif framesextension == '.mrc':
			self.params['input_type'] = 'stacks'
		apDisplay.printMsg('Frames located at %s' % framespathname)

		if handlefiles == 'direct':
			targetdict['brightref'] = brightref
			targetdict['darkref'] = darkref
			targetdict['framespathname'] = framespathname
			targetdict['outpath'] = self.params['rundir']
		elif handlefiles == 'copy':
			if self.params['skipgain'] is False and brightref is not None and darkref is not None:
				shutil.copy(brightref, scratchdir)
				shutil.copy(darkref, scratchdir)
				targetdict['brightref'] = os.path.join(scratchdir, brightrefname)
				targetdict['darkref'] = os.path.join(scratchdir, darkrefname)
			try:
				if framesextension == '.frames':
					shutil.copytree(framespathname, os.path.join(scratchdir, framesname))
				elif framesextension == '.mrc':
					newpath=os.path.join(scratchdir,framesname)
					os.mkdir(newpath)
					shutil.copy(framespathname, newpath)
			except:
				apDisplay.printWarning('there was a problem copying the frames for %s' % imgdata['filename'])

			targetdict['framespathname'] = os.path.join(scratchdir, framesname)
			targetdict['outpath'] = os.path.join(scratchdir, imgdata['filename'])
		elif handlefiles == 'link':
			if self.params['skipgain'] is False and brightref is not None and darkref is not None:
				os.symlink(brightref, os.path.join(scratchdir, brightrefname))
				os.symlink(darkref, os.path.join(scratchdir, darkrefname))
				targetdict['brightref'] = os.path.join(scratchdir, brightrefname)
				targetdict['darkref'] = os.path.join(scratchdir, darkrefname)
			os.symlink(framespathname, os.path.join(scratchdir, framesname))
			targetdict['framespathname'] = os.path.join(scratchdir, framesname)
			targetdict['outpath'] = os.path.join(scratchdir, imgdata['filename'])
			
		if self.params['stackid'] is not None:
			particledata = self.stackimagedict[imgdata['filename']]
			boxsize=self.boxsize
			shiftdata={'scale':1,'shiftx':0,'shifty':0}
			boxpath=os.path.join(scratchdir,framesname+'.box')
			apBoxer.processParticleData(imgdata,boxsize,particledata,shiftdata,boxpath)
			print boxsize,boxpath
		return targetdict

	def calculateListDifference(self, list1, list2):
		from sets import Set
		set1 = Set(list1)
		set2 = Set(list2)
		list_diff = list(set1.difference(set2))
		list_diff.sort()
		return list_diff

	def getCameraDefects(self, imgdata):
		"""
		Set defects for camera in self.params if not entered already.
		"""
		corrector_plan = imgdata['corrector plan']
		cam_size = imgdata['camera']['dimension']
		border = self.params['border']
		# map name to de params name and leginon corrector plan name
		namemap = {'x': ('columns', 'cols'), 'y': ('rows', 'rows')}

		def formatBadList(badlist):
			return ','.join(map(lambda x: '%d' % x,badlist))

		badlines = {'x':[],'y':[]}
		for axis in namemap.keys():
			de_name = 'defects_%s' % namemap[axis][0]
			leg_name = 'bad_%s' % namemap[axis][1]
			exclude_list = []
			# figure out the defects if not specified already
			if not self.params[de_name]:
				if corrector_plan and corrector_plan[leg_name]:
					# Do not include a location in defects for DE 
					# process if in the border because large number
					# of defect correction is slow.
					if border:
						exclude_list = range(0, border)
						exclude_list.extend(range(cam_size[axis] - border, cam_size[axis]))
					bad = self.calculateListDifference(corrector_plan[leg_name], exclude_list)
					badlines[axis] = bad
					self.params[de_name] = formatBadList(bad)
			else:
				# overwrite corrector_plan
				badlines[axis] = map((lambda x:int(x)),self.params[de_name].split(','))

		# Leginon sum image and DE frames flipping does not need to be handled
		# because DE program handles that by default
		# camera may be mounted with a rotation so that frames are rotated relative to the image known in Leginon
		# Here we are transforming from image to frames
		if imgdata['camera']['frame rotate'] == 1:
			# row 1 becomes column 1, column 1 becomes dimx-col
			rotated_bad_rows = map((lambda x: x),badlines['x'])
			rotated_bad_cols = map((lambda x: cam_size['y']-x-1),badlines['y'])
			self.params['defects_%s' % namemap['x'][0]] = formatBadList(rotated_bad_cols)
			self.params['defects_%s' % namemap['y'][0]] = formatBadList(rotated_bad_rows)
			# allow user to overwrite transforms
			if self.params['darkreference_transform']+self.params['gainreference_transform']+self.params['output_transform'] == 0:
				self.params['darkreference_transform'] = 2  #90 degrees
				self.params['gainreference_transform'] = 2
				self.params['output_transform'] = 3  #270 degrees
		elif imgdata['camera']['frame rotate'] == 3:
			rotated_bad_rows = map((lambda x: cam_size['x']-x-1),badlines['x'])
			rotated_bad_cols = map((lambda x: x),badlines['y'])
			self.params['defects_%s' % namemap['x'][0]] = formatBadList(rotated_bad_cols)
			self.params['defects_%s' % namemap['y'][0]] = formatBadList(rotated_bad_rows)
			# allow user to overwrite transforms
			if self.params['darkreference_transform']+self.params['gainreference_transform']+self.params['output_transform'] == 0:
				self.params['darkreference_transform'] = 3
				self.params['gainreference_transform'] = 3
				self.params['output_transform'] = 2
		# TODO: need to handle bad pixels, too

	def generateCommand(self, imgdata, targetdict):

		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return

#		### set processing image
#		try:
#			self.dd.setImageData(imgdata)
#		except Exception as e:
#			apDisplay.printWarning(e.args[0])
#			return

		# Set up the alignment
		kev = imgdata['scope']['high tension'] / 1000
		apix = apDatabase.getPixelSize(imgdata)
		nframes = imgdata['camera']['nframes']
		try:
			dose = apDatabase.getDoseFromImageData(imgdata)
		except:
			dose = None

		# overwrite radiationdamage_exposurerate if it is at default
		if dose and self.exposurerate_is_default:
			self.params['radiationdamage_exposurerate'] = dose / nframes

		#set appion specific options
		#flatfield references
		if self.params['skipgain'] is not True and targetdict['brightref'] is not None and targetdict['darkref'] is not None:
			self.params['gainreference_filename'] = targetdict['brightref']
			brightnframes = imgdata['bright']['camera']['nframes']
			self.params['gainreference_framecount'] = brightnframes
			self.params['darkreference_filename'] = targetdict['darkref']
			darknframes = imgdata['dark']['camera']['nframes']
			self.params['darkreference_framecount'] = darknframes
		self.getCameraDefects(imgdata)
		self.params['input_framecount'] = nframes
		self.params['output_invert'] = 0
		self.params['radiationdamage_apix'] = apix
		self.params['radiationdamage_voltage'] = kev
		if self.params['stackid'] is not None:
			self.params['boxes_fromfiles']=1
		if os.path.exists(targetdict['outpath']):
			shutil.rmtree(targetdict['outpath'])
		os.mkdir(targetdict['outpath'])
		command = ['runDEProcessFrames.py']
		keys = self.params.keys()
		keys.sort()
		for key in keys:
			param = self.params[key]
			if param == None or param == '' or key == 'description':
				pass
			else:
				option = '--%s=%s' % (key, param)
				command.append(option)

		command.append(targetdict['outpath'])
		framespathname = targetdict['framespathname']

		#check to see if there are frames in the path
		if self.params['input_type'] == 'directories':
			framesinpath = len(glob.glob(os.path.join(framespathname, '*')))
			if framesinpath == 0:
				apDisplay.printWarning('%s skipped because %d frames were found' % (imgdata['filename'], framesinpath))
				return
		elif self.params['input_type']=='stacks':
			framespathname=glob.glob(os.path.join(framespathname, '*'))[0]
		command.append(framespathname)
		return command

	def collectResults(self, imgdata, targetdict):
		"""
		Overwrite collectResults to do final processing of the
		queue job result and commit
		"""
		try:
			innamepath = glob.glob(os.path.join(targetdict['outpath'], '*.mrc'))[0]
			print innamepath
		except IndexError:
			apDisplay.printWarning('queued job for %s failed' % imgdata['filename'])
			return None
		if self.params['stackid'] is not None:
			return None
		outname = imgdata['filename'] + '-' + self.params['alignlabel'] + '.mrc'
		outnamepath = os.path.join(targetdict['outpath'], outname)
		if self.params['border'] != 0:
			command = ['proc2d', innamepath, outnamepath]
			header = mrc.readHeaderFromFile(innamepath)
			origx = header['nx']
			origy = header['ny']
			newx = origx - self.params['border']
			newy = origy - self.params['border']
			command.append('clip=%d,%d' % (newx, newy))
			print command
			subprocess.call(command)
			command = ['proc2d', outnamepath, outnamepath]
			command.append('clip=%d,%d' % (origx, origy))
			command.append('edgenorm')
			print command
			subprocess.call(command)
		newimg_array = mrc.read(outnamepath)
		self.commitAlignedImageToDatabase(imgdata, newimg_array, alignlabel=self.params['alignlabel'])
		# return None since everything is committed within this function.
		if self.params['hackcopy'] is True:
			origpath = imgdata['session']['image path']
			archivecopy = os.path.join(origpath, imgdata['filename'] + '.orig.mrc')
			if os.path.exists(archivecopy) is True:
				apDisplay.printMsg('archive copy for %s already exists, so skipping archive' % archivecopy)
			else:
				shutil.move(os.path.join(origpath, imgdata['filename'] + '.mrc'), archivecopy)
			shutil.copyfile(outnamepath, os.path.join(origpath, imgdata['filename'] + '.mrc'))

	def insertFunctionRun(self):
		stackdata = None
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'], align=None, bin=None, stack=None, method='de_aligner')
		qpath = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		sessiondata = self.getSessionData()
		qdeparams = appiondata.ApDEAlignerParamsData()
		qdeparams['alignment_correct'] = self.params['alignment_correct']
		qdeparams['alignment_quanta'] = self.params['alignment_quanta']
		qdeparams['radiationdamage_compensate'] = self.params['radiationdamage_compensate']
		qdeparams['radiationdamage_multiplier'] = self.params['radiationdamage_multiplier']
		qdeparams['output_sumranges'] = self.params['output_sumranges']
		qparams['de_aligner'] = qdeparams
		q = appiondata.ApDDStackRunData(runname=self.params['runname'], params=qparams, session=sessiondata, path=qpath)
		results = q.query()
		if results:
			return results[0]
		if self.params['commit'] is True:
			q.insert()
			return q

	def postLoopFunctions(self):
		if self.params['stackid'] is not None and self.params['commit'] is True:
			#recreate particle stack
			newstackname='framealigned.hed'
			stackapix=apDatabase.getPixelSize(self.imgtree[0])
			for n,particledict in enumerate(self.stackmasterlist):
				#proc2d=proc2dLib.RunProc2d()
				#proc2d.setValue('outfile', newstackname)
				#proc2d.setValue('apix', stackapix)
				#proc2d.setValue('append', True)
				parentimage=particledict['key']
				correctedpath=os.path.join(self.params['queue_scratch'],parentimage,parentimage)
				if os.path.exists(correctedpath):				
					correctedparticle=glob.glob(os.path.join(correctedpath,('%s.*.region_%03d.*' % (parentimage,particledict['index']))))
					#proc2d.setValue('infile', correctedparticle[0])
					###TODO proc2dLib reads files in opposite direction of proc2d. Need to add xflip to proc2dLib
					command=['proc2d',correctedparticle[0], newstackname]
					if self.params['output_rotation'] !=0:
						###TODO add rot to proc2dLib
						command.append('rot=%d' % self.params['output_rotation'])
					
					apDisplay.printMsg( "adding %s" % correctedparticle[0])
					subprocess.call(command)
					#proc2d.run()
				else:
					print "did not find frames for ", parentimage
					#proc2d.setValue('infile', origstackpath)
					#proc2d.setValue('first', n)
					#proc2d.setValue('last', n)
					command=['proc2d', origstackpath, newstackname,('first=%d' % n), ('last=%d' % n)]
					print command
					#proc2d.run()
					if self.params['dryrun'] is False:
						subprocess.call(command)
			totalptcls=n+1
			#upload stack
			
			#make keep file
			self.params['keepfile']='keepfile.txt'
			f=open(self.params['keepfile'],'w')
			for n in range(len(self.stackmasterlist)):
				f.write('%d\n' % (n))
			f.close()
			
			apStack.commitSubStack(self.params, newname=newstackname)
			apStack.averageStack(stack=newstackname)
			apDisplay.printMsg("processed %d particles" % totalptcls)
	
	def commitAlignedImageToDatabase(self, imgdata, newimage, alignlabel = 'a'):
		if self.params['commit'] is False:
			return
		camdata = imgdata['camera']
		newimagedata = apDBImage.makeAlignedImageData(imgdata, camdata, newimage, alignlabel)
		newimageresults = newimagedata.query()
		if newimageresults:
			apDisplay.printWarning('Warning an image named %s already exists in the database. This image will be skipped' % newimageresults['filename'])
			return
		else:
			apDisplay.printMsg('Uploading aligned image as %s' % newimagedata['filename'])
			newimagedata.insert()
			q = appiondata.ApDDAlignImagePairData(source=imgdata, result=newimagedata, ddstackrun=self.rundata)
			q.insert()

	def commitToDatabase(self, imgdata):
		"""
		This commitToDatabase does nothing. The actual commit is handled in commitAlignedImageToDatabase where the input also include the new image array.
		"""
		pass


if __name__ == '__main__':
	makeSum = MakeAlignedSumLoop()
	makeSum.run()