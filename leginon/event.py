## defines the Event and EventHandler classes

import leginonobject
import data

class Event(data.Data):
	def __init__(self, id, content=None):
		data.Data.__init__(self, id, content)


## Standard Event Types:
##
##	Event
##		NotificationEvent
##			NodeAvailableEvent
##				LauncherAvailableEvent
##			NodeUnavailableEvent
##			PublishEvent
##			UnpublishEvent
##			ListPublishEvent
##		ControlEvent
##			StartEvent
##			Stopvent
##			NumericControlEvent
##			LaunchEvent

### generated by a node to notify manager that node is ready
class NotificationEvent(Event):
	'Event sent by for notification'
	def __init__(self, id, content):
		Event.__init__(self, id, content)

class NodeAvailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is accessible'
	def __init__(self, id, nodelocation):
		NotificationEvent.__init__(self, id, content=nodelocation)

class LauncherAvailableEvent(NodeAvailableEvent):
	'Event sent by a launcher to the manager to indicate that it is accessible'
	def __init__(self, id, nodelocation):
		NodeAvailableEvent.__init__(self, id, nodelocation)

class NodeUnavailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is inaccessible'
	def __init__(self, id):
		NotificationEvent.__init__(self, id, content=None)

class PublishEvent(NotificationEvent):
	'Event indicating data was published'
	def __init__(self, id, dataid):
		NotificationEvent.__init__(self, id, content=dataid)

class UnpublishEvent(NotificationEvent):
	'Event indicating data was unpublished (deleted)'
	def __init__(self, id, dataid):
		NotificationEvent.__init__(self, id, content=dataid)

class PublishImageEvent(NotificationEvent):
	'Event indicating image was published'
	def __init__(self, id, dataid):
		NotificationEvent.__init__(self, id, content=dataid)

# this could be a subclass of publish event, but I'm not sure if that
# would confuse those not looking for a list
class ListPublishEvent(Event):
	'Event indicating data was published'
	def __init__(self, id, idlist):
		if type(idlist) == list:
			Event.__init__(self, id, content = idlist)
		else:
			raise TypeError

class ControlEvent(Event):
	'Event that passes a value with it'
	def __init__(self, id, content=None):
		Event.__init__(self, id, content)

class StartEvent(ControlEvent):
	'Event that signals a start'
	def __init__(self, id):
		ControlEvent.__init__(self, id)
	
class StopEvent(ControlEvent):
	'Event that signals a stop'
	def __init__(self, id):
		ControlEvent.__init__(self, id)

class NumericControlEvent(ControlEvent):
	'ControlEvent that allows only numeric values to be passed'
	def __init__(self, id, content):
		allowedtypes = (int, long, float)
		if type(content) in allowedtypes:
			ControlEvent.__init__(self, id, content)
		else:
			raise TypeError('NumericControlEvent content type must be in %s' % allowedtypes)

class LaunchEvent(ControlEvent):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def __init__(self, id, newproc, targetclass, args=(), kwargs={}):
		nodeinfo = {'newproc':newproc,'targetclass':targetclass, 'args':args, 'kwargs':kwargs}
		Event.__init__(self, id, content=nodeinfo)

###########################################################
## event related exceptions

class InvalidEventError(TypeError):
	pass

