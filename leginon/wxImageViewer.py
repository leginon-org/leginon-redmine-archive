#!/usr/bin/env python

import cStringIO
import Mrc
import math
import Numeric
from wxPython.wx import *
from wxPython.lib.buttons import wxGenBitmapToggleButton
from NumericImage import NumericImage

wxInitAllImageHandlers()

class ImageTool(object):
	def __init__(self, imagepanel, sizer, bitmap, tooltip='', cursor=None,
								untoggle=False):
		self.sizer = sizer
		self.imagepanel = imagepanel
		self.cursor = cursor
		self.button = wxGenBitmapToggleButton(self.imagepanel, -1, bitmap,
                                          size=(24, 24))
		self.untoggle = untoggle
		self.button.SetBezelWidth(1)
		if tooltip:
			self.button.SetToolTip(wxToolTip(tooltip))
		self.sizer.Add(self.button, 0, wxALL, 3)
		EVT_BUTTON(self.imagepanel, self.button.GetId(), self.OnButton)

	def OnButton(self, evt):
		if self.button.GetToggle():
			if self.untoggle:
				self.untoggle = False
				self.imagepanel.UntoggleTools()
				self.untoggle = True
			if self.cursor is not None:
				self.imagepanel.panel.SetCursor(self.cursor)
			self.OnToggle(True)
		else:
			self.imagepanel.panel.SetCursor(self.imagepanel.defaultcursor)
			self.OnToggle(False)

	def OnToggle(self, value):
		pass

	def getToolBitmap(self, filename):
		wximage = wxImage('icons/' + filename)
		bitmap = wxBitmapFromImage(wximage)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		return bitmap

	def OnLeftClick(self, evt):
		pass

	def OnRightClick(self, evt):
		pass

	def OnLeftDoubleClick(self, evt):
		pass

	def OnRightDoubleClick(self, evt):
		pass

	def OnMotion(self, evt, dc):
		pass

	def getToolTipString(self, x, y, value):
		return ''

class ValueTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('valuetool.bmp')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(True)

	def valueString(self, x, y, value):
		return '(%d, %d) %s' % (x, y, str(value))

	def getToolTipString(self, x, y, value):
		if self.button.GetToggle():
			return self.valueString(x, y, value)
		else:
			return ''

class RulerTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('rulertool.bmp')
		tooltip = 'Toggle Ruler Tool'
		cursor = wxCROSS_CURSOR
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.start = None

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.start = self.imagepanel.view2image((evt.m_x, evt.m_y))

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			self.imagepanel.UpdateDrawing()

	def OnToggle(self, value):
		if not value:
			self.start = None

	def DrawRuler(self, dc, x, y):
		dc.SetPen(wxPen(wxRED, 1))
		x0, y0 = self.imagepanel.image2view(self.start)
		x0 -= self.imagepanel.offset[0]
		y0 -= self.imagepanel.offset[1]
		dc.DrawLine(x0, y0, x, y)

	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x = evt.m_x - self.imagepanel.offset[0]
			y = evt.m_y - self.imagepanel.offset[1]
			self.DrawRuler(dc, x, y)

	def getToolTipString(self, x, y, value):
		if self.button.GetToggle() and self.start is not None:
			x0, y0 = self.start
			return 'From (%d, %d) x=%d y=%d %.2f' % (x0, y0, x - x0, y - y0,
																								math.sqrt((x-x0)**2+(y-y0)**2))
		else:
			return ''

class ZoomTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('zoomtool.bmp')
		tooltip = 'Toggle Zoom Tool'
		cursor = wxStockCursor(wxCURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.label = wxStaticText(self.imagepanel, -1, '')
		self.updateLabel()
		self.sizer.Add(self.label, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.zoomIn(evt.m_x, evt.m_y)

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.zoomOut(evt.m_x, evt.m_y)

	def updateLabel(self):
		xscale, yscale = self.imagepanel.getScale()
		self.label.SetLabel('Zoom: ' + str(xscale) + 'x')
		width, height = self.label.GetSizeTuple()
		self.sizer.SetItemMinSize(self.label, width, height)
		self.sizer.Layout()

	def zoomIn(self, x, y):
		xscale, yscale = self.imagepanel.getScale()
		center = self.imagepanel.view2image((x, y))
		self.imagepanel.setScale((xscale*2, yscale*2))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()
		self.updateLabel()

	def zoomOut(self, x, y):
		xscale, yscale = self.imagepanel.getScale()
		center = self.imagepanel.view2image((x, y))
		self.imagepanel.setScale((xscale/2, yscale/2))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()
		self.updateLabel()

class ImagePanel(wxPanel):
	def __init__(self, parent, id, imagesize=(512, 512)):
		self.numericimage = None
		self.bitmap = None
		self.buffer = None
		self.imagesize = imagesize
		self.scale = (1.0, 1.0)
		self.offset = (0, 0)

		wxPanel.__init__(self, parent, id)

		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetAutoLayout(true)
		self.SetSizer(self.sizer)

		self.toolsizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.toolsizer)
		self.tools = []

		height, width = self.imagesize
		self.initPanel()


		EVT_LEFT_UP(self.panel, self.OnLeftUp)
		EVT_RIGHT_UP(self.panel, self.OnRightUp)
		EVT_LEFT_DCLICK(self.panel, self.OnLeftDoubleClick)
		EVT_RIGHT_DCLICK(self.panel, self.OnRightDoubleClick)
		EVT_PAINT(self.panel, self.OnPaint)
		EVT_SIZE(self.panel, self.OnSize)
		EVT_MOTION(self.panel, self.OnMotion)
		EVT_LEAVE_WINDOW(self.panel, self.OnLeave)

		self.addTool(ValueTool(self, self.toolsizer))
		self.addTool(RulerTool(self, self.toolsizer))
		self.addTool(ZoomTool(self, self.toolsizer))

		self.Fit()

	def addTool(self, tool):
		self.tools.append(tool)

	def initPanel(self):
		self.panel = wxScrolledWindow(self, -1, size=self.imagesize)
		self.panel.SetScrollRate(1,1)
		self.defaultcursor = wxCROSS_CURSOR
		self.panel.SetCursor(self.defaultcursor)
		self.sizer.Add(self.panel)
		width, height = self.panel.GetSizeTuple()
		self.sizer.SetItemMinSize(self.panel, width, height)

	# image set functions

	def setBitmap(self):
		if self.numericimage is None:
			self.bitmap = None
			return

		image = NumericImage(self.numericimage)
		image.update_image()
		wximage = image.wxImage()

		if self.smallScale():
			xscale, yscale = self.getScale()
			width, height = wximage.GetWidth()*xscale, wximage.GetHeight()*yscale
			self.bitmap = wxBitmapFromImage(wximage.Scale(width, height))
		else:
			self.bitmap = wxBitmapFromImage(wximage)

	def setBuffers(self):
		if self.bitmap is None:
			self.buffer = None
		else:
			bitmapwidth = self.bitmap.GetWidth()
			bitmapheight = self.bitmap.GetHeight()
			clientwidth, clientheight = self.panel.GetClientSize()

			if bitmapwidth < clientwidth:
				width = bitmapwidth
			else:
				width = clientwidth

			if bitmapheight < clientheight:
				height = bitmapheight
			else:
				height = clientheight

			self.buffer = wxEmptyBitmap(width, height)

	def setVirtualSize(self):
		if self.bitmap is not None:
			width, height = self.bitmap.GetWidth(), self.bitmap.GetHeight()
			if self.smallScale():
				virtualsize = (width - 1, height - 1)
			else:
				xscale, yscale = self.getScale()
				virtualsize = ((width - 1) * xscale, (height - 1) * yscale)
			self.panel.SetVirtualSize(virtualsize)
		else:
			self.panel.SetVirtualSize((0, 0))

		if self.biggerView():
			xsize, ysize = self.panel.GetVirtualSize()
			xclientsize, yclientsize = self.panel.GetClientSize()
			self.offset = ((xclientsize - xsize)/2, (yclientsize - ysize)/2)
		else:
			self.offset = (0, 0)

	def setNumericImage(self, numericimage, scroll=False):
		self.numericimage = numericimage
		self.setBitmap()
		self.setBuffers()
		self.setVirtualSize()
		if not scroll:
			self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	def clearImage(self):
		self.setNumericImage(None)

	def setImageFromMrcString(self, imagestring, scroll=False):
		self.setNumericImage(Mrc.mrcstr_to_numeric(imagestring), scroll)

	# scaling functions

	def getScale(self):
		return self.scale

	def smallScale(self, scale=None):
		if scale is None:
			scale = self.getScale()
		if scale[0] < 1.0 or scale[1] < 1.0:
			return True
		else:
			return False

	def setScale(self, scale):
		for n in scale:
			# from one test
			if n > 128.0 or n < 0.002:
				return
		oldscale = self.getScale()
		self.scale = scale
		if self.smallScale() or self.smallScale(oldscale):
			self.setBitmap()
			self.setBuffers()

		self.setVirtualSize()
		if self.biggerView():
			self.panel.Refresh()
		#self.UpdateDrawing()

	# utility functions

	def getValue(self, x, y):
		try:
			return self.numericimage[y, x]
		except (IndexError, AttributeError), e:
			return None

	def getClientCenter(self):
		center = self.panel.GetClientSize()
		return (center[0]/2, center[1]/2)

	def biggerView(self):
		size = self.panel.GetVirtualSize()
		clientsize = self.panel.GetClientSize()
		if size[0] < clientsize[0] or size[1] < clientsize[1]:
			return True
		else:
			return False

	def center(self, center):
		x, y = center
		xcenter, ycenter = self.getClientCenter()
		xscale, yscale = self.getScale()
		self.panel.Scroll(x * xscale - xcenter, y * yscale - ycenter)

	def view2image(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round((viewoffset[0] + xy[0] - xoffset) / scale[0])),
						int(round((viewoffset[1] + xy[1] - yoffset) / scale[1])))

	def image2view(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round(((xy[0]) * scale[0]) - viewoffset[0] + xoffset)),
						int(round(((xy[1]) * scale[1]) - viewoffset[1] + yoffset)))

	# tool utility functions

	def UntoggleTools(self):
		for tool in self.tools:
			if tool.untoggle:
				tool.button.SetToggle(False)

	# eventhandlers

	def OnMotion(self, evt):
		if self.buffer is None:
			return

		if self.smallScale():
			xoffset, yoffset = self.offset
			width, height = self.panel.GetVirtualSize()
			if evt.m_x < xoffset or evt.m_x > xoffset + width: 
				self.UpdateDrawing()
				return
			if evt.m_y < yoffset or evt.m_y > yoffset + height: 
				self.UpdateDrawing()
				return

		dc = wxMemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()

		self.Draw(dc)


		for tool in self.tools:
			tool.OnMotion(evt, dc)

		strings = []
		x, y = self.view2image((evt.m_x, evt.m_y))
		value = self.getValue(x, y)

		for tool in self.tools:
			string = tool.getToolTipString(x, y, value)
			if string:
				strings.append(string)
		if strings:
			self.drawToolTip(dc, x, y, strings)

		dc.EndDrawing()

		self.paint(dc, wxClientDC(self.panel))
		dc.SelectObject(wxNullBitmap)

	def OnLeftUp(self, evt):
		for tool in self.tools:
			tool.OnLeftClick(evt)

	def OnRightUp(self, evt):
		for tool in self.tools:
			tool.OnRightClick(evt)

	def OnLeftDoubleClick(self, evt):
		for tool in self.tools:
			tool.OnLeftDoubleClick(evt)

	def OnRightDoubleClick(self, evt):
		for tool in self.tools:
			tool.OnRightDoubleClick(evt)

	def drawToolTip(self, dc, x, y, strings):
		dc.SetBrush(wxBrush(wxColour(255, 255, 220)))
		dc.SetPen(wxPen(wxBLACK, 1))

		xextent = 0
		yextent = 0
		for string in strings:
			width, height, d, e = dc.GetFullTextExtent(string, wxNORMAL_FONT)
			if width > xextent:
				xextent = width
			yextent += height

		xcenter, ycenter = self.getClientCenter()

		ix, iy = self.image2view((x, y))

		if ix <= xcenter:
			xoffset = 10
		else:
			xoffset = -(10 + xextent + 4)
		if iy <= ycenter:
			yoffset = 10
		else:
			yoffset = -(10 + yextent + 4)

		ix -= self.offset[0]
		iy -= self.offset[1]

		x = int(round((ix + xoffset)))
		y = int(round((iy + yoffset)))

		dc.DrawRectangle(x, y, xextent + 4, yextent + 4)

		dc.SetFont(wxNORMAL_FONT)
		for string in strings:
			dc.DrawText(string, x + 2 , y + 2)
			width, height, d, e = dc.GetFullTextExtent(string, wxNORMAL_FONT)
			y += height

	def Draw(self, dc):
		dc.BeginDrawing()
		if self.bitmap is None:
			dc.Clear()
		else:
			bitmapdc = wxMemoryDC()
			bitmapdc.SelectObject(self.bitmap)

			if self.smallScale():
				xscale, yscale = (1.0, 1.0)
			else:
				xscale, yscale = self.getScale()
				#bitmapdc.SetUserScale(1.0/xscale, 1.0/yscale)
				dc.SetUserScale(xscale, yscale)

			xviewoffset, yviewoffset = self.panel.GetViewStart()
			xsize, ysize = self.panel.GetClientSize()

			#dc.Blit(0, 0, xsize, ysize, bitmapdc, xviewoffset, yviewoffset)
			dc.Blit(0, 0, xsize/xscale + yscale, ysize/yscale + yscale, bitmapdc,
							xviewoffset/xscale, yviewoffset/xscale)
			bitmapdc.SelectObject(wxNullBitmap)
		dc.EndDrawing()
		dc.SetUserScale(1.0, 1.0)

	def paint(self, fromdc, todc):
		xsize, ysize = self.panel.GetClientSize()
		xoffset, yoffset = self.offset
		todc.Blit(xoffset, yoffset, xsize + 1, ysize + 1, fromdc, 0, 0)

	def UpdateDrawing(self):
		if self.buffer is None:
			self.panel.Refresh()
		else:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wxClientDC(self.panel))
			dc.SelectObject(wxNullBitmap)

	def OnSize(self, evt):
		self.UpdateDrawing()

	def OnPaint(self, evt):
		if self.buffer is None:
			evt.Skip()
		else:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wxPaintDC(self.panel))
			dc.SelectObject(wxNullBitmap)

#			dc = wxPaintDC(self.panel)
#			xoffset, yoffset = self.offset
#			dc.DrawBitmap(self.buffer, xoffset, yoffset)

	def OnLeave(self, evt):
		self.UpdateDrawing()

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = self.getToolBitmap('arrowtool.bmp')
		tooltip = 'Click Tool'
		cursor = wxStockCursor(wxCURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.callback = callback

	def OnLeftDoubleClick(self, evt):
		if self.button.GetToggle():
			xy = self.imagepanel.view2image((evt.m_x, evt.m_y))
			if callable(self.callback):
				self.callback(xy)

class ClickImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		ImagePanel.__init__(self, parent, id)
		self.addTool(ClickTool(self, self.toolsizer, callback))

class TargetTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = self.getToolBitmap('targettool.bmp')
		tooltip = 'Toggle Target Tool'
		cursor = wxStockCursor(wxCURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.callback = callback
		self.target_type = None
		self.combobox = None

	def getTargetType(self):
		return self.target_type

	def setTargetType(self, name):
		self.target_type = name
		self.setTargetButtonBitmap()

	def addTargetType(self, name):
		if self.getTargetType is None:
			self.setTargetType(name)
		self.addComboBox(name)

	def deleteTargetType(self, name):
		self.deleteComboBox(name)

	def OnToggle(self, value):
		if not value:
			self.imagepanel.closest_target = None
			self.imagepanel.UpdateDrawing()

	def setTargetButtonBitmap(self):
		bitmap = wxEmptyBitmap(16, 16)
		dc = wxMemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		color = self.imagepanel.target_types[self.target_type].getColor()
		dc.SetPen(wxPen(color, 2))
		dc.DrawLine(8, 0, 8, 15)
		dc.DrawLine(0, 8, 15, 8)
		dc.EndDrawing()
		dc.SelectObject(wxNullBitmap)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		self.button.SetBitmapLabel(bitmap)
		self.button.Refresh()

	def OnComboBoxSelect(self, evt):
		self.setTargetType(evt.GetString())

	def addComboBox(self, name):
		if self.combobox is None:
			if len(self.imagepanel.target_types) > 1:
				self.combobox = wxComboBox(self.imagepanel, -1, value=self.target_type,
																		choices=self.imagepanel.target_types.keys(),
																		style=wxCB_DROPDOWN|wxCB_READONLY|wxCB_SORT)
				EVT_COMBOBOX(self.imagepanel, self.combobox.GetId(),
											self.OnComboBoxSelect)
				self.sizer.Add(self.combobox, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)
				self.sizer.Layout()
			elif len(self.imagepanel.target_types) == 1:
				self.target_type = name
				self.sizer.Layout()
		else:
			self.combobox.Append(name)
			self.combobox.SetSize(self.combobox.GetBestSize())
			width, height = self.combobox.GetSizeTuple()
			self.sizer.SetItemMinSize(self.combobox, width, height)
			self.sizer.Layout()

	def deleteComboBox(self, name):
		if self.combobox is None:
			if len(self.imagepanel.targets) > 2:
				self.combobox.Delete(self.combobox.FindString(name))
			elif len(self.imagepanel.targets) == 2:
				self.sizer.Remove(self.combobox)
				self.sizer.Layout()
				self.target_type = self.imagepanel.targets.keys()[0]
			else:
				EVT_BUTTON(self.imagepanel, self.button.GetId(), None)
				self.sizer.Remove(self.button)
				self.sizer.Layout()
				self.target_type = None

	def OnLeftClick(self, evt):
		if self.button.GetToggle() and self.target_type is not None:
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			target = self.imagepanel.addTarget(self.target_type, x, y)
			if callable(self.callback):
				name = target.target_type.getName()
				targets = self.imagepanel.getTargetTypeValue(name)
				self.callback(target.target_type.getName(), targets)

	def OnRightClick(self, evt):
		selectedtarget = self.imagepanel.getSelectedTarget()
		if self.button.GetToggle() and selectedtarget is not None:
			target_type, value = self.imagepanel.deleteTarget(selectedtarget)
			if callable(self.callback):
				self.callback(target_type, value)

	def closestTarget(self, x, y):
		minimum_magnitude = 10

		if self.imagepanel.smallScale():
			xscale, yscale = self.imagepanel.getScale()
			minimum_magnitude /= xscale

		closest_target = None
		for target in self.imagepanel.getTargets():
			tx, ty = target.getPosition()
			magnitude = math.sqrt((x - tx)**2 + (y - ty)**2)
			if magnitude < minimum_magnitude:
				minimum_magnitude = magnitude
				closest_target = target

		return closest_target

	def OnMotion(self, evt, dc):
		if self.button.GetToggle():
			viewoffset = self.imagepanel.panel.GetViewStart()
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			self.imagepanel.setSelectedTarget(self.closestTarget(x, y))

	def getToolTipString(self, x, y, value):
		selectedtarget = self.imagepanel.getSelectedTarget()
		if selectedtarget is not None:
			name = selectedtarget.target_type.getName()
			position = selectedtarget.getPosition()
			return name + ' ' + str(position)
		else:
			return ''

class Target(object):
	def __init__(self, x, y, target_type=None):
		self.setPosition(x, y)
		self.target_type = target_type

	def getPosition(self):
		return self.x, self.y

	def setPosition(self, x, y):
		self.x = x
		self.y = y

	def getTargetType(self):
		return self.target_type

	def setTargetType(self, target_type):
		self.target_type = target_type

class TargetType(object):
	def __init__(self, name, color):
		self.targets = []
		self.bitmaps = {}
		self.setName(name)
		self.setColor(color)

	def getTargets(self):
		return self.targets

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getColor(self):
		return self.color

	def setColor(self, color):
		self.color = color
		self.setBitmaps(self.color)

	def addTarget(self, target):
		if target in self.targets:
			raise ValueError('cannot add target, target already exists')
		if target.target_type != self:
			if target.target_type is not None:
				target.target_type.removeTarget(target)
			target.setTargetType(self)
			self.targets.append(target)

	def removeTarget(self, target):
		if target not in self.targets:
			raise ValueError('cannot remove target, no such target')
		target.setTargetType(None)
		self.targets.remove(target)

	def clearTargets(self):
		for target in self.targets:
			target.setTargetType(None)
		self.targets = []

	def getTargetPositions(self):
		targetpositions = []
		for target in self.targets:
			targetpositions.append(target.getPosition())
		return targetpositions

	def getBitmap(self, name):
		try:
			return self.bitmaps[name]
		except KeyError:
			raise ValueError('no such bitmap')

	def getDefaultBitmap(self):
		return self.getBitmap('default')

	def getSelectedBitmap(self):
		return self.getBitmap('selected')

	def makeBitmap(self, color):
		penwidth = 1
		length = 15
		bitmap = wxEmptyBitmap(length, length)
		dc = wxMemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		dc.SetBrush(wxBrush(color, wxTRANSPARENT))
		dc.SetPen(wxPen(color, penwidth))
		dc.DrawLine(length/2, 0, length/2, length)
		dc.DrawLine(0, length/2, length, length/2)
		dc.EndDrawing()
		dc.SelectObject(wxNullBitmap)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		return bitmap

	def setBitmaps(self, color):
		default = self.makeBitmap(color)
		self.bitmaps['default'] = default

		selectedcolor = wxColor(color.Red()/2, color.Green()/2, color.Blue()/2)
		selected = self.makeBitmap(selectedcolor)
		self.bitmaps['selected'] = selected

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		ImagePanel.__init__(self, parent, id)
		self.target_types = {}
		self.selectedtarget = None
		self.colorlist = [wxRED, wxBLUE, wxColor(255, 0, 255), wxColor(0, 255, 255)]
		self.addTool(TargetTool(self, self.toolsizer, callback))

	def addTargetTypeColor(self, color):
		self.colorlist.append(color)

	def removeTargetTypeColor(self):
		try:
			color = self.colorlist[0]
			del self.colorlist[0]
		except IndexError:
			raise RuntimeError('Not enough colors for addition target types')
		return color

	def addTargetType(self, name):
		if name in self.target_types:
			raise ValueError('Target type already exists')
		color = self.removeTargetTypeColor()
		self.target_types[name] = TargetType(name, color)

		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.addTargetType(name)

	def deleteTargetType(self, name):
		try:
			target_type = self.target_types[name]
		except KeyError:
			raise ValueError('No such target type')
		color = target_type.color
		del self.target_types[name]
		self.addTargetTypeColor(color)

		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.deleteTargetType(name)

	# compat function
	def getTargetTypeValue(self, name):
		try:
			return self.target_types[name].getTargetPositions()
		except KeyError:
			raise ValueError('No such target type')

	# compat function
	def setTargetTypeValue(self, name, value):
		if name not in self.target_types:
			self.addTargetType(name)
		else:
			self.target_types[name].clearTargets()
		for position in value:
			x, y = position
			self.addTarget(name, x, y)

		self.UpdateDrawing()

	def addTarget(self, name, x, y):
		if name not in self.target_types:
			raise ValueError('No such target type to add target')
		target = Target(x, y)
		self.target_types[name].addTarget(target)
		self.UpdateDrawing()
		return target

	def deleteTarget(self, target):
		target_type = target.target_type
		if target_type in self.target_types.values():
			target_type.removeTarget(target)
		else:
			raise ValueError('Target\'s target type does not exist')
		if self.getSelectedTarget() == target:
			self.setSelectedTarget(None)
		self.UpdateDrawing()

		return target_type.getName(), target_type.getTargetPositions()

	def clearTargets(self):
		for target_type in self.target_types.values():
			target_type.clearTargets()
		self.UpdateDrawing()

	def getTargets(self):
		targetlist = []
		for target_type in self.target_types.values():
			targetlist += target_type.getTargets()
		return targetlist

	def getSelectedTarget(self):
		return self.selectedtarget

	def setSelectedTarget(self, target):
		if target is not None:
			if target not in self.getTargets():
				raise ValueError('no such target')
		self.selectedtarget = target

	def getTargetBitmap(self, target):
		for target_type in self.targets:
			if target in self.targets[target_type]:
				# temp
				for tool in self.tools:
					if hasattr(tool, 'closest_target'):
						if target == tool.closest_target:
							return self.targetbitmaps[target_type]['selected']
				return self.targetbitmaps[target_type]['default']

	def drawTarget(self, dc, target):
		if target_type not in self.target_types.values():
			return

		if target == self.getSelectedTarget():
			bitmap = target.target_type.getSelectedBitmap()
		else:
			bitmap = target.target_type.getDefaultBitmap()

		memorydc = wxMemoryDC()
		memorydc.SelectObject(bitmap)
		width = bitmap.GetWidth()
		height = bitmap.GetHeight()

		xscale, yscale = self.getScale()
		position = target.getPosition()
		if self.biggerView():
			x, y = position
			x *= xscale
			y *= yscale
		else:
			x, y = self.image2view(position)

		if not self.smallScale():
			memorydc.SetUserScale(1.0/xscale, 1.0/yscale)
			width *= xscale
			height *= yscale

		dc.Blit(x - width/2, y - height/2, width, height,
						memorydc, 0, 0, wxCOPY, True)

		memorydc.SelectObject(wxNullBitmap)

	def drawTargets(self, dc):
		xscale, yscale = self.getScale()
		memorydc = wxMemoryDC()

		for target in self.getTargets():

			if target == self.getSelectedTarget():
				bitmap = target.target_type.getSelectedBitmap()
			else:
				bitmap = target.target_type.getDefaultBitmap()

			position = target.getPosition()
			if self.biggerView():
				x, y = position
				x *= xscale
				y *= yscale
			else:
				x, y = self.image2view(position)

			memorydc.Clear()
			memorydc.SelectObject(bitmap)
			width = bitmap.GetWidth()
			height = bitmap.GetHeight()

			if not self.smallScale():
				memorydc.SetUserScale(1.0/xscale, 1.0/yscale)
				width *= xscale
				height *= yscale

			dc.Blit(x - width/2, y - height/2,
							width, height, memorydc, 0, 0, wxCOPY, True)

			memorydc.SelectObject(wxNullBitmap)

	def Draw(self, dc):
		ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		self.drawTargets(dc)
		dc.EndDrawing()

if __name__ == '__main__':
	def bar(xy):
		print xy

	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = TargetImagePanel(frame, -1)
#			self.panel = ClickImagePanel(frame, -1, bar)
			self.panel.addTargetType('foo')
			self.panel.addTargetType('bar')
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.panel.setImageFromMrcString(open('test2.mrc', 'rb').read())
	app.MainLoop()

