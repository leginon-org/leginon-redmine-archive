import navigator
import data
import event
import math
import node

class MosaicNavigator(navigator.Navigator):
	def __init__(self, id, nodelocations, **kwargs):
		self.statemosaic = {}
		navigator.Navigator.__init__(self, id, nodelocations, **kwargs)
		self.addEventInput(event.StateMosaicPublishEvent, self.addStateMosaic)
		self.defineUserInterface()
		self.start()

	def addStateMosaic(self, ievent):
		idata = self.researchByDataID(ievent.content)
		imagedataid = idata.content['image data ID']
		statemosaicdata = idata.content
		del statemosaicdata['image data ID']
		self.statemosaic[imagedataid] = statemosaicdata

	def handleImageClick(self, clickevent):
		imagedataid = clickevent.content['image id']
		try:
			mosaicdata = self.statemosaic[imagedataid]
		except:
			self.printerror('unknown image data ID for navigation')
			return

		row = clickevent.content['array row']
		column = clickevent.content['array column']
		shape = clickevent.content['array shape']

		# certainly not optimal
		maxmagnitude = math.sqrt(shape[0]**2 + shape[1]**2)
		nearestdelta = (0,0)
		nearesttile = None
		for tile in mosaicdata:
			position = mosaicdata[tile]['position']
			deltaposition = ((position[0] - row), (position[1] - column))
			magnitude = math.sqrt((deltaposition[0])**2 + (deltaposition[1])**2)
			if magnitude < maxmagnitude:
				maxmagnitude = magnitude
				nearestdelta = deltaposition
				nearesttile = tile

		self.publishRemote(data.EMData('all', mosaicdata[nearesttile]['state']))
		e = self.shiftEventClass(self.ID(),
									{'row': nearestdelta[0], 'column': nearestdelta[1]})
		self.output(e)

		time.sleep(self.delaydata.get())

		# hmm?
		self.acquireImage()

if __name__ == '__main__':
	foo = MosaicNavigator(('fake id',), [])
	foo.addStateMosaic(data.StateMosaicData(('data', 0),
				{'image data ID': ('image', 0),
				('tile', 0): {'position': (0, 0), 'state': 'state 0'},
				('tile', 1): {'position': (5, 5), 'state': 'state 1'},
				('tile', 2): {'position': (10, 10), 'state': 'state 2'},
				('tile', 3): {'position': (15, 15), 'state': 'state 3'}}))

	foo.handleImageClick(event.ImageClickEvent(('event', 0),
		{'image id': ('image', 0),
		'array row': 5,
		'array column': 5,
		'array shape': (256, 256)}))

	print foo.statemosaic

