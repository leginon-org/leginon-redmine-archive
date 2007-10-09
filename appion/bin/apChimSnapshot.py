#!/usr/bin/python

# -----------------------------------------------------------------------------
# Script to radially color a contour surface of a density map and save an
# image without starting the Chimera graphical user interface.  This uses
# the "OSMESA" version of Chimera.
#

# -----------------------------------------------------------------------------
#
import sys
import os
import chimera

chimlog=None

def openVolumeData(path, file_type="mrc", contour_level=1.5, color=None):

	from VolumeData import open_file_type
	g = open_file_type(path, file_type)

	from VolumeViewer import full_region, Rendering_Options, Data_Region
	region = full_region(g.size)
	
	region_name = 'none'
	ro = Rendering_Options()
	ro.show_outline_box = False
	ro.surface_smoothing = True

	dr = Data_Region(g, region, region_name, ro, message)

	if contour_level != None:
		dr.set_parameters(surface_levels = [contour_level])
	if color != None:
		dr.set_parameters(surface_colors = [color])

	dr.show('surface', dr.rendering_options, True, message)
	return dr

# -----------------------------------------------------------------------------
# Print status message.
#

def message(m):

	from chimera.replyobj import nogui_message
	nogui_message(m + '\n')

# -----------------------------------------------------------------------------
#
def color_surface_radially(surf, center):

	from SurfaceColor import color_surface, Radial_Color, Color_Map
	rc = Radial_Color()
#	rc.origin = center
	rc.origin = [0,0,0]
	vertices, triangles = surf.surface_groups()[0].geometry()
	rmin, rmax = rc.value_range(vertices, vertex_xform = None)
	data_values = (.5*rmax, .625*rmax, .75*rmax, .875*rmax, rmax)
	colors = [(0.933,0.067,0.067,1), (0.933,0.933,0.067,1), (0.067,0.933,0.067,1), (0.067,0.933,0.933,1), (0.067,0.067,0.933,1)]  
	# Red,green,blue,opacity
	rc.colormap = Color_Map(data_values, colors)
	color_surface(surf, rc, caps_only = False, auto_update = False)

# -----------------------------------------------------------------------------
#
def save_image(path, format):

	# propagate changes from C++ layer back to Python
	# can also be done via Midas module: Midas.wait(1)
	chimera.update.checkForChanges()

	# save an image
	chimera.printer.saveImage(path, format = format)

# -----------------------------------------------------------------------------
#
def radial_color_volume(tmp_path, vol_path, contour=1.5, vol_file_type="mrc", 
	zoom_factor=1.0, image_size=(512, 512), imgFormat="PNG", sym="C"):

	chimera.viewer.windowSize = image_size

	dr = openVolumeData(tmp_path, vol_file_type, contour)

	center = map(lambda s: .5*(s-1), dr.data.size) # Center for radial coloring
	m = dr.surface_model()

	#from chimera import runCommand
	runChimCommand('scale %.3f' % zoom_factor)   # Zoom

	image1 = vol_path+'.1.png'
	image2 = vol_path+'.2.png'
	image3 = vol_path+'.3.png'

	if sym=='Icosahedral':
		color_surface_radially(m, center)

		# move clipping planes to obscure back half
#		xsize,ysize,zsize=dr.data.size
#		hither=float(zsize)/5
#		runChimCommand('clip yon %.3f' % yon)
#		runChimCommand('clip hither -%.3f' % hither)
		
		save_image(image1, format=imgFormat)

		writeMessageToLog("turn: down 3-fold axis")
		runChimCommand('turn y 37.377')
		save_image(image2, format=imgFormat)
		
		writeMessageToLog("turn: viper orientation (2 fold)")
		runChimCommand('turn y 20.906')
		save_image(image3, format=imgFormat) 

	else:
		writeMessageToLog("turn: flip image 180")
		runChimCommand('turn x 180')
		save_image(image1, format=imgFormat)

		writeMessageToLog("turn: get tilt view")
		runChimCommand('turn x -45')
		save_image(image2, format=imgFormat)

		writeMessageToLog("turn: get side view")
		runChimCommand('turn x -45')
		save_image(image3, format=imgFormat)

		if sym is not 'D':
			image4 = vol_path+'.4.png'
			image5 = vol_path+'.5.png'

			writeMessageToLog("turn: get tilt 2")
			runChimCommand('turn x -45')
			save_image(image4, format=imgFormat)

			writeMessageToLog("turn: bottom view")
			runChimCommand('turn x -45')
			save_image(image5, format=imgFormat)

# -----------------------------------------------------------------------------
#

def runChimCommand(cmd):
	if chimlog is not None:
		f = open(chimlog, "a")
		f.write(str(cmd)+"\n")
		f.close()
		#nogui_message(cmd.strip()+"\n")
	chimera.runCommand(cmd)

# -----------------------------------------------------------------------------
#

def writeMessageToLog(msg):
	if chimlog is None:
		return
	f = open(chimlog, "a")
	f.write(str(msg)+"\n")
	f.close()

# -----------------------------------------------------------------------------
#

if True:
	env = os.environ.get('CHIMENV')
	if env is None:
		#writeMessageToLog("no environmental data")
		sys.exit(1)
	params = env.split(',')


	tmpfile_path = params[0] #sys.argv[2]
	volume_path = params[1] #sys.argv[3]
	rundir = os.path.dirname(volume_path)
	sym = params[2] #sys.argv[4]
	contour = float(params[3]) #sys.argv[5])
	zoom_factor = float(params[4]) #sys.argv[6])

	rundir = os.path.dirname(volume_path)
	chimlog = os.path.join(rundir, "chimera.log")

	writeMessageToLog("Environmental data: "+str(params))

	radial_color_volume(tmpfile_path, volume_path, contour, zoom_factor=zoom_factor, sym=sym)

	chimera.ChimeraExit()
	chimera.ChimeraSystemExit()
	sys.exit(1)






