import xmlrpclib
import uiserver
import Tkinter
import Pmw

class XMLRPCClient(object):
	def __init__(self, serverhostname, serverport, port=None):
		uri = 'http://%s:%s' % (serverhostname, serverport)
		self.proxy = xmlrpclib.ServerProxy(uri)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except xmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except xmlrpclib.Fault:
			# exception during call of the function
			raise

class UIWidget(object):
	def __init__(self, name, parent, tkparent):
		if type(name) is not str:
			raise TypeError('UIWidget name must be a string')
		self.name = name
		if parent is not None and not isinstance(parent, UIContainerWidget):
			raise TypeError('UIWidget parent must be a UIContainer or None')
		self.parent = parent
		self.tkparent = tkparent

	def getWidgetFromList(self, namelist):
		if len(namelist) == 1 and namelist[0] == self.name:
			return self
		else:
			raise ValueError('incorrect widget')

class UIButtonWidget(UIWidget, Tkinter.Button):
	def __init__(self, name, parent, tkparent):
		UIWidget.__init__(self, name, parent, tkparent)
		Tkinter.Button.__init__(self, tkparent, text=self.name,
																						command=self.command)

	def command(self):
		self.parent.commandCallback((self.name,), ())

class UIDataWidget(UIWidget, Tkinter.Frame):
	def __init__(self, name, parent, tkparent):
		UIWidget.__init__(self, name, parent, tkparent)
		Tkinter.Frame.__init__(self, tkparent)

	def set(self, value):
		raise NotImplemetedError()

	def apply(self):
		raise NotImplemetedError()

	def setServer(self):
		self.parent.setCallback((self.name,), self.value)

def UIWidgetClassFromType(typelist):
	if typelist[0] == 'object':
		if len(typelist) > 1:
			if typelist[1] == 'container':
				return UIContainerWidget
			elif typelist[1] == 'method':
				return UIButtonWidget
			elif typelist[1] == 'data':
				if len(typelist) > 2:
					if typelist[2] == 'boolean':
						return UICheckbuttonWidget
				return UIEntryWidget
	raise ValueError('invalid type list for UI widget class')

class UIContainerWidget(UIWidget, Pmw.Group):
	def __init__(self, name, parent, tkparent):
		self.uiwidgets = {}
		UIWidget.__init__(self, name, parent, tkparent)
		Pmw.Group.__init__(self, tkparent, tag_text=self.name)

	def getWidgetFromList(self, namelist):
		if type(namelist) not in (list, tuple):
			raise TypeError('name hierarchy must be a list')
		if not namelist:
			raise ValueError('no widget name[s] specified')
		if namelist[0] == self.name:
			if len(namelist) == 1:
				return self
			else:
				for uiwidget in self.uiwidgets.values():
					try:
						return uiwidget.getWidgetFromList(namelist[1:])
					except ValueError:
						pass
				raise ValueError(	
										'widget with specified name does not exists in container')
		else:
			raise ValueError('specfied name does not match widget name')
			
	def add(self, namelist, typelist, value):
		container = self.getWidgetFromList(namelist[:-1])
		if not isinstance(container, UIContainerWidget):
			raise ValueError('parent of widget must be a container')
		uiwidget_type = UIWidgetClassFromType(typelist)
		name = namelist[-1]
		uiwidget = uiwidget_type(name, container, container.interior())
		if isinstance(uiwidget, UIDataWidget):
			uiwidget.set(value)
		uiwidget.grid(row=len(container.uiwidgets), column=0)
		container.uiwidgets[name] = uiwidget

	def set(self, namelist, value):
		container = self.getWidgetFromList(namelist[:-1])
		if not isinstance(container, UIContainerWidget):
			raise ValueError('parent of widget must be a container')
		name = namelist[-1]
		try:
			uiwidget = container.uiwidgets[name].set(value)
		except KeyError:
			raise ValueError('container \'%s\' does not contain widget \'%s\''
																						% (self.name, name))

	def delete(self, namelist):
		container = self.getWidgetFromList(namelist[:-1])
		if not isinstance(container, UIContainerWidget):
			raise ValueError('parent of widget must be a container')
		name = namelist[-1]
		try:
			uiwidget = container.uiwidgets[name]
		except KeyError:
			raise ValueError('container \'%s\' does not contain widget \'%s\''
																						% (self.name, name))
		deletedrow = uiwidget.grid_info()['row']
		uiwidget.grid_forget()
		#uiwidget.destroy()
		del container.uiwidgets[name]

		for uiwidget in container.uiwidgets.values():
			row = uiwidget.grid_info()['row']
			if row > deletedrow:
				uiwidget.grid_configure(row=int(row)-1)

	def setCallback(self, namelist, value):
		self.parent.setCallback((self.name,) + namelist, value)

	def commandCallback(self, namelist, args):
		self.parent.commandCallback((self.name,) + namelist, args)

class UIEntryWidget(UIDataWidget):
	def __init__(self, name, parent, tkparent):
		self.value = None
		UIDataWidget.__init__(self, name, parent, tkparent)
		self.applybutton = Tkinter.Button(self, text='Apply', command=self.apply)
		self.applybutton.grid(row=0, column=1)
		self.markClean()
		self.entryfield = Pmw.EntryField(self, labelpos='w',
																						label_text=self.name,
																						modifiedcommand=self.markDirty)
		self.entryfield.grid(row=0, column=0)

	def set(self, value):
		self.value = value
		self.entryfield.setvalue(value)
		self.markClean()

	def markDirty(self):
		self.applybutton['state'] = Tkinter.NORMAL

	def markClean(self):
		self.applybutton['state'] = Tkinter.DISABLED

	def apply(self):
		value = self.entryfield.getvalue()
		if type(self.value) != str:
			try:
				value = eval(value)
			except:
				return
			if type(value) == type(self.value):
				self.set(value)
			else:
				return
		else:
			self.set(value)
		self.setServer()

class UICheckbuttonWidget(UIDataWidget):
	def __init__(self, name, parent, tkparent):
		self.value = None
		UIDataWidget.__init__(self, name, parent, tkparent)
		self.checkbuttonvar = Tkinter.IntVar()
		self.checkbutton = Tkinter.Checkbutton(self, variable=self.checkbuttonvar,
																									command=self.check,
																									text=self.name)
		self.checkbutton.grid(row=0, column=0)

	def set(self, value):
		self.value = value
		self.checkbuttonvar.set(self.value)

	def check(self):
		if self.checkbuttonvar.get():
			self.value = 1
		else:
			self.value = 0
		self.setServer()

class UIClient(XMLRPCClient, uiserver.XMLRPCServer, UIContainerWidget):
	def __init__(self, tkparent, serverhostname, serverport, port=None):
		UIContainerWidget.__init__(self, 'Server', None, tkparent)
		XMLRPCClient.__init__(self, serverhostname, serverport, port)
		uiserver.XMLRPCServer.__init__(self, port)
		self.server.register_function(self.setFromServer, 'SET')
		self.server.register_function(self.addFromServer, 'ADD')
		self.server.register_function(self.deleteFromServer, 'DEL')
		self.execute('ADDSERVER', (self.hostname, self.port))

	def setServer(self, namelist, value):
		self.execute('SET', (namelist, value))

	def commandServer(self, namelist, args):
		self.execute('COMMAND', (namelist, args))

	def addFromServer(self, namelist, typelist, value):
		print 'ADD', namelist, typelist, value
		self.add(namelist, typelist, value)
		return ''

	def setFromServer(self, namelist, value):
		print 'SET', namelist, value
		self.set(namelist, value)
		return ''

	def deleteFromServer(self, namelist):
		print 'DEL', namelist
		self.delete(namelist)
		return ''

	def setCallback(self, namelist, value):
		self.setServer((self.name,) + namelist, value)

	def commandCallback(self, namelist, args):
		self.commandServer((self.name,) + namelist, args)

