# -*- coding: iso-8859-1 -*-
import copy
import data
import wx
from gui.wx.Entry import IntEntry, FloatEntry, EVT_ENTRY

ConfigurationChangedEventType = wx.NewEventType()
SetConfigurationEventType = wx.NewEventType()

EVT_CONFIGURATION_CHANGED = wx.PyEventBinder(ConfigurationChangedEventType)
EVT_SET_CONFIGURATION = wx.PyEventBinder(SetConfigurationEventType)

class ConfigurationChangedEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, ConfigurationChangedEventType,
																source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class SetConfigurationEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, SetConfigurationEventType, source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class CameraPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)
		self.geometry = None
		self.binnings = {'x': [1,2,4,8,16], 'y': [1,2,4,8,16]}

		# geometry
		std = wx.StaticText(self, -1, 'Dimension:')
		self.stdimension = wx.StaticText(self, -1, '')

		sto = wx.StaticText(self, -1, 'Offset:')
		self.stoffset = wx.StaticText(self, -1, '')

		stb = wx.StaticText(self, -1, 'Binning:')
		self.stbinning = wx.StaticText(self, -1, '')

		bcustom = wx.Button(self, -1, 'Custom...')

		self.ccommon = wx.Choice(self, -1)

		self.szmain = wx.GridBagSizer(3, 3)

		self.szmain.Add(std, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stdimension, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(sto, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stoffset, (1, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(stb, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stbinning, (2, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(self.ccommon, (3, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szmain.Add(bcustom, (3, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		# exposure time
		stet = wx.StaticText(self, -1, 'Exposure time:')
		self.feexposuretime = FloatEntry(self, -1, min=0, chars=7)
		stms = wx.StaticText(self, -1, 'ms')

		self.szmain.Add(stet, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz = wx.GridBagSizer(0, 3)
		sz.Add(self.feexposuretime, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(stms, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(sz, (4, 1), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizerAndFit(self.sbsz)

		self.Bind(wx.EVT_CHOICE, self.onCommonChoice, self.ccommon)
		self.Bind(wx.EVT_BUTTON, self.onCustomButton, bcustom)
		self.Bind(EVT_ENTRY, self.onExposureTime, self.feexposuretime)
		self.Bind(EVT_SET_CONFIGURATION, self.onSetConfiguration)

		self.Enable(False)

	def setSize(self, session):
		if session['instrument'] is None:
			return
		size = session['instrument']['camera size']
		if size is None:
			return
		self.size = {'x': size, 'y': size}

		self.Freeze()
		choices, self.common = self.getCenteredGeometries()
		self.ccommon.Clear()
		self.ccommon.AppendItems(choices)
		self.ccommon.SetSelection(0)
		self.setGeometry(self.common[self.ccommon.GetStringSelection()])
		self.Enable(True)
		self.szmain.Layout()
		self.Thaw()

	def onConfigurationChanged(self):
		evt = ConfigurationChangedEvent(self.getConfiguration(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onExposureTime(self, evt):
		self.onConfigurationChanged()

	def setCommonChoice(self):
		for key, geometry in self.common.items():
			flag = True
			for i in ['dimension', 'offset', 'binning']:
				if self.geometry[i] != geometry[i]:
					flag = False
					break
			if flag:
				self.ccommon.SetStringSelection(key)
				return
		if self.ccommon.FindString('(Custom)') is wx.NOT_FOUND:
			self.ccommon.Insert('(Custom)', 0)
			self.ccommon.SetSelection(0)

	def _getDimension(self):
		return self.geometry['dimension']

	def _setDimension(self, value):
		self.geometry['dimension'] = value
		self.setCommonChoice()

	def _getOffset(self):
		return self.geometry['offset']

	def _setOffset(self, value):
		self.geometry['offset'] = value
		self.setCommonChoice()

	def _getBinning(self):
		return self.geometry['binning']

	def _setBinning(self, value):
		self.geometry['binning'] = value
		self.setCommonChoice()

	def _getExposureTime(self):
		return self.feexposuretime.GetValue()

	def _setExposureTime(self, value):
		self.feexposuretime.SetValue(value)

	def onCommonChoice(self, evt):
		key = evt.GetString()
		if key == '(Custom)':
			return
		if self.setGeometry(self.common[key]):
			self.onConfigurationChanged()
		n = self.ccommon.FindString('(Custom)')
		if n is not wx.NOT_FOUND:
			self.ccommon.Delete(n)

	def onCustomButton(self, evt):
		dialog = CustomDialog(self, self.getGeometry())
		if dialog.ShowModal() == wx.ID_OK:
			if self.setGeometry(dialog.getGeometry()):
				self.onConfigurationChanged()
			self.setCommonChoice()
		dialog.Destroy()

	def getCenteredGeometry(self, dimension, binning):
		offset = (self.size['x']/binning - dimension)/2
		geometry = {'dimension': {'x': dimension, 'y': dimension},
								'offset': {'x': offset, 'y': offset},
								'binning': {'x': binning, 'y': binning}}
		return geometry

	def getCenteredGeometries(self):
		geometries = {}
		if self.size['x'] != self.size['y']:
			return geometries
		if self.binnings['x'] != self.binnings['y']:
			return geometries
		dimensions = map(lambda b: self.size['x']/b, self.binnings['x'])
		dimensions.reverse()
		keys = []
		for d in dimensions:
			for b in self.binnings['x']:
				if d*b <= self.size['x']:
					key = '%d� � %d' % (d, b)
					geometries[key] = self.getCenteredGeometry(d, b)
					keys.append(key)
				else:
					break
		return keys, geometries

	def validateGeometry(self, geometry):
		for a in ['x', 'y']:
			if geometry['dimension'][a] < 1 or geometry['offset'][a] < 0:
				return False
			if geometry['binning'][a] not in self.binnings[a]:
				return False
			size = geometry['dimension'][a] + geometry['offset'][a]
			size *= geometry['binning'][a]
			if size > self.size[a]:
				return False
		return True

	def setGeometry(self, geometry):
		if geometry == self.geometry:
			return False
		if not self.validateGeometry(geometry):
			raise ValueError
		dimension = '%d � %d' % (geometry['dimension']['x'],
														geometry['dimension']['y'])
		self.stdimension.SetLabel(dimension)
		offset = '(%d, %d)' % (geometry['offset']['x'],
															geometry['offset']['y'])
		self.stoffset.SetLabel(offset)
		binning = '%d � %d' % (geometry['binning']['x'],
														geometry['binning']['y'])
		self.stbinning.SetLabel(binning)
		self.geometry = geometry
		self.Freeze()
		self.szmain.Layout()
		self.Thaw()
		return True

	def getGeometry(self):
		return self.geometry

	def getConfiguration(self):
		g = self.getGeometry()
		if g is None:	
			return None
		c = dict(g)
		g['exposure time'] = self._getExposureTime()
		return g

	def _setGeometry(self, geometry):
		self.geometry = copy.deepcopy(self.geometry)
		for g in ['dimension', 'offset', 'binning']:
			if g not in self.geometry:
				self.geometry[g] = {}
			try:
				self.geometry[g].update(geometry[g])
				if g == 'offset':
					label = '(%d, %d)'
				else:
					label = '%d � %d'
				label = label % (self.geometry[g]['x'], self.geometry[g]['y'])
				getattr(self, 'st' + g).SetLabel(label)
			except KeyError:
				pass
		self.Freeze()
		self.szmain.Layout()
		self.Thaw()
		return True

	def _setConfiguration(self, value):
		try:
			self._setExposureTime(value['exposure time'])
		except KeyError:
			pass
		self._setGeometry(value)
		self.setCommonChoice()

	def setConfiguration(self, value):
		self._setExposureTime(value['exposure time'])
		self.setGeometry(value)

	def getData(self):
		return data.CameraSettingsData(initializer=self.getConfiguration())

	def setData(self, d):
		self.setConfiguration(d.toDict())
		self.setCommonChoice()

	def onSetConfiguration(self, evt):
		self.setConfiguration(evt.configuration)

class CustomDialog(wx.Dialog):
	def __init__(self, parent, geometry):
		wx.Dialog.__init__(self, parent, -1, 'Custom')
		binnings = parent.binnings

		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stdimension = wx.StaticText(self, -1, 'Dimension:')
		self.iexdimension = IntEntry(self, -1, min=1, max=parent.size['x'],
																	chars=len(str(parent.size['x'])))
		self.ieydimension = IntEntry(self, -1, min=1, max=parent.size['y'],
																	chars=len(str(parent.size['y'])))
		stbinning = wx.StaticText(self, -1, 'Binning:')
		self.cxbinning = wx.Choice(self, -1, choices=parent.binnings['x'])
		self.cybinning = wx.Choice(self, -1, choices=parent.binnings['y'])
		stoffset = wx.StaticText(self, -1, 'Offset:')
		self.iexoffset = IntEntry(self, -1, min=0, max=parent.size['x'],
																	chars=len(str(parent.size['x'])))
		self.ieyoffset = IntEntry(self, -1, min=0, max=parent.size['y'],
																	chars=len(str(parent.size['y'])))
		self.szxy = wx.GridBagSizer(5, 5)
		self.szxy.Add(stx, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(sty, (0, 2), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(stdimension, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.iexdimension, (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(self.ieydimension, (1, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(stbinning, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.cxbinning, (2, 1), (1, 1),
									wx.ALIGN_CENTER|wx.ALL)
		self.szxy.Add(self.cybinning, (2, 2), (1, 1),
									wx.ALIGN_CENTER|wx.ALL)
		self.szxy.Add(stoffset, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.iexoffset, (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(self.ieyoffset, (3, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)

		bok = wx.Button(self, wx.ID_OK, 'OK')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbsz.Add(self.szxy, 0, wx.ALIGN_CENTER)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.sbsz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		sz.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		if geometry is not None:
			self.iexdimension.SetValue(int(geometry['dimension']['x']))
			self.ieydimension.SetValue(int(geometry['dimension']['y']))
			self.cxbinning.SetStringSelection(str(geometry['binning']['x']))
			self.cybinning.SetStringSelection(str(geometry['binning']['y']))
			self.iexoffset.SetValue(int(geometry['offset']['x']))
			self.ieyoffset.SetValue(int(geometry['offset']['y']))

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onOK, bok)

	def getGeometry(self):
		geometry = {'dimension': {}, 'binning': {}, 'offset': {}}
		geometry['dimension']['x'] = self.iexdimension.GetValue()
		geometry['dimension']['y'] = self.ieydimension.GetValue()
		geometry['binning']['x'] = int(self.cxbinning.GetStringSelection())
		geometry['binning']['y'] = int(self.cybinning.GetStringSelection())
		geometry['offset']['x'] = self.iexoffset.GetValue()
		geometry['offset']['y'] = self.ieyoffset.GetValue()
		return geometry

	def onOK(self, evt):
		geometry = self.getGeometry()
		if geometry is not None and self.GetParent().validateGeometry(geometry):
			evt.Skip()
		else:
			dialog = wx.MessageDialog(self, 'Invalid camera geometry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Camera Test')
			panel = CameraPanel(frame)
			panel.setSize({'instrument': {'camera size': 1024}})
			panel.setGeometry({'dimension': {'x': 128, 'y': 128},
													'offset': {'x': 256, 'y': 256},
													'binning': {'x': 2, 'y': 2}})
			panel.getCenteredGeometries()
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

