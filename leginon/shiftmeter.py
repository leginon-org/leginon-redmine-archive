#!/usr/bin/env python

import watcher
import correlator, fftengine, peakfinder
import data, event
from mrc.Mrc import mrc_to_numeric
from Tkinter import *
from viewer.ImageViewer import ImageViewer
import threading

class ShiftMeter(watcher.Watcher):
	'''
	This node watches for published images.  It inserts images into
	its buffer, which can hold two images.  The shift between the two
	images in the buffer is measured after every insert.
	'''
	def __init__(self, id, managerlocation):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, managerlocation, watchfor, lockblocking)
		ffteng = fftengine.fftFFTW(planshapes=(),estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()
		self.shift = ()

		#t = threading.Thread(target=self.initViewers)
		#t.setDaemon(1)
		#t.start()

	def processData(self, newdata):
		## phase correlation with new image
		newimage = newdata.content
		self.correlator.insertImage(newimage)
		try:
			pcim = self.correlator.phaseCorrelate()
		except correlator.MissingImageError:
			print 'missing image, no correlation'
			return

		## find peak in correlation image
		peak = self.peakfinder.subpixelPeak(npix=3,newimage=pcim)
		print 'peak', peak
		## interpret as a shift
		shift = correlator.wrap_coord(peak, pcim.shape)
		print 'shift', shift
		self.shift = shift

		pcid = self.ID()
		pcdata = data.PhaseCorrelationImageData(pcid, pcim)
		self.publish(pcdata, eventclass=event.PhaseCorrelationImagePublishEvent)
		corrinfo = {}
		corrinfo['phase correlation image'] = pcid
		corrinfo['phase correlation shift'] = shift
		corrdata = data.CorrelationData(self.ID(), corrinfo)
		self.publish(corrdata, eventclass=event.CorrelationPublishEvent)

	def process_numeric(self, numarray, filename):
		'''mainly for debugging'''
		class fakedata: pass
		fakedata.content = numarray
		fakedata.id = (filename,)
		print 'processing data'
		self.processData(fakedata)

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)
		argspec = (
			{'name':'filename', 'alias':'Filename', 'type':'string'},
			)
		self.registerUIFunction(self.uiLoadImage, argspec, 'Load')
		self.registerUIFunction(self.uiClearBuffer, (), 'Clear Buffer')
		self.registerUIFunction(self.uiGetResult, (), 'Get Result', returntype='array')

	def uiLoadImage(self, filename):
		print 'reading %s' % filename
		newimage = mrc_to_numeric(filename)
		print 'image read'
		self.process_numeric(newimage, filename)
		return 'image loaded'

	def uiClearBuffer(self):
		self.correlator.clearBuffer()
		return ''

	def uiGetResult(self):
		print 'uiGetResult:', self.shift
		return self.shift

	def initViewers(self):
		ccwin = Toplevel()
		ccwin.wm_title('Cross Correlation')
		self.cciv = ImageViewer(ccwin)

		pcwin = Toplevel()
		pcwin.wm_title('Phase Correlation')
		self.pciv = ImageViewer(pcwin)

		self.cciv.pack()
		self.pciv.pack()
		ccwin.mainloop()

	def updateViewers(self, ccim, pcim):
		self.cciv.import_numeric(ccim)
		self.pciv.import_numeric(pcim)


if __name__ == '__main__':
	from Tkinter import *
	import nodegui

	s = ShiftMeter(('none',), None)

	host = s.location()['hostname']
	uiport = s.location()['UI port']
	
	tk = Tk()
	sgui = nodegui.NodeGUI(tk, hostname=host, port=uiport)
	sgui.pack()
	tk.mainloop()
