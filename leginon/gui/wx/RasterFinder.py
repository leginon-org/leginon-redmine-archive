# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import wx.lib.filebrowsebutton as filebrowse
import threading

import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.Settings
import leginon.gui.wx.AutoTargetFinder
import leginon.gui.wx.IceTargetFinder
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
from leginon.gui.wx.Presets import PresetChoice
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.AutoTargetFinder.Panel):
	def initialize(self):
		leginon.gui.wx.AutoTargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.AutoTargetFinder.SettingsDialog

		self.imagepanel.addTargetTool('Raster', wx.Colour(0, 255, 255), settings=True)
		
		self.imagepanel.addTargetTool('Polygon Vertices', wx.Colour(255,255,0), settings=True, target=True, shape='polygon')
		self.imagepanel.selectiontool.setDisplayed('Polygon Vertices', True)
		self.imagepanel.setTargets('Polygon Vertices', [])
	

	
		self.imagepanel.addTargetTool('Polygon Raster', wx.Colour(255,128,0))
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, exp=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = leginon.gui.wx.AutoTargetFinder.OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Raster':
			dialog = RasterSettingsDialog(self)
		elif evt.name == 'Polygon Vertices':
			dialog = PolygonSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = self._FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = self._FinalSettingsDialog(self)
		# modeless display
		dialog.Show(True)

	def _FinalSettingsDialog(self,parent):
		# This "private call" allows the class in the module containing
		# a subclass to redefine it in that module
		return FinalSettingsDialog(parent)
	
class OriginalSettingsDialog(leginon.gui.wx.AutoTargetFinder.OriginalSettingsDialog):
	pass

class RasterSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return RasterScrolledSettings(self,self.scrsize,False)

class RasterScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Raster')
		sbszraster = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Spacing/Angle Calculator')
		sbszauto = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['raster spacing'] = IntEntry(self, -1, chars=4, min=1)
		self.widgets['raster spacing asymm'] = IntEntry(self, -1, chars=4)
		self.widgets['raster limit'] = IntEntry(self, -1, chars=4, min=1)
		self.widgets['raster limit asymm'] = IntEntry(self, -1, chars=4)
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=4)
		self.widgets['raster center on image'] = wx.CheckBox(self, -1, 'Center on image')
		self.widgets['raster center x'] = IntEntry(self, -1, chars=4)
		self.widgets['raster center y'] = IntEntry(self, -1, chars=4)
		self.widgets['raster symmetric'] = wx.CheckBox(self, -1, '&Symmetric')

		## auto raster
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')
		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		self.widgets['raster preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['raster preset'].setChoices(presets)
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)


		szauto = wx.GridBagSizer(5, 5)
		szauto.Add(self.autobut, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Raster Preset')
		szauto.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster preset'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Overlap percent')
		szauto.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster overlap'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		movetypes = self.node.calclients.keys()
		# beam size is not a valid move type
		movetypes.remove('beam size')
		self.widgets['raster movetype'] = Choice(self, -1, choices=movetypes)
		label = wx.StaticText(self, -1, 'Move Type')
		szauto.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster movetype'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszauto.Add(szauto, 1, wx.EXPAND|wx.ALL,5)

		szraster = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'XY symmetry:')
		szraster.Add(label, (0,0), (1,1) , wx.ALIGN_CENTER_VERTICAL)

		self.Bind(wx.EVT_CHECKBOX, self.onToggleSymm, self.widgets['raster symmetric'])
		szraster.Add(self.widgets['raster symmetric'], (0,1), (1,2) , wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.widgets['raster symmetric'].SetMinSize((120,30))

		label = wx.StaticText(self, -1, 'Spacing (x,y):')
		szraster.Add(label, (1,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster spacing'], (1,1), (1,1), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.Add(self.widgets['raster spacing asymm'], (1,2), (1,1), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Num points (x,y):')
		szraster.Add(label, (2,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster limit'], (2,1), (1,1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.Add(self.widgets['raster limit asymm'], (2,2), (1,1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.AddGrowableCol(1)

		label = wx.StaticText(self, -1, 'Angle:')
		szraster.Add(label, (3,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster angle'], (3,1), (1,2), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)

		szraster.Add(self.widgets['raster center on image'], (4,0), (1,3), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		self.Bind(wx.EVT_CHECKBOX, self.onCheckBox, self.widgets['raster center on image'])

		label = wx.StaticText(self, -1, 'Center on x,y:')
		szraster.Add(label, (5,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster center x'], (5,1), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster center y'], (5,2), (1,1), wx.ALIGN_CENTER_VERTICAL)

		if self.widgets['raster center on image'].GetValue():
			self.widgets['raster center x'].Enable(False)
			self.widgets['raster center y'].Enable(False)

		if self.widgets['raster symmetric'].GetValue():
			self.widgets['raster spacing asymm'].Enable(False)
			self.widgets['raster limit asymm'].Enable(False)
			self.widgets['raster spacing asymm'].SetValue(None)
			self.widgets['raster limit asymm'].SetValue(None)
		else:
			self.widgets['raster spacing asymm'].Enable(True)
			self.widgets['raster limit asymm'].Enable(True)		

		sbszraster.Add(szraster, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszauto,sbszraster, szbutton]

	def onToggleSymm(self, evt):
		if self.widgets['raster symmetric'].GetValue():
			self.widgets['raster spacing asymm'].Enable(False)
			self.widgets['raster limit asymm'].Enable(False)
			self.widgets['raster spacing asymm'].SetValue(None)
			self.widgets['raster limit asymm'].SetValue(None)
		else:
			self.widgets['raster spacing asymm'].SetValue(self.widgets['raster spacing'].GetValue())
			self.widgets['raster limit asymm'].SetValue(self.widgets['raster limit'].GetValue())
			self.widgets['raster spacing asymm'].Enable(True)
			self.widgets['raster limit asymm'].Enable(True)			
		return

	def onAutoButton(self, evt):
		self.dialog.setNodeSettings()
		s,a = self.node.autoSpacingAngle()
		if s is not None:
			self.widgets['raster spacing'].SetValue(s)
			self.widgets['raster angle'].SetValue(a)
			self.widgets['raster spacing asymm'].SetValue(s)

	def onCheckBox(self, evt):
		if self.widgets['raster center on image'].GetValue():
			self.widgets['raster center x'].Enable(False)
			self.widgets['raster center y'].Enable(False)
		else:		
			self.widgets['raster center x'].Enable(True)
			self.widgets['raster center y'].Enable(True)

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.createRaster()
		self.panel.imagepanel.showTypeToolDisplays(['Raster'])

class PolygonSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return PolygonScrolledSettings(self,self.scrsize,False)

class PolygonScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Polygon')
		sbszpolygon = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['select polygon'] = wx.CheckBox(self, -1, 'Wait for polygon selection')
		self.widgets['publish polygon'] = wx.CheckBox(self, -1, 'Publish polygon vertices as targets')

		szpolygon = wx.GridBagSizer(5, 5)
		szpolygon.Add(self.widgets['select polygon'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpolygon.Add(self.widgets['publish polygon'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbszpolygon.Add(szpolygon, 1, wx.EXPAND|wx.ALL, 5)

		sbszstats = self.createStatsBoxSizer()

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszpolygon, sbszstats, szbutton]

	def createStatsBoxSizer(self):
		sb = wx.StaticBox(self, -1, 'Statistics')
		sbszstats = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['lattice hole radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['lattice zero thickness'] = FloatEntry(self, -1, chars=6)

		szstats = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Radius:')
		szstats.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice hole radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Reference Intensity:')
		szstats.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice zero thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szstats.AddGrowableCol(1)

		sbszstats.Add(szstats, 1, wx.EXPAND|wx.ALL, 5)
		return sbszstats

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.setPolygon()
		self.panel.imagepanel.showTypeToolDisplays(['Polygon Raster'])

class PolygonRasterSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return PolygonRasterScrolledSettings(self,self.scrsize,False)

class PolygonRasterScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Polygon Raster')
		sbszpolygon = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szpolyraster = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'No Settings')
		szpolyraster.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszpolygon.Add(szpolyraster, 1, wx.EXPAND|wx.ALL, 5)
		return [sbszpolygon,]

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.IceTargetFinder.FinalScrolledSettings):
	this = 'RasterTargetFinder'

class SettingsDialog(leginon.gui.wx.AutoTargetFinder.SettingsDialog):
	pass

class ScrolledSettings(leginon.gui.wx.AutoTargetFinder.ScrolledSettings):
	pass



if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raster Finder Test')
			panel = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

