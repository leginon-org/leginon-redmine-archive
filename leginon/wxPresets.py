import wx
import wx.lib.buttons
import sys, os

def getBitmap(filename):
	rundir = sys.path[0]
	iconpath = os.path.join(rundir, 'icons', filename)
	wximage = wx.Image(iconpath)
	bitmap = wx.BitmapFromImage(wximage)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

PresetOrderChangedEventType = wx.NewEventType()
PresetsChangedEventType = wx.NewEventType()

EVT_PRESET_ORDER_CHANGED = wx.PyEventBinder(PresetOrderChangedEventType)
EVT_PRESETS_CHANGED = wx.PyEventBinder(PresetsChangedEventType)

class PresetOrderChangedEvent(wx.PyEvent):
	def __init__(self, presets):
		wx.PyEvent.__init__(self)
		self.SetEventType(PresetOrderChangedEventType)
		self.presets = presets

class PresetsChangedEvent(wx.PyEvent):
	def __init__(self, presets):
		wx.PyEvent.__init__(self)
		self.SetEventType(PresetsChangedEventType)
		self.presets = presets

class PresetOrder(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		sizer = wx.GridBagSizer(3, 3)

		label = wx.StaticText(self, -1, 'Presets Order')
		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		self.choice = wx.Choice(self, -1)
		self.choice.Enable(False)

		self.insertbutton = wx.lib.buttons.GenBitmapButton(self, -1,
																												getBitmap('plus.png'),
																												size=(20, 20))
		self.insertbutton.SetBezelWidth(1)
		self.insertbutton.Enable(False)

		sizer.Add(self.choice, (1, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		sizer.Add(self.insertbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		self.listbox = wx.ListBox(self, -1)
		sizer.Add(self.listbox, (2, 0), (3, 1), wx.EXPAND|wx.ALL)

		self.deletebutton = wx.lib.buttons.GenBitmapButton(self, -1,
																												getBitmap('minus.png'),
																												size=(20, 20))
		self.deletebutton.SetBezelWidth(1)
		self.deletebutton.Enable(False)

		self.upbutton = wx.lib.buttons.GenBitmapButton(self, -1,
																										getBitmap('up.png'),
																										size=(20, 20))
		self.upbutton.SetBezelWidth(1)
		self.upbutton.Enable(False)

		self.downbutton = wx.lib.buttons.GenBitmapButton(self, -1,
																											getBitmap('down.png'),
																											size=(20, 20))
		self.downbutton.SetBezelWidth(1)
		self.downbutton.Enable(False)

		sizer.Add(self.deletebutton, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.upbutton, (3, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.downbutton, (4, 1), (1, 1),
							wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
		sizer.AddGrowableRow(4)
		self.SetSizerAndFit(sizer)

		self.Bind(wx.EVT_BUTTON, self.onInsert, self.insertbutton)
		self.Bind(wx.EVT_BUTTON, self.onDelete, self.deletebutton)
		self.Bind(wx.EVT_BUTTON, self.onUp, self.upbutton)
		self.Bind(wx.EVT_BUTTON, self.onDown, self.downbutton)
		self.Bind(wx.EVT_LISTBOX, self.onSelect, self.listbox)

		self.Bind(EVT_PRESETS_CHANGED, self.onPresetsChanged)

	def onPresetsChanged(self, evt):
		self.setChoices(evt.presets)

	def setChoices(self, choices):
		self.Freeze()
		self.choice.Clear()
		self.choice.AppendItems(choices)
		self.choice.Enable(choices)
		self.insertbutton.Enable(choices)
		self.Thaw()

	def getValues(self):
		values = []
		for i in range(self.listbox.GetCount()):
			try:
				values.append(self.listbox.GetString(i))
			except ValueError:
				raise
		return values

	def setValues(self, values):
		count = self.listbox.GetCount()
		if values is None:
			values = []
		n = len(values)
		if count < n:
			nsame = count
		else:
			nsame = n
		for i in range(nsame):
			try:
				if self.listbox.GetString(i) != values[i]:
					self.listbox.SetString(i, values[i])
			except ValueError:
				raise
		if count < n:
			self.listbox.InsertItems(values[nsame:], nsame)
		elif count > n:
			for i in range(count - 1, n - 1, -1):
				self.listbox.Delete(i)

	def presetsEditEvent(self):
		evt = PresetEditEvent(self.getValues())
		self.GetEventHandler().AddPendingEvent(evt)

	def onInsert(self, evt):
		try:
			string = self.choice.GetStringSelection()
		except ValueError:
			return
		n = self.listbox.GetSelection()
		if n < 0:
			self.listbox.Append(string)
		else:
			self.listbox.InsertItems([string], n)
			self.updateButtons(n + 1)
		self.presetsEditEvent()

	def onDelete(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0:
			self.listbox.Delete(n)
		count = self.listbox.GetCount()
		if n < count:
			self.listbox.Select(n)
			self.updateButtons(n)
		elif count > 0:
			self.listbox.Select(n - 1)
			self.updateButtons(n - 1)
		else:
			self.deletebutton.Enable(False)
		self.presetsEditEvent()

	def onUp(self, evt):
		n = self.listbox.GetSelection()
		if n > 0:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n - 1)
			self.listbox.Select(n - 1)
		self.updateButtons(n - 1)
		self.presetsEditEvent()

	def onDown(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0 and n < self.listbox.GetCount() - 1:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n + 1)
			self.listbox.Select(n + 1)
		self.updateButtons(n + 1)
		self.presetsEditEvent()

	def onSelect(self, evt):
		self.deletebutton.Enable(True)
		self.updateButtons(evt.GetSelection())

	def updateButtons(self, n):
		if n > 0:
			self.upbutton.Enable(True)
		else:
			self.upbutton.Enable(False)
		if n < self.listbox.GetCount() - 1:
			self.downbutton.Enable(True)
		else:
			self.downbutton.Enable(False)

