import wx
import gui.wx.Data
from gui.wx.Entry import Entry, FloatEntry
import gui.wx.Node
from gui.wx.Presets import PresetChoice
import gui.wx.Settings

class Panel(gui.wx.Node.Panel):
	icon = 'atlasmaker'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1,
																name='%s.pMosaicTargetMaker' % name)
		self.szmain = wx.GridBagSizer(5, 5)

		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.bcreate = wx.Button(self, -1, 'Create Atlas')
		self.szmain.Add(self.bsettings, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(self.bcreate, (2, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_BUTTON, self.onCreateAtlas, self.bcreate)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onCreateAtlas(self, evt):
		self.node.makeMosaicTargetList()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = PresetChoice(self, -1)
		self.widgets['preset'].setChoices(presets)
		self.widgets['label'] = Entry(self, -1)
		self.widgets['radius'] = FloatEntry(self, -1, min=0.0, chars=9)
		self.widgets['overlap'] = FloatEntry(self, -1, min=0.0, chars=5)

		szradius = wx.GridBagSizer(5, 5)
		szradius.Add(self.widgets['radius'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'meters')
		szradius.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szoverlap = wx.GridBagSizer(5, 5)
		szoverlap.Add(self.widgets['overlap'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '%')
		szoverlap.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)

		label = wx.StaticText(self, -1, 'Preset:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Label:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Radius:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szradius, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Overlap:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szoverlap, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Mosaic')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return sbsz

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Target Maker Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

