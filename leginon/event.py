## defines the Event and EventHandler classes

import leginonobject
import data

### False is not defined in early python 2.2
False = 0
True = 1

def eventClasses():
	"""
	returns a dict:   {name: class_object, ...}
	that contains all the Event subclasses defined in this module
	"""
	eventclasses = {}
	all_attrs = globals()
	for name,value in all_attrs.items():
		if type(value) == type:
			if issubclass(value, Event):
				eventclasses[name] = value
	return eventclasses

class Event(data.Data):
	def __init__(self, id, content=None, confirm=False):
		data.Data.__init__(self, id, content)
		self.confirm = confirm


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
##			ConfirmationEvent
##		ControlEvent
##			StartEvent
##			Stopvent
##			KillEvent
##			PauseEvent
##			ResumeEvent
##			NumericControlEvent
##			LaunchEvent
##			LockEvent
##			UnlockEvent

### generated by a node to notify manager that node is ready
class NotificationEvent(Event):
	'Event sent by for notification'
	def __init__(self, id, content, confirm=False):
		Event.__init__(self, id, content, confirm)

class NodeAvailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is accessible'
	def __init__(self, id, nodelocation, nodeclass, confirm=False):
		NotificationEvent.__init__(self, id,
					{'location': nodelocation, 'class': nodeclass}, confirm)

#class LauncherAvailableEvent(NodeAvailableEvent):
#	'Event sent by a launcher to the manager to indicate that it is accessible'
#	def __init__(self, id, nodelocation, confirm=False):
#		NodeAvailableEvent.__init__(self, id, nodelocation, confirm)

#class ManagerAvailableEvent(NodeAvailableEvent):
#	'Event sent by a manager to the nodes to indicate that it is accessible'
#	def __init__(self, id, nodelocation, confirm=False):
#		NodeAvailableEvent.__init__(self, id, nodelocation, confirm)

class NodeUnavailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is inaccessible'
	def __init__(self, id, confirm=False):
		NotificationEvent.__init__(self, id, None, confirm)

class PublishEvent(NotificationEvent):
	'Event indicating data was published'
	def __init__(self, id, dataid, confirm=False):
		NotificationEvent.__init__(self, id, dataid, confirm)

class UnpublishEvent(NotificationEvent):
	'Event indicating data was unpublished (deleted)'
	def __init__(self, id, dataid, confirm=False):
		NotificationEvent.__init__(self, id, dataid, confirm)

class ConfirmationEvent(NotificationEvent):
	'Event sent to confirm event processing'
	def __init__(self, id, eventid, confirm=False):
		NotificationEvent.__init__(self, id, eventid, confirm)

class ConfirmationPublishEvent(NotificationEvent, PublishEvent):
	'Event sent to confirm event processing'
	def __init__(self, id, eventid, dataid, confirm=False):
		NotificationEvent.__init__(self, id, \
					{'event ID': eventid, 'data ID': dataid}, confirm)

# this could be a subclass of publish event, but I'm not sure if that
# would confuse those not looking for a list
class ListPublishEvent(Event):
	'Event indicating data was published'
	def __init__(self, id, idlist, confirm=False):
		if type(idlist) == list:
			Event.__init__(self, id, idlist, confirm)
		else:
			raise TypeError

class NodeClassesPublishEvent(PublishEvent):
	'Event indicating launcher published new list of node classes'
	def __init__(self, id, content, confirm):
		PublishEvent.__init__(self, id, content, confirm)

class CorrelationPublishEvent(PublishEvent):
	'Event indicating cross correlation was published'
	def __init__(self, id, content, confirm):
		PublishEvent.__init__(self, id, content, confirm)

class ImagePublishEvent(PublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		PublishEvent.__init__(self, id, content, confirm)

class ReferenceImagePublishEvent(ImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		ImagePublishEvent.__init__(self, id, content, confirm)

class ImageTilePublishEvent(ImagePublishEvent):
	'Event indicating image tile was published'
	def __init__(self, id, content, confirm):
		ImagePublishEvent.__init__(self, id, content, confirm)

class StateImageTilePublishEvent(ImagePublishEvent):
	'Event indicating image tile was published'
	def __init__(self, id, content, confirm):
		ImagePublishEvent.__init__(self, id, content, confirm)

class DarkImagePublishEvent(ReferenceImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		ReferenceImagePublishEvent.__init__(self, id, content, confirm)

class BrightImagePublishEvent(ReferenceImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		ReferenceImagePublishEvent.__init__(self, id, content, confirm)

class CorrelationImagePublishEvent(ImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		ImagePublishEvent.__init__(self, id, content, confirm)

class CrossCorrelationImagePublishEvent(CorrelationImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		CorrelationImagePublishEvent.__init__(self, id, content, confirm)

class PhaseCorrelationImagePublishEvent(CorrelationImagePublishEvent):
	'Event indicating image was published'
	def __init__(self, id, content, confirm):
		CorrelationImagePublishEvent.__init__(self, id, content, confirm)

class StateMosaicPublishEvent(PublishEvent):
	'Event indicating state mosaic data was published'
	def __init__(self, id, content, confirm):
		PublishEvent.__init__(self, id, content, confirm)

class ControlEvent(Event):
	'Event that passes a value with it'
	def __init__(self, id, content=None, confirm=False):
		Event.__init__(self, id, content, confirm)

class StartEvent(ControlEvent):
	'Event that signals a start'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)
	
class StopEvent(ControlEvent):
	'Event that signals a stop'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)

class KillEvent(ControlEvent):
	'Event that signals a kill'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)

class PauseEvent(ControlEvent):
	'Event that signals a pause'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)
	
class ResumeEvent(ControlEvent):
	'Event that signals a resume'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)

class NumericControlEvent(ControlEvent):
	'ControlEvent that allows only numeric values to be passed'
	def __init__(self, id, content, confirm=False):
		allowedtypes = (int, long, float)
		if type(content) in allowedtypes:
			ControlEvent.__init__(self, id, content, confirm)
		else:
			raise TypeError('NumericControlEvent content type must be in %s' % allowedtypes)

class LaunchEvent(ControlEvent):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def __init__(self, id, newproc, targetclass, args=(), kwargs={}, confirm=False):
		nodeinfo = {'newproc':newproc,'targetclass':targetclass, 'args':args, 'kwargs':kwargs}
		Event.__init__(self, id, nodeinfo, confirm)

class UpdateNodeClassesEvent(ControlEvent):
	'ControlEvent sent to a launcher telling it to update node classes'
	def __init__(self, id):
		ControlEvent.__init__(self, id)

class LockEvent(ControlEvent):
	'Event that signals a lock'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)
	
class UnlockEvent(ControlEvent):
	'Event that signals an unlock'
	def __init__(self, id, confirm=False):
		ControlEvent.__init__(self, id)

class ImageClickEvent(Event):
	def __init__(self, id, content, confirm=False):
		Event.__init__(self, id, dict(content), confirm)

class ImageAcquireEvent(Event):
	def __init__(self, id):
		Event.__init__(self, id)
	
class PixelShiftEvent(Event):
	def __init__(self, id, content, confirm=False):
		Event.__init__(self, id, dict(content), confirm)

class StagePixelShiftEvent(PixelShiftEvent):
	def __init__(self, id, content, confirm=False):
		Event.__init__(self, id, dict(content), confirm)

class ImageShiftPixelShiftEvent(PixelShiftEvent):
	def __init__(self, id, content, confirm=False):
		Event.__init__(self, id, dict(content), confirm)

###########################################################
###########################################################
## event related exceptions

class InvalidEventError(TypeError):
	pass

