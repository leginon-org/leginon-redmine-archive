import numarray
import wx
import numarrayimage
import gui.wx.ImageViewerEvents as Events

class SizeScaler(wx.Choice):
	def __init__(self, parent, id):
		self.width = None
		self.height = None
		self.percentages = [10, 25, 50, 75, 100, 125, 150, 200, 400, 800, 1600]
		choices = [('%d' % percentage) + '%' for percentage in self.percentages]
		choices.append('Fit to page')
		wx.Choice.__init__(self, parent, id, choices=choices)
		self.SetSelection(self.percentages.index(100))
		self.Bind(wx.EVT_CHOICE, self.onChoice)

	def setSize(self, width, height):
		self.width = width
		self.height = height

	def onChoice(self, evt):
		evt.Skip()

		if self.width is None or self.height is None:
			return

		string = evt.GetString()
		if string == 'Fit to page':
			evt = Events.FitToPageEvent(self)
		else:
			i = evt.GetSelection()
			percentage = self.percentages[i]/100.0
			width = int(round(percentage*self.width))
			height = int(round(percentage*self.height))

			evt = Events.ScaleSizeEvent(self, width, height)
		self.GetEventHandler().AddPendingEvent(evt)

def getValueScaleBitmap(extrema, fromrange, width, height):
	types = [type(i) for i in fromrange]
	if float in types:
		arraytype = numarray.Float
	elif int in types:
		arraytype = numarray.Int
	else:
		raise TypeError

	array = numarray.arange(width, type=numarray.Float, shape=(1, width))
	array *= float(extrema[1] - extrema[0])/(width - 1)
	array += extrema[0]
	array = array.astype(arraytype)
	array = array.repeat(height)

	return numarrayimage.numarray2wxBitmap(array, fromrange=fromrange)

class ValueScaler(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.valuerange = None
		self.extrema = None
		self.type = None

		self.sizer = wx.GridBagSizer(3, 3)

		self.minlabel = wx.StaticText(self, -1)
		self.maxlabel = wx.StaticText(self, -1)

		self.minentry = wx.TextCtrl(self, -1, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
		self.maxentry = wx.TextCtrl(self, -1, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
		self.minentry.Enable(False)
		self.maxentry.Enable(False)

		self.minslider = wx.Slider(self, -1, 0, 0, 0)
		self.maxslider = wx.Slider(self, -1, 0, 0, 0)
		self.minslider.Enable(False)
		self.maxslider.Enable(False)

		self.sizer.Add(self.minlabel, (0, 1), (1, 1),
										wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.maxlabel, (0, 2), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.minentry, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.maxentry, (2, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.minslider, (1, 1), (1, 2), wx.EXPAND)
		self.sizer.Add(self.maxslider, (2, 1), (1, 2), wx.EXPAND)

		self.sizer.AddGrowableCol(1)
		self.sizer.AddGrowableCol(2)

		self.Bind(wx.EVT_SIZE, self.onSize)
		self.minentry.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
		self.maxentry.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
		self.minentry.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.maxentry.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.minslider.Bind(wx.EVT_SCROLL, self.onScroll)
		self.maxslider.Bind(wx.EVT_SCROLL, self.onScroll)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

	def setValueRange(self, extrema, valuerange=None):
		if valuerange is None:
			valuerange = extrema

		self.valuerange = valuerange
		self.extrema = extrema

		if self.extrema is None:
			self.type = None
			self.minentry.Enable(False)
			self.maxentry.Enable(False)
			self.minslider.Enable(False)
			self.maxslider.Enable(False)
			self.minlabel.SetLabel('')
			self.maxlabel.SetLabel('')
			self.minentry.SetValue('')
			self.maxentry.SetValue('')
			self.minslider.SetValue(self.minslider.GetMin())
			self.maxslider.SetValue(self.maxslider.GetMax())
		else:
			types = [type(value) for value in self.valuerange + self.extrema]
			if float in types:
				self.type = float
			elif int in types:
				self.type = int
			else:
				raise TypeError
			self.minlabel.SetLabel('%g' % extrema[0])
			self.maxlabel.SetLabel('%g' % extrema[1])
			self.minentry.SetValue('%g' % valuerange[0])
			self.maxentry.SetValue('%g' % valuerange[1])
			slidermin = self.minslider.GetMin()
			slidermax = self.maxslider.GetMax()
			sliderscale = float(slidermax - slidermin)/(extrema[1] - extrema[0])
			self.minslider.SetValue(
				int(round((valuerange[0] - extrema[0])*sliderscale + slidermin)))
			self.maxslider.SetValue(
				int(round((valuerange[1] - extrema[0])*sliderscale + slidermin)))
			self.minentry.Enable(True)
			self.maxentry.Enable(True)
			self.minslider.Enable(True)
			self.maxslider.Enable(True)

	def onEntry(self, eventobject, string):
		try:
			value = self.type(string)
		except:
			if eventobject is self.minentry:
				eventobject.SetValue('%g' % self.valuerange[0])
			elif eventobject is self.maxentry:
				eventobject.SetValue('%g' % self.valuerange[1])
			return
		if value < self.extrema[0] or value > self.extrema[1]:
			if value < self.extrema[0]:
				value = self.extrema[0]
			elif value > self.extrema[1]:
				value = self.extrema[1]
			eventobject.SetValue('%g' % value)
		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		extremarange = self.extrema[1] - self.extrema[0]
		sliderscale = float(slidermax-slidermin)/extremarange
		if eventobject is self.minentry:
			self.valuerange = (value, self.valuerange[1])
			self.minslider.SetValue(
				int(round((value - self.extrema[0])*sliderscale + slidermin)))
		elif eventobject is self.maxentry:
			self.valuerange = (self.valuerange[0], value)
			self.maxslider.SetValue(
				int(round((value - self.extrema[0])*sliderscale + slidermin)))

		evt = Events.ScaleValuesEvent(self, self.valuerange)
		self.GetEventHandler().AddPendingEvent(evt)

	def onKillFocus(self, evt):
		eventobject = evt.GetEventObject()
		string = eventobject.GetValue()
		self.onEntry(eventobject, string)
		evt.Skip()

	def onTextEnter(self, evt):
		eventobject = evt.GetEventObject()
		string = evt.GetString()
		self.onEntry(eventobject, string)
		evt.Skip()

	def onSize(self, evt):
		width, height = evt.GetSize()

		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		minvalue = self.minslider.GetValue()
		maxvalue = self.maxslider.GetValue()

		self.minslider.SetRange(0, width)
		self.maxslider.SetRange(0, width)

		try:
			scale = float(width)/(slidermax - slidermin)
		except ZeroDivisionError:
			minvalue = 0
			maxvalue = width
		else:
			minvalue = int(round((minvalue - slidermin)*scale))
			maxvalue = int(round((maxvalue - slidermin)*scale))

		self.minslider.SetValue(minvalue)
		self.maxslider.SetValue(maxvalue)
		evt.Skip()

	def onScroll(self, evt):
		eventobject = evt.GetEventObject()
		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		extremarange = self.extrema[1] - self.extrema[0]
		sliderscale = float(slidermax - slidermin)/extremarange
		position = evt.GetPosition()
		value = self.type((position - slidermin)/sliderscale + self.extrema[0])
		if eventobject is self.minslider:
			self.minentry.SetValue('%g' % value)
			self.valuerange = (value, self.valuerange[1])
		elif eventobject is self.maxslider:
			self.maxentry.SetValue('%g' % value)
			self.valuerange = (self.valuerange[0], value)

		evt.Skip()

		evt = Events.ScaleValuesEvent(self, self.valuerange)
		self.GetEventHandler().AddPendingEvent(evt)

if __name__ == '__main__':
	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = ValueScaler(frame, -1)
			self.panel = SizeScaler(frame, -1)

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)
	foo = getValueScaleBitmap((10, 1000.0), 256, 32)
	app.MainLoop()

