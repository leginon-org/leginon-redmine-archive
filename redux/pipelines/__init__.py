# redux.__init__.py

registered = {}
def register(name, pipes):
	global registered
	registered[name] = pipes

import standard
register('standard', standard.pipes)

