'''
functions useful to either client or server
'''

import itertools
import json
import numpy

## Server accepts connections on this port
REDUX_PORT = 55123

def request_to_kwargs(request):
	'''convert request string into keyword args'''
	args = request.split('&')
	key_value = itertools.imap(str.split, args, itertools.repeat('='))
	kwargs = {}
	for key,value in key_value:
		kwargs[key.strip()] = value.strip()
	return kwargs

def kwargs_to_request(**kwargs):
	'''convert keyword args to a request string'''
	args = ['%s=%s' % (key,value) for (key, value) in kwargs.items()]
	request = '&'.join(args)
	return request

class ReduxJSONEncoder(json.JSONEncoder):
	def default(self, obj):
		## convert numpy types to built-in python types
		if isinstance(obj, numpy.bool_):
			return bool(obj)
		elif isinstance(obj, numpy.integer):
			return long(obj)
		elif isinstance(obj, numpy.floating):
			return float(obj)
		elif isinstance(obj, numpy.complexfloating):
			return complex(obj)
		elif isinstance(obj, numpy.dtype):
			return str(obj)
		return json.JSONEncoder.default(self, obj)
