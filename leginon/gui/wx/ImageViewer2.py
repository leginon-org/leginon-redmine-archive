import math
import numextension
import wx

def getColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	return zip(r, g, b)

colormap = getColorMap()

def wxBitmapFromNumarray(n, min=None, max=None, color=False):
	if min is None or max is None:
		min, max = numextension.minmax(n)
	wximage = wx.EmptyImage(n.shape[1], n.shape[0])
	if color:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max), colormap))
	else:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max)))
	return wx.BitmapFromImage(wximage)

class BufferedWindow(wx.ScrolledWindow):
	def __init__(self, parent, id):
		wx.ScrolledWindow.__init__(self, parent, id)

		self.onSize(None)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)

	def onEraseBackground(self, evt):
		pass

	def _updateDrawing(self, dc):
		pass

	def updateDrawing(self):
		dc = wx.MemoryDC()
		dc.SelectObject(self._buffer)
		self._updateDrawing(dc)
		dc.SelectObject(wx.NullBitmap)

	def _onPaintRegion(self, dc, x, y, width, height, memorydc):
		dc.Blit(x, y, width, height, memorydc, x, y)

	def _onPaint(self, dc):
		memorydc = wx.MemoryDC()
		memorydc.SelectObject(self._buffer)
		regioniterator = wx.RegionIterator(self.GetUpdateRegion())
		while(regioniterator):
			rect = regioniterator.GetRect()
			self._onPaintRegion(dc, rect.x, rect.y, rect.width, rect.height, memorydc)
			regioniterator.Next()
		memorydc.SelectObject(wx.NullBitmap)

	def onPaint(self, evt):
		dc = wx.PaintDC(self) 
		dc.SetDeviceOrigin(0, 0)
		self._onPaint(dc)

	def _onSize(self, evt):
		self._clientwidth, self._clientheight = self.GetClientSizeTuple() 
		# TODO: set buffer size in steps
		self._buffer = wx.EmptyBitmap(self._clientwidth, self._clientheight) 

	def onSize(self, evt):
		self._onSize(evt)
		self.updateDrawing()
		if evt is not None:
			evt.Skip()

class BitmapWindow(BufferedWindow):
	def __init__(self, parent, id):
		self._xoffset = 0
		self._yoffset = 0
		self._xoffsetscaled = 0
		self._yoffsetscaled = 0
		self._xscale = 1.0
		self._yscale = 1.0
		self._xview = 0
		self._yview = 0
		self._bitmap = None
		BufferedWindow.__init__(self, parent, id)

	def _setBitmap(self, bitmap):
		self._bitmap = bitmap
		if bitmap is None:
			self._bitmapwidth = 0
			self._bitmapheight = 0
		else:
			self._bitmapwidth = self._bitmap.GetWidth()
			self._bitmapheight = self._bitmap.GetHeight()

	def setBitmap(self, bitmap):
		self._setBitmap(bitmap)
		self.updateDrawing()
		self.Refresh()

	def _updateDrawing(self, dc):
		BufferedWindow._updateDrawing(self, dc)

		# TODO: _draw smarter
		dc.Clear()

		if self._bitmap is None:
			return

		dc.SetUserScale(self._xscale, self._yscale)

		memorydc = wx.MemoryDC()
		memorydc.SelectObject(self._bitmap)
		if wx.Platform == '__WXGTK__':
			dc.DestroyClippingRegion()
			dc.SetClippingRegion(0, 0,
														self._clientwidthscaled, self._clientheightscaled)
			xoffset = self._xoffsetscaled
			if self._xview > 0:
				xoffset -= self._xview
			yoffset = self._yoffsetscaled
			if self._yview > 0:
				yoffset -= self._yview
			dc.Blit(xoffset, yoffset,
							self._bitmapwidth, self._bitmapheight,
							memorydc,
							0, 0)
		else:
			dc.Blit(self._xoffsetscaled, self._yoffsetscaled,
							self._clientwidthscaled, self._clientheightscaled,
							memorydc,
							self._xview, self._yview)
		memorydc.SelectObject(wx.NullBitmap)

class ScaledWindow(BitmapWindow):
	def _setBitmap(self, bitmap):
		BitmapWindow._setBitmap(self, bitmap)
		self._bitmapwidthscaled = int(self._bitmapwidth*self._xscale)
		self._bitmapheightscaled = int(self._bitmapheight*self._yscale)

	def _setScale(self, x, y):
		updated = False
		if self._xscale != x:
			self._xscale = x
			self._clientwidthscaled = int(self._clientwidth/self._xscale + 1)
			if self._bitmap is not None:
				self._bitmapwidthscaled = int(self._bitmapwidth*self._xscale)
				updated = True

		if self._yscale != y:
			self._yscale = y
			self._clientheightscaled = int(self._clientheight/self._yscale + 1)
			if self._bitmap is not None:
				self._bitmapheightscaled = int(self._bitmapheight*self._yscale)
				updated = True

		return updated

	def setScale(self, x, y):
		self.Freeze()
		if self._setScale(x, y):
			self.updateDrawing()
			self.Refresh()

	def getScale(self):
		return (self._xscale, self._yscale)

	def _onSize(self, evt):
		BitmapWindow._onSize(self, evt)
		self._clientwidthscaled = int(self._clientwidth/self._xscale + 1)
		self._clientheightscaled = int(self._clientheight/self._yscale + 1)

class OffsetWindow(ScaledWindow):
	def updateOffset(self):
		updated = False
		if self._bitmap is None or self._bitmapwidthscaled >= self._clientwidth:
			xoffset = 0
		else:
			xoffset = int((self._clientwidth - self._bitmapwidthscaled)/2.0)
		if self._xoffset != xoffset:
			self._xoffset = xoffset
			self._xoffsetscaled = int(self._xoffset/self._xscale)
			updated = True
		if self._bitmap is None or self._bitmapheightscaled >= self._clientheight:
			yoffset = 0
		else:
			yoffset = int((self._clientheight - self._bitmapheightscaled)/2.0)
		if self._yoffset != yoffset:
			self._yoffset = yoffset
			self._yoffsetscaled = int(self._yoffset/self._yscale)
			updated = True
		return updated

	def _setBitmap(self, bitmap):
		ScaledWindow._setBitmap(self, bitmap)
		self.SetScrollbars(self._xscale, self._yscale,
												self._bitmapwidth, self._bitmapheight)
		self.updateOffset()
		self.Refresh()

	def _onSize(self, evt):
		ScaledWindow._onSize(self, evt)
		# GTK requests a paint of the full area on size
		if self.updateOffset() and wx.Platform != '__WXGTK__':
			self.Refresh()

	def _setScale(self, x, y, center=None):
		xview, yview = self.GetViewStart()
		if center is None:
			xcenter = xview + self._clientwidthscaled/2 - self._xoffsetscaled
			ycenter = yview + self._clientheightscaled/2 - self._yoffsetscaled
		else:
			xcenter = xview + int(center[0]/self._xscale) - self._xoffsetscaled
			ycenter = yview + int(center[1]/self._yscale) - self._yoffsetscaled
		if ScaledWindow._setScale(self, x, y):
			xposition = xcenter - self._clientwidthscaled/2
			yposition = ycenter - self._clientheightscaled/2
			self.SetScrollbars(self._xscale, self._yscale,
													self._bitmapwidth, self._bitmapheight,
													xposition, yposition)
			self.updateOffset()
			return True
		return False

	def setScale(self, x, y, center=None):
		if self._setScale(x, y, center):
			self.updateDrawing()
			self.Refresh()

	def _onPaint(self, dc):
		updated = False
		xview, yview = self.GetViewStart()
		if self._xview != xview:
			self._xview = xview
			updated = True
		if self._yview != yview:
			self._yview = yview
			updated = True
		if updated:
			self.updateDrawing()
			if wx.Platform != '__WXGTK__':
				# TODO: ScrolledWindow w/ update on buffer
				self.Refresh()
				return
		ScaledWindow._onPaint(self, dc)


if __name__ == '__main__':
	import sys
	import Mrc
	import numarray

	def wxBitmapFromMRC(filename, min=None, max=None, color=False):
		n = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
		return wxBitmapFromNumarray(n, min, max, color)

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = BufferedWindow(frame, -1)
			#self.panel = BitmapWindow(frame, -1)
			#self.panel = ScaledWindow(frame, -1)
			self.panel = OffsetWindow(frame, -1)

			self.panel.Bind(wx.EVT_LEFT_UP,
		lambda e: self.panel.setScale(*(tuple(map(lambda s: s*2.0, self.panel.getScale()))) + ((e.m_x, e.m_y),)))
			self.panel.Bind(wx.EVT_RIGHT_UP,
		lambda e: self.panel.setScale(*map(lambda s: s/2.0, self.panel.getScale())))

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		import numarray
		n = numarray.zeros((128, 128))
		for i in range(n.shape[0]):
			for j in range(n.shape[1]):
				n[i, j] = (i + j) * ((i + j) % 2)
		app.panel.setBitmap(wxBitmapFromNumarray(n))
	else:
		app.panel.setBitmap(wxBitmapFromMRC(filename, color=True))
	app.MainLoop()

