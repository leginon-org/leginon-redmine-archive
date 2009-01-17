#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

# defines the Event and EventHandler classes

import leginondata
import sinedon.data
import copy

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

class Event(sinedon.data.Data):
	def __init__(self, initializer=None, **kwargs):
		sinedon.data.Data.__init__(self, initializer, **kwargs)

	def typemap(cls):
		return sinedon.data.Data.typemap() + (
			('node', str),
			('confirm', tuple),
			('destination', str),
		)
	typemap = classmethod(typemap)

class EventLog(sinedon.data.Data):
	def typemap(cls):
		return sinedon.data.Data.typemap() + (
			('eventclass', str),
			('status', str),
		)
	typemap = classmethod(typemap)


## Standard Event Types:
##
##	Event
##		NotificationEvent
##			NodeAvailableEvent
##				LauncherAvailableEvent
##			NodeUnavailableEvent
##			PublishEvent
##			UnpublishEvent
##			ConfirmationEvent
##		ControlEvent
##			StartEvent
##			Stopvent
##			KillEvent
##			PauseEvent
##			ResumeEvent
##			NumericControlEvent
##			CreateNodeEvent
##			LockEvent
##			UnlockEvent

### generated by a node to notify manager that node is ready
class NotificationEvent(Event):
	'Event sent for notification'
	pass

## I'm definietely not sure about this one
class NodeAvailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is accessible'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('location', dict),
			('nodeclass', str),
		)
	typemap = classmethod(typemap)

class NodeUnavailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is inaccessible'
	pass

class NodeInitializedEvent(NotificationEvent):
	'Event sent by a node to indicate that it is operational'
	pass

class NodeUninitializedEvent(NotificationEvent):
	'Event sent by a node to indicate that it is no longer operational'
	pass

class TargetListDoneEvent(NotificationEvent):
	'Event indicating target list is done'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('targetlistid', tuple),
			('status', str),
			('targetlist', leginondata.ImageTargetListData),
		)
	typemap = classmethod(typemap)

class ImageProcessDoneEvent(NotificationEvent):
	'Event indicating target list is done'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('imageid', int),
			('status', str),
		)
	typemap = classmethod(typemap)

class GridInsertedEvent(NotificationEvent):
	'Event indicating a grid has been inserted'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('grid', leginondata.GridData),
		)
	typemap = classmethod(typemap)

class GridExtractedEvent(NotificationEvent):
	'Event indicating a grid has been extracted'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('grid', leginondata.GridData),
		)
	typemap = classmethod(typemap)

class MosaicDoneEvent(NotificationEvent):
	'Event indicating mosaic is done'
	pass

class PublishEvent(NotificationEvent):
	'Event indicating data was published'
	def typemap(cls):
		if not hasattr(cls, 'dataclass'):
			raise RuntimeError('need to define "dataclass" for publish event')
		return NotificationEvent.typemap() + (
			('data', cls.dataclass),
		)
	typemap = classmethod(typemap)

class ConfirmationEvent(NotificationEvent):
	'Event sent to confirm event processing'
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('eventid', tuple),
			('status', str),
		)
	typemap = classmethod(typemap)

class QueuePublishEvent(PublishEvent):
	dataclass = leginondata.QueueData

class ReferenceTargetPublishEvent(PublishEvent):
	dataclass = leginondata.ReferenceTargetData

class AlignZeroLossPeakPublishEvent(PublishEvent):
	dataclass = leginondata.AlignZeroLossPeakData

class MeasureDosePublishEvent(PublishEvent):
	dataclass = leginondata.MeasureDoseData

class FixBeamEvent(PublishEvent):
	dataclass = leginondata.FixBeamData

class AcquisitionImageDriftPublishEvent(PublishEvent):
	dataclass = leginondata.AcquisitionImageDriftData

class NeedTargetShiftEvent(NotificationEvent):
	'''notify DriftManager that I want to know image drift for target update'''
	def typemap(cls):
		return NotificationEvent.typemap() + (
			('image', leginondata.AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class DriftMonitorRequestEvent(PublishEvent):
	dataclass = leginondata.DriftMonitorRequestData

class DriftMonitorResultEvent(PublishEvent):
	dataclass = leginondata.DriftMonitorResultData

class NodeOrderEvent(Event):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def typemap(cls):
		return Event.typemap() + (
			('order', list),
		)
	typemap = classmethod(typemap)

class NodeClassesPublishEvent(PublishEvent):
	'Event indicating launcher published new list of node classes'
	dataclass = leginondata.NodeClassesData

class ImagePublishEvent(PublishEvent):
	'Event indicating image was published'
	dataclass = leginondata.ImageData

class CameraImagePublishEvent(ImagePublishEvent):
	'Event indicating camera image was published'
	dataclass = leginondata.CameraImageData

class CorrectedCameraImagePublishEvent(CameraImagePublishEvent):
	'Event indicating camera image was published'
	dataclass = leginondata.CorrectedCameraImageData

class PresetImagePublishEvent(CameraImagePublishEvent):
	'Event indicating preset camera image was published'
	dataclass = leginondata.PresetImageData

class AcquisitionImagePublishEvent(PresetImagePublishEvent):
	dataclass = leginondata.AcquisitionImageData

class FilmPublishEvent(AcquisitionImagePublishEvent):
	dataclass = leginondata.FilmData

class CorrectorImagePublishEvent(CameraImagePublishEvent):
	dataclass = leginondata.CorrectorImageData

class DarkImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = leginondata.DarkImageData

class BrightImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = leginondata.BrightImageData

class NormImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = leginondata.NormImageData

class ImageTargetListPublishEvent(PublishEvent):
	dataclass = leginondata.ImageTargetListData

class ImageListPublishEvent(PublishEvent):
	dataclass = leginondata.ImageListData

class ScopeEMPublishEvent(PublishEvent):
	dataclass = leginondata.ScopeEMData

class CameraEMPublishEvent(PublishEvent):
	dataclass = leginondata.CameraEMData

class CameraImageEMPublishEvent(PublishEvent):
	dataclass = leginondata.CameraEMData

class PresetPublishEvent(PublishEvent):
	dataclass = leginondata.PresetData

class ControlEvent(Event):
	'Event that passes a value with it'
	pass

class KillEvent(ControlEvent):
	'Event that signals a kill'
	pass

class SetManagerEvent(ControlEvent):
	def typemap(cls):
		return ControlEvent.typemap() + (
			('location', dict),
			('session', leginondata.SessionData),
		)
	typemap = classmethod(typemap)

class CreateNodeEvent(ControlEvent):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def typemap(cls):
		return ControlEvent.typemap() + (
			('targetclass', str),
			('session', leginondata.SessionData),
			('manager location', dict),
		)
	typemap = classmethod(typemap)

class LockEvent(ControlEvent):
	'Event that signals a lock'
	pass
	
class UnlockEvent(ControlEvent):
	'Event that signals an unlock'
	pass

class QueueGridEvent(ControlEvent):
	def typemap(cls):
		return ControlEvent.typemap() + (
			('grid ID', int),
		)
	typemap = classmethod(typemap)

class QueueGridsEvent(ControlEvent):
	def typemap(cls):
		return ControlEvent.typemap() + (
			('grid IDs', list),
		)
	typemap = classmethod(typemap)

class GridLoadedEvent(NotificationEvent):
	def typemap(cls):
		return ControlEvent.typemap() + (
			('grid', leginondata.GridData),
			('request node', str),
			('status', str),
		)
	typemap = classmethod(typemap)

class UnloadGridEvent(NotificationEvent):
	def typemap(cls):
		return ControlEvent.typemap() + (
			('grid ID', int),
		)
	typemap = classmethod(typemap)

class InsertGridEvent(ControlEvent):
	'Event that signals a grid to be inserted'
	pass

class ExtractGridEvent(ControlEvent):
	'Event that signals a grid to be extracted'
	pass

class MakeTargetListEvent(ControlEvent):
	'Event telling target maker to make a target list'
	def typemap(cls):
		return ControlEvent.typemap() + (
			('grid', leginondata.GridData),
		)
	typemap = classmethod(typemap)

class EmailEvent(Event):
	'Event to send email'
	def typemap(cls):
		return Event.typemap() + (
			('subject', str),
			('text', str),
			('image string', str),
		)
	typemap = classmethod(typemap)

class PresetLockEvent(Event):
	'lock presets manager so only I can change presets'
	pass

class PresetUnlockEvent(Event):
	'unlock presets manager'
	pass

class ChangePresetEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('name', str),
			('emtarget', leginondata.EMTargetData),
			('key', str),
			('keep image shift', bool),
		)
	typemap = classmethod(typemap)

class PresetChangedEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('name', str),
			('preset', leginondata.PresetData),
		)
	typemap = classmethod(typemap)

class MeasureDoseEvent(ChangePresetEvent):
    pass

class DoseMeasuredEvent(PresetChangedEvent):
    pass

class SetEMEvent(PublishEvent):
	pass

class SetScopeEvent(SetEMEvent):
	dataclass = leginondata.ScopeEMData

class SetCameraEvent(SetEMEvent):
	dataclass = leginondata.CameraEMData

class DeviceLockEvent(ControlEvent):
	pass

class DeviceUnlockEvent(ControlEvent):
	pass

class DeviceGetPublishEvent(PublishEvent):
	dataclass = leginondata.DeviceGetData

class MoveToTargetEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('target', leginondata.AcquisitionImageTargetData),
			('movetype', str),
			('move precision', float),
			('accept precision', float),
			('final image shift', bool),
		)
	typemap = classmethod(typemap)

class MoveToTargetDoneEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('target', leginondata.AcquisitionImageTargetData),
			('status', str),
		)
	typemap = classmethod(typemap)

class DevicePublishEvent(PublishEvent):
	dataclass = leginondata.DeviceData
	def typemap(cls):
		return PublishEvent.typemap() + (
			('get data ID', tuple),
		)
	typemap = classmethod(typemap)

'''
class DeviceGetEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('data ID', tuple),
		)
	typemap = classmethod(typemap)

class DeviceSetEvent(Event):
	def typemap(cls):
		return Event.typemap() + (
			('data ID', tuple),
		)
	typemap = classmethod(typemap)
'''

class DeviceConfirmationEvent(ConfirmationEvent):
	def typemap(cls):
		return ConfirmationEvent.typemap() + (
			('data ID', tuple),
		)
	typemap = classmethod(typemap)

# generate the mapping of data class to publish event class
publish_events = {}
event_classes = eventClasses()
for eventclass in event_classes.values():
	if issubclass(eventclass, PublishEvent):
		if hasattr(eventclass, 'dataclass'):
			publish_events[eventclass.dataclass] = eventclass

# event related exceptions

class InvalidEventError(TypeError):
	pass


# generate the mapping of data class to publish event class
publish_events = {}
event_classes = eventClasses()
for eventclass in event_classes.values():
	if issubclass(eventclass, PublishEvent):
		if hasattr(eventclass, 'dataclass'):
			if eventclass.dataclass in publish_events:
				## for now we will just avoid a conflict
				publish_events[eventclass.dataclass] = None
			else:
				publish_events[eventclass.dataclass] = eventclass

# event related exceptions

class InvalidEventError(TypeError):
	pass

