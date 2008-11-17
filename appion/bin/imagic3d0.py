#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import apDB
import sys
import re
import appionScript
import appionData

import apParam
import apRecon
import apDisplay
import apEMAN
import apFile
import apUpload
import apDatabase
import apStack
appiondb = apDB.apdb

#=====================
#=====================
class imagic3d0Script(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")

		self.parser.add_option("--reclassId", dest="reclassId",
			help="ID for reclassification of reference-free alignment", metavar="int")
		self.parser.add_option("--norefId", dest="norefId",
			help="ID for reference-free alignment", metavar="int")
		self.parser.add_option("--norefClassId", dest="norefClassId", type="int",
			help="reference free class id", metavar="INT")
		#self.parser.add_option("--file_new", dest="file_new",
		#	help="Filename of the new class averages", metavar="FILE")

		self.parser.add_option("--3_projections", dest="projections", type="str",
			help="3 initial projections for angular reconstitution", metavar="STR")
		self.parser.add_option("--symmetry", dest="symmetry", type="str",
			help="symmetry of the object", metavar="STR")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", #default=10,
			help="angular increment for euler angle search", metavar="INT")
		self.parser.add_option("--num_classums", dest="num_classums", type="int",
			help="total number of classums used for 3d0 construction", metavar="INT")	
		self.parser.add_option("--ham_win", dest="ham_win", type="float", 
			help="similar to lp-filtering parameter that determines detail in 3d map", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", #default=0.8
			help="object size as fraction of image size", metavar="float")	
		self.parser.add_option("--repalignments", dest="repalignments", type="int",
			help="number of alignments to reprojections", metavar="INT")
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float",
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float",
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float",
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="float",
			help="automasking parameter that determines object thresholding", metavar="float")
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	#default=25
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int",	#default=25
			help="angular increment of reprojections for euler angle refinement", metavar="INT")

		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to which output file will be saved", metavar="PATH")
		self.parser.add_option("-r", "--runid", dest="runId",
			help="Name assigned to this reclassification", metavar="TEXT")
		self.parser.add_option("--description", dest="description", type="str",
			help="description of run", metavar="STR")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")

		return 

	#=====================
	def checkConflicts(self):
		if (self.params['reclassId'] is None and self.params['norefClassId'] is None) :
			apDisplay.printError("There is no reclassification or noref-classification ID specified")
		if self.params['runId'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['projections'] is None:
			apDisplay.printError("enter 3 projections from which to begin angular reconstitution")
		if self.params['symmetry'] is None:
			apDisplay.printError("enter object symmetry")
		if self.params['euler_ang_inc'] is None:
			apDisplay.printError("enter euler angle increment")
		if self.params['num_classums'] is None:
			apDisplay.printError("enter number of classums used for creating 3d0")
		if self.params['ham_win'] is None:
			apDisplay.printError("enter value for hamming window")
		if self.params['object_size'] is None:
			apDisplay.printError("enter value for object size as fraction of image size")
		if self.params['repalignments'] is None:
			apDisplay.printError("enter number of alignments to reprojections")
		if self.params['amask_dim'] is None:
			apDisplay.printError("enter automask parameter amask_dim")
		if self.params['amask_lp'] is None:
			apDisplay.printError("enter automask parameter amask_lp")
		if self.params['amask_sharp'] is None:
			apDisplay.printError("enter automask parameter amask_sharp")
		if self.params['amask_thresh'] is None:
			apDisplay.printError("enter automask parameter amask_thresh")
		if self.params['mrarefs_ang_inc'] is None:
			apDisplay.printError("enter angular increment of forward projections for MRA")
		if self.params['forw_ang_inc'] is None:
			apDisplay.printError("enter angular increment of forward projections for euler angle refinement")
		
		return

	#=====================
	def setOutDir(self):
	
		# get reference-free classification and reclassification parameters
		norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefClassId'])

		if norefclassdata is True:
			self.params['apix'] = norefclassdata['norefRun']['stack']['pixelsize']
			self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid
			self.params['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
			path = norefclassdata['norefRun']['path']['path']
			return

		reclassdata = appiondb.direct_query(appionData.ApImagicReclassifyData, self.params['reclassId'])
		if reclassdata is True:
			self.params['apix'] = reclassdata['norefclass']['norefRun']['stack']['pixelsize']
			self.params['stackid'] = reclassdata['norefclass']['norefRun']['stack'].dbid
			self.params['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
			path = reclassdata['norefclass']['norefRun']['path']['path']
			return
		
		if norefclassdata is None and reclassdata is None: 
			apDisplay.printError("class averages not in the database")

		uppath = os.path.abspath(os.path.join(path, "../.."))
		position = uppath.find("data")
		uppath = uppath[:position] + 'data00' + uppath[(position+6):]
		self.params['outdir'] = os.path.join(uppath, "clsavgstacks", self.params['runid'])	



	def upload3d0(self, mrcmodel):
		reclassq = appionData.ApImagic3d0Data()
		#reclassq['name'] = model
		reclassq['runname'] = self.params['runId']
		if self.params['norefClassId'] is not None:
			reclassq['norefclass'] = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefClassId'])
		elif self.params['reclassId'] is not None:
			reclassq['reclass'] = appiondb.direct_query(appionData.ApImagicReclassifyData, self.params['reclassId'])
		#reclassq['projections'] = self.params['projections']
		reclassq['euler_ang_inc'] = self.params['euler_ang_inc']
		reclassq['ham_win'] = self.params['ham_win']
		reclassq['obj_size'] = self.params['object_size']
		reclassq['repalignments'] = self.params['repalignments']
		reclassq['amask_dim'] = self.params['amask_dim']
		reclassq['amask_lp'] = self.params['amask_lp']
		reclassq['amask_sharp'] = self.params['amask_sharp']
		reclassq['amask_thresh'] = self.params['amask_thresh']
		reclassq['mra_ang_inc'] = self.params['mrarefs_ang_inc']
		reclassq['forw_ang_inc'] = self.params['forw_ang_inc']
		reclassq['description'] = self.params['description']
		reclassq['num_classums'] = self.params['num_classums']
		reclassq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(self.params['outdir'])))
		reclassq['hidden'] = False
		if self.params['commit'] is True:
			reclassq.insert()
		return 


	#=====================
	def start(self):
		self.params['projections'] = self.params['projections'].replace(",", ";")
		print self.params
		
		# get reference-free classification and reclassification parameters
		if self.params['norefClassId'] is not None:
			norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefClassId'])
			self.params['apix'] = norefclassdata['norefRun']['stack']['pixelsize']
			self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid
			stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
			binning = norefclassdata['norefRun']['norefParams']['bin']
			self.params['boxsize'] = stack_box_size / binning
			orig_path = norefclassdata['norefRun']['path']['path']
			orig_file = norefclassdata['classFile']
			linkingfile = orig_path+"/"+orig_file
		elif self.params['reclassId'] is not None:
			reclassdata = appiondb.direct_query(appionData.ApImagicReclassifyData, self.params['reclassId'])
			self.params['apix'] = reclassdata['norefclass']['norefRun']['stack']['pixelsize']
			self.params['stackid'] = reclassdata['norefclass']['norefRun']['stack'].dbid
			stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
			binning = reclassdata['norefclass']['norefRun']['norefParams']['bin']
			self.params['boxsize'] = stack_box_size / binning
			orig_path = reclassdata['path']['path']
			orig_runname = reclassdata['runname']
			orig_file = "reclassified_classums_sorted"
			linkingfile = orig_path+"/"+orig_runname+"/"+orig_file
		else:
			apDisplay.printError("class averages not in the database")
		
		filename = "imagicCreate3d0.batch"
		f = open(filename, 'w')
		
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['outdir'])+"/\n")		f.write("rm ordered0.*\n")		f.write("rm sino_ordered0.*\n")
		f.write("ln -s "+linkingfile+".img start_stack.img\n") 
		f.write("ln -s "+linkingfile+".hed start_stack.hed\n")
		if self.params['norefClassId'] is not None:
			# THERE IS A REALLY STUPID IMAGIC ERROR WHERE IT DOESN'T READ IMAGIC FORMAT CREATED BY OTHER 
			# PROGRAMS, AND SO FAR THE ONLY WAY I CAN DEAL WITH IT IS BY WIPING OUT THE HEADERS!
			f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF > imagicCreate3d0.log\n")
			f.write("start_stack\n")
			f.write("start_stack_copy\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/headers.e <<EOF >> imagicCreate3d0.log\n")
			f.write("start_stack_copy\n")
			f.write("write\n")
			f.write("wipe\n")
			f.write("all\n")
			f.write("EOF\n")
			f.write("rm start_stack.*\n")
			f.write("ln -s start_stack_copy.img start_stack.img\n") 
			f.write("ln -s start_stack_copy.hed start_stack.hed\n")
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF > imagicCreate3d0.log\n")		f.write(str(self.params['symmetry'])+"\n")
		f.write("new\n")
		f.write("fresh\n")		f.write("start_stack\n")		f.write(str(self.params['projections'])+"\n")		f.write("ordered0\n") 		f.write("sino_ordered0\n")		f.write("yes\n")		f.write(".9\n")		f.write("my_sine\n")		f.write(str(self.params['euler_ang_inc'])+"\n")		f.write("30\n")		f.write("no\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF >> imagicCreate3d0.log\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("new\n")		f.write("add\n")		f.write("start_stack\n")		f.write("1-"+str(self.params['num_classums'])+"\n")		f.write("ordered0\n")		f.write("sino_ordered0\n")		f.write("yes\n")		f.write("0.9\n")		f.write("my_sine\n")		f.write("5.0\n")		f.write("yes\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")		f.write("no\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("yes\n")		f.write("ordered0\n")		f.write("ANGREC_HEADER_VALUES\n")		f.write("3d0_ordered0\n")		f.write("rep0_ordered0\n")		f.write("err0_ordered0\n")		f.write("no\n")		f.write("0.8\n")		f.write("0.8\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagicCreate3d0.log\n")		f.write("all\n")		f.write("ccf\n")		f.write("ordered0\n")		f.write("ordered0_repaligned\n")		f.write("rep0_ordered0\n")		f.write("0.2\n")		f.write("-180,180\n")		f.write("5\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")		f.write("no\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("yes\n")		f.write("ordered0_repaligned\n")		f.write("ANGREC_HEADER_VALUES\n")		f.write("3d0_ordered0_repaligned\n")		f.write("rep0_ordered0_repaligned\n")		f.write("err0_ordered0_repaligned\n")		f.write("no\n")		f.write("0.8\n")		f.write("0.8\n")		f.write("EOF\n\n")		f.write("set j=1\n")		f.write("while ($j<"+str(self.params['repalignments'])+")\n")		f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicCreate3d0.log\n")		f.write("ordered0_repaligned\n")		f.write("to_be_aligned\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagicCreate3d0.log\n")		f.write("all\n")		f.write("ccf\n")		f.write("to_be_aligned\n")		f.write("ordered0_repaligned\n")		f.write("rep0_ordered0_repaligned\n")		f.write("0.2\n")		f.write("-180,180\n")		f.write("5\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")		f.write("no\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("yes\n")		f.write("ordered0_repaligned\n")		f.write("ANGREC_HEADER_VALUES\n")		f.write("3d0_ordered0_repaligned\n")		f.write("rep0_ordered0_repaligned\n")		f.write("err0_ordered0_repaligned\n")		f.write("no\n")		f.write(str(self.params['ham_win'])+"\n")		f.write(str(self.params['object_size'])+"\n")		f.write("EOF\n")		f.write("@ j++\n")		f.write("end\n\n")		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagicCreate3d0.log\n")		f.write("DO_IT_ALL\n")		f.write("3d0_ordered0_repaligned\n")		f.write("3d0_ordered0_repaligned_modvar\n")		f.write("yes\n")		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")		f.write(str(self.params['amask_sharp'])+"\n")		f.write("AUTOMATIC\n")		f.write(str(self.params['amask_thresh'])+"\n")		f.write("mask_3d0_ordered0_repaligned\n")		f.write("masked_3d0_ordered0_repaligned\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagicCreate3d0.log\n")		f.write("IMAGIC\n")		f.write("MRC\n")		f.write("3d\n")		f.write("multiple\n")		f.write("masked_3d0_ordered0_repaligned\n")		f.write("masked_3d0_ordered0_repaligned.mrc\n")		f.write("yes\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/threed/forward.e <<EOF >> imagicCreate3d0.log\n")		f.write("masked_3d0_ordered0_repaligned\n")		f.write("-99999\n")		f.write("projections\n")		f.write("widening\n")		f.write("mrarefs_masked_3d0\n")		f.write("asym_triangle\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("equidist\n")		f.write("zero\n")		f.write(str(self.params['mrarefs_ang_inc'])+"\n")		f.write("EOF\n")		f.write("/usr/local/IMAGIC/threed/forward.e <<EOF >> imagicCreate3d0.log\n")		f.write("masked_3d0_ordered0_repaligned\n")		f.write("-99999\n")		f.write("projections\n")		f.write("widening\n")		f.write("masked_3d0_ordered0_repaligned_forward\n")		f.write("asym_triangle\n")		f.write(str(self.params['symmetry'])+"\n")		f.write("equidist\n")		f.write("zero\n")		f.write(str(self.params['forw_ang_inc'])+"\n")		f.write("EOF\n\n")		f.write("rm to_be_aligned.*\n")		f.write("cp masked_3d0_ordered0_repaligned_forward.img masked_3d_ordered_repaligned_forward.img\n")		f.write("cp masked_3d0_ordered0_repaligned_forward.hed masked_3d_ordered_repaligned_forward.hed\n")		f.write("cp mrarefs_masked_3d0.img mrarefs_masked_3d.img\n")		f.write("cp mrarefs_masked_3d0.hed mrarefs_masked_3d.hed\n") 
		f.close()
		os.chdir(str(self.params['outdir']))
		os.system('chmod 755 imagicCreate3d0.batch')
		os.system('./imagicCreate3d0.batch')

		mrcname = self.params['outdir']+"/masked_3d0_ordered0_repaligned.mrc"

		### create chimera slices
		apRecon.renderSnapshots(mrcname, 30, None, 
			1.5, 1.0, self.params['apix'], 'c1', self.params['boxsize'], False)

		### upload density
		self.upload3d0(mrcname)

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	imagic3d0 = imagic3d0Script()
	imagic3d0.start()
	imagic3d0.close()

	
