import data
import leginonconfig
import os
import project
import socket
import time
import uidata

class ManagerSetup(object):
	def __init__(self, manager):
		self.manager = manager

		self.defineUserInterface()

		self.initProjects()
		self.initUsers()
		self.initInstruments()

	def start(self):
		session_name = self.sessionselector.getSelectedValue()
		session = self.session_dict[session_name]
		self.manager.session = session

		if session['instrument'] is not None and \
			session['instrument']['hostname'] not in self.manager.launcherdict.keys() and not self.skipinstrument.get():
			try:
				hostname = session['instrument']['hostname']
				if hostname:
					location = {}
					location['TCP transport'] = {}
					location['TCP transport']['hostname'] = hostname
					location['TCP transport']['port'] = 55555
					self.manager.addNode(location)
			except (IOError, TypeError, socket.error), e:
				if isinstance(e, socket.error):
					self.manager.outputWarning('Cannot add instrument\'s launcher.')
		if self.container.parent is not None:
			self.container.parent.deleteObject(self.container.name)

		self.manager.defineUserInterface()

	def uiCreateSession(self):
		## publish a new session
		sessiondata = self.buildSessionData()
		print 'sessiondata', sessiondata
		projectname = self.projectselection.getSelectedValue()
		print 'projectname', projectname
		self.manager.publish(sessiondata, database=True)
		print 'published'
		self.linkSessionProject(sessiondata, projectname)
		print 'linked'
		# refresh session list
		self.uiUpdateSessionList()
		print 'done'

	def linkSessionProject(self, sessiondata, projectname):
		try:
			projectid = self.projectmap[projectname]['projectId']
		except KeyError:
			return
		projectsession = project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

	def buildSessionData(self):
		initializer = {
		  'name': self.build_session_name.get(),
		  'comment': self.build_session_comment.get(),
		  'user': self.uiGetUser(),
		  'instrument': self.uiGetInstrument(),
		  'image path': self.build_image_path.get()
		}
		return data.SessionData(initializer=initializer)

	def initInstruments(self):
		instruments = self.getInstruments()
		self.instruments = self.indexByName(instruments)
		initializer = {'name': 'None',
										'description': 'No Instrument'}
		self.instruments['None'] = data.InstrumentData(initializer=initializer)
		self.uiUpdateInstrument()

	def uiUpdateInstrument(self):
		instrumentnames = self.instruments.keys()
		instrumentnames.sort()
		try:
			index = instrumentnames.index('None')
		except ValueError:
			index = 0
		self.instrumentselection.set(instrumentnames, index)

	def uiGetInstrument(self):
		instrumentname = self.instrumentselection.getSelectedValue()
		if instrumentname in self.instruments:
			return self.instruments[instrumentname]
		else:
			return None

	def getInstruments(self):
		instrumentinitializer = {}
		instrumentinstance = data.InstrumentData(initializer=instrumentinitializer)
		instrumentdatalist = self.manager.research(datainstance=instrumentinstance)
		return instrumentdatalist

	def initUsers(self):
		self.initAdmin()
		users = self.getUsers()
		self.users = self.indexByName(users)
		self.uiUpdateUsers()

	def initProjects(self):
		self.projectdata = project.ProjectData()
		self.projects = self.projectdata.getProjects()
		projects = self.projects.getall()
		self.projectmap = {}
		for p in projects:
			self.projectmap[p['name']] = p
		self.uiUpdateProjects()

	def uiUpdateProjects(self):
		projectnames = self.projectmap.keys()
		projectnames.sort()
		self.projectselection.set(projectnames, 0)

	def uiUpdateUsers(self):
		usernames = self.users.keys()
		usernames.sort()
		self.userselection.set(usernames, 0)

	def uiGetUser(self):
		username = self.userselection.getSelectedValue()
		if username in self.users:
			return self.users[username]
		else:
			return None

	def indexByName(self, datalist):
		### assuming datalist is ordered by timestamp (default from
		### a research), this gets the latest instance by each name
		index = {}
		namesdone = []
		for indexdata in datalist:
			try:
				name = indexdata['name']
				if name not in namesdone:
					index[name] = indexdata
					namesdone.append(name)
			except (TypeError, IndexError):
				pass
		return index

	def getUsers(self):
		self.initAdmin()
		groupinstance = data.GroupData()
		userinitializer = {'group': groupinstance}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		return userdatalist

	def initAdmin(self):
		adminuser = self.getAdminUser()
		if adminuser is None:
			admingroup = self.getAdminGroup()
			if admingroup is None:
				admingroup = self.addAdminGroup()
			adminuser = self.addAdminUser(admingroup)

	def getAdminGroup(self):
		groupinitializer = {'name': 'administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		groupdatalist = self.manager.research(datainstance=groupinstance)
		try:
			return groupdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminGroup(self):
		groupinitializer = {'name': 'administrators',
												'description': 'Administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		self.manager.publish(groupinstance, database=True)
		return groupinstance

	def getAdminUser(self):
		userinitializer = {'name': 'administrator', 'group': data.GroupData()}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		try:
			return userdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminUser(self, group):
		userinitializer = {'name': 'administrator',
												'full name': 'Administrator',
												'group': group}
		userinstance = data.UserData(initializer=userinitializer)
		self.manager.publish(userinstance, database=True)
		return userinstance

	def uiProjectSelectCallback(self, index):
		if not hasattr(self, 'projectselection'):
			return index
		'''
		projectname = self.projectselection.getSelectedValue(index)
		try:
			# show description
			print self.projectmap[projectname]
		except KeyError:
			pass
		'''
		return index

	def uiUserSelectCallback(self, index):
		if not hasattr(self, 'userselection'):
			return index
		username = self.userselection.getSelectedValue(index)
		if username in self.users:
			userdata = self.users[username]
			try:
				self.build_userfullname.set(userdata['full name'])
			except KeyError:
				self.build_userfullname.set('')
			try:
				self.build_usergroup.set(userdata['group']['name'])
			except KeyError:
				self.build_usergroup.set('')
		else:
			self.build_userfullname.set('')
			self.build_usergroup.set('')
		return index

	def uiInstrumentSelectCallback(self, index):
		if not hasattr(self, 'instrumentselection'):
			return index
		instrumentname = self.instrumentselection.getSelectedValue(index)
		if instrumentname in self.instruments:
			instrumentdata = self.instruments[instrumentname]
			try:
				self.build_instrumentdescription.set(instrumentdata['description'])
			except (TypeError, KeyError):
				self.build_instrumentdescription.set('')
			try:
				self.build_instrumenthostname.set(instrumentdata['hostname'])
			except (TypeError, KeyError):
				self.instrumenthostname.set('')
		else:
			self.build_instrumentdescription.set('')
			self.build_instrumenthostname.set('')
		return index

	def suggestSessionName(self):
		session_name = time.strftime('%y%b%da').lower()
		return session_name

	def uiSuggestSessionName(self):
		#session_name = self.suggestSessionName()
		session_name = 'testaaaa'
		self.build_session_name.set(session_name)

	def uiSessionSelectCallback(self, index):
		try:
			session_name = self.sessionselector.getSelectedValue(index)
		except AttributeError:
			return index
		sessiondata = self.session_dict[session_name]
		self.uiShowSessionInfo(sessiondata)
		return index

	def uiShowSessionInfo(self, sessiondata):
		comment = sessiondata['comment']
		self.load_sessioncomment.set(comment)

		user = sessiondata['user']['name']
		self.load_sessionuser.set(user)

		inst = sessiondata['instrument']['name']
		self.load_sessioninstrument.set(inst)

		path = sessiondata['image path']
		self.load_sessionpath.set(path)

	def getSessionDataName(self, sessiondata):
		return sessiondata['name']

	def uiUpdateSessionList(self):
		sessionlist = self.researchSessions()
		session_names = map(self.getSessionDataName, sessionlist)
		self.session_dict = dict(zip(session_names, sessionlist))
		self.sessionselector.set(session_names,0)

	def researchSessions(self):
		qsession = data.SessionData()
		sessionlist = self.manager.research(datainstance=qsession)
		return sessionlist

	def defineUserInterface(self):
		self.container = uidata.ExternalContainer('Manager Setup')

		## there are two main sections:
		sessionloader = uidata.Container('Session Loader')
		sessionbuilder = uidata.Container('Session Builder')

		## components of the loader section:
		self.load_sessioncomment = uidata.String('Comment', '', 'r')
		self.load_sessionuser = uidata.String('User', '', 'r')
		self.load_sessioninstrument = uidata.String('Instrument', '', 'r')
		self.load_sessionpath = uidata.String('Image Path', '', 'r')

		self.sessionselector = uidata.SingleSelectFromList('Session', [], 0, 'rw', persist=False, callback=self.uiSessionSelectCallback)
		self.uiUpdateSessionList()

		self.skipinstrument = uidata.Boolean('Do Not Connect Instrument Launcher', False, 'rw', persist=True)

		startmethod = uidata.Method('Start', self.start)

		sessionloaderobjects = (
		  self.sessionselector,
		  self.load_sessioncomment,
		  self.load_sessionuser,
		  self.load_sessioninstrument,
		  self.load_sessionpath,
		  self.skipinstrument,
		  startmethod,
		)
		sessionloader.addObjects(sessionloaderobjects)

		## components of the builder section:
		suggestnamemethod = uidata.Method('Suggest A Name', self.uiSuggestSessionName)
		session_name = self.suggestSessionName()
		self.build_session_name = uidata.String('Session Name', session_name, 'rw', persist=True)
		self.build_session_comment = uidata.String('Session Comment', '', 'rw', persist=True)



		build_projectcontainer = uidata.Container('Project')
		self.projectselection = uidata.SingleSelectFromList('Project', [], 0,
																				callback=self.uiProjectSelectCallback,
																				persist=True)
		build_projectcontainer.addObject(self.projectselection)

		build_usercontainer = uidata.Container('User')
		self.userselection = uidata.SingleSelectFromList('Name', [], 0,
																						callback=self.uiUserSelectCallback,
																						persist=True)
		self.build_userfullname = uidata.String('Full Name', '', 'r')
		self.build_usergroup = uidata.String('Group Name', '', 'r')
		build_usercontainer.addObjects((self.userselection,
																		self.build_userfullname,
																		self.build_usergroup))

		build_instrumentcontainer = uidata.Container('Instrument')
		self.instrumentselection = uidata.SingleSelectFromList('Name', [], 0,
																			callback=self.uiInstrumentSelectCallback,
																			persist=True)
		self.build_instrumentdescription = uidata.String('Description', '', 'r')
		self.build_instrumenthostname = uidata.String('Hostname', '', 'r')

		build_instrumentcontainer.addObjects((self.instrumentselection,
																		self.build_instrumentdescription,
																		self.build_instrumenthostname))



		## default path comes from leginonconfig
		image_path = os.path.join(leginonconfig.IMAGE_PATH,session_name)
		self.build_image_path = uidata.String('Image Path', image_path, 'rw', persist=True)

		createmethod = uidata.Method('Create Session', self.uiCreateSession)

		sessionbuilderobjects = (
		  suggestnamemethod,
		  self.build_session_name,
		  self.build_session_comment,
		  build_projectcontainer,
		  build_usercontainer,
		  build_instrumentcontainer,
		  self.build_image_path,
		  createmethod,
		)
		sessionbuilder.addObjects(sessionbuilderobjects)

		mainobjects = (
		  sessionloader,
		  sessionbuilder,
		)
		self.container.addObjects(mainobjects)

	def getUserInterface(self):
		return self.container

