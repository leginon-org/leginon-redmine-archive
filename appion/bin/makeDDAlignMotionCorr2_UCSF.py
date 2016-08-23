#!/usr/bin/env python
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay

class MotionCorr2UCSFAlignStackLoop(apDDMotionCorrMaker.MotionCorrAlignStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MotionCorr2UCSFAlignStackLoop,self).setupParserOptions()

		self.parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

		self.parser.add_option("--FmRef", dest="FmRef",type="int",default=0,
			help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.", metavar="#")

		self.parser.add_option("--Iter", dest="Iter",type="int",default=5,
			help="Maximum iterations for iterative alignment, default is 7.")

                self.parser.add_option("--Tol", dest="Tol",type="float",default=0.5,
                        help="Tolerance for iterative alignment, in pixels", metavar="#")

		self.parser.add_option("--Patch",dest="Patch",metavar="#,#",type=str,default="0,0",
			help="Number of patches to be used for patch based alignment. Default 0,0 corresponds to full frame alignment.")

		self.parser.add_option("--MaskCent",dest="MaskCent",metavar="#,#",type=str,default="0,0",
			help="Coordinates for center of subarea that will be used for alignment. Default 0,0 corresponds to center coordinate.")

		self.parser.add_option("--MaskSize",dest="MaskSize",metavar="#,#",type=str,default="0,0",
			help="The size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")

		self.parser.add_option("--Throw",dest="Throw",metavar="#",type=int,default=0,
                        help="Throw initial number of frames")

		self.parser.add_option("--Trunc",dest="Trunc",metavar="#",type=int,default=0,
                        help="Truncate last number of frames")

		### making these into general options
#		self.parser.add_option("--doseweight",dest="doseweight",metavar="bool", default=False, 
#			action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")

#		self.parser.add_option("--FmDose",dest="FmDose",metavar="float",type=float,
#                        help="Frame dose in e/A^2. If not specified, will get value from database")

	#=======================
	def checkConflicts(self):
		super(MotionCorr2UCSFAlignStackLoop,self).checkConflicts()
		# does NOT keep stack by default
		if self.params['keepstack'] is True:
			apDisplay.printWarning('Frame stack saving not available to MotionCorr2 from UCSF')
			self.params['keepstack'] = False

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.MotionCorr2_UCSF()

	def setOtherProcessImageResultParams(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# include both hostname and gpu to identify the temp output
		#self.temp_aligned_sumpath = 'temp%s.gpuid_%d_sum.mrc' % (self.hostname, self.gpuid)
		super(MotionCorr2UCSFAlignStackLoop,self).setOtherProcessImageResultParams()
		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.gpuid)
		#self.temp_aligned_stackpath = 'temp%s.gpuid_%d_aligned_st.mrc' % (self.hostname, self.gpuid)
		self.framealigner.setKV(self.dd.getKVFromImage(self.dd.image))
		self.framealigner.setTotalFrames(self.dd.getNumberOfFrameSaved())
		if self.params['totaldose'] is not None:
			self.framealigner.setTotalDose(self.params['totaldose'])
		else:
			self.framealigner.setTotalDose(apDatabase.getDoseFromImageData(self.dd.image))
#		self.temp_aligned_dw_sumpath = 'temp%s.gpuid_%d_sum_DW.mrc' % (self.hostname, self.params['gpuid'])
#		self.framealigner.setFmDose()

	def organizeAlignedSum(self):
		'''
		Move local temp results to rundir in the official names
		'''
		temp_aligned_sumpath = self.temp_aligned_sumpath
		temp_aligned_dw_sumpath = self.temp_aligned_dw_sumpath
		if os.path.isfile(temp_aligned_sumpath):
			if self.params['doseweight'] is True:
				shutil.move(temp_aligned_dw_sumpath,self.dd.aligned_dw_sumpath)
		super(MotionCorr2UCSFAlignStackLoop,self).organizeAlignedSum()

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		if os.path.isfile(self.dd.aligned_sumpath):
			if self.params['doseweight'] is True:
				self.params['align_dw_label'] = self.params['alignlabel']+"-DW"
				self.aligned_dw_imagedata = self.dd.makeAlignedDWImageData(alignlabel=self.params['align_dw_label'])

		super(MotionCorr2UCSFAlignStackLoop,self).organizeAlignedStack()

if __name__ == '__main__':
	makeStack = MotionCorr2UCSFAlignStackLoop()
	makeStack.run()
